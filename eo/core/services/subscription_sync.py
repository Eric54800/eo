from __future__ import annotations

from datetime import datetime

from django.utils import timezone

from core.models import Organisation, Subscription


def _stripe_ts_to_datetime(value):
    if not value:
        return None
    return datetime.fromtimestamp(value, tz=timezone.utc)


def _map_subscription_status(stripe_status: str) -> str:
    if stripe_status == "trialing":
        return Subscription.Status.TRIALING
    if stripe_status == "active":
        return Subscription.Status.ACTIVE
    return Subscription.Status.CANCELED


def _extract_object_data(event):
    data = event.get("data", {}) if isinstance(event, dict) else getattr(event, "data", {})
    if isinstance(data, dict):
        return data.get("object", {})
    return getattr(data, "object", {})


class SubscriptionSyncService:
    def handle_event(self, event):
        event_type = event.get("type") if isinstance(event, dict) else getattr(event, "type", "")

        if event_type == "checkout.session.completed":
            self._handle_checkout_completed(event)
            return

        if event_type in {"customer.subscription.created", "customer.subscription.updated"}:
            self._handle_subscription_upsert(event)
            return

        if event_type == "customer.subscription.deleted":
            self._handle_subscription_deleted(event)
            return

        if event_type == "invoice.paid":
            self._handle_invoice_paid(event)
            return

        if event_type == "invoice.payment_failed":
            self._handle_invoice_payment_failed(event)
            return

    def _handle_checkout_completed(self, event):
        session = _extract_object_data(event)
        metadata = session.get("metadata", {}) or {}
        organisation_id = metadata.get("organisation_id")
        if not organisation_id:
            return

        organisation = Organisation.objects.filter(id=organisation_id).first()
        if not organisation:
            return

        subscription, _ = Subscription.objects.get_or_create(
            organisation=organisation,
            defaults={"status": Subscription.Status.TRIALING},
        )
        subscription.stripe_customer_id = session.get("customer") or subscription.stripe_customer_id
        subscription.stripe_subscription_id = (
            session.get("subscription") or subscription.stripe_subscription_id
        )
        subscription.save(
            update_fields=[
                "stripe_customer_id",
                "stripe_subscription_id",
                "updated_at",
            ]
        )

    def _handle_subscription_upsert(self, event):
        stripe_subscription = _extract_object_data(event)
        metadata = stripe_subscription.get("metadata", {}) or {}
        organisation_id = metadata.get("organisation_id")

        organisation = None
        if organisation_id:
            organisation = Organisation.objects.filter(id=organisation_id).first()

        if organisation is None:
            stripe_subscription_id = stripe_subscription.get("id")
            organisation = Organisation.objects.filter(
                subscription__stripe_subscription_id=stripe_subscription_id
            ).first()

        if organisation is None:
            return

        subscription, _ = Subscription.objects.get_or_create(
            organisation=organisation,
            defaults={"status": Subscription.Status.TRIALING},
        )
        subscription.status = _map_subscription_status(
            stripe_subscription.get("status", "")
        )
        subscription.trial_end = _stripe_ts_to_datetime(
            stripe_subscription.get("trial_end")
        )
        subscription.current_period_end = _stripe_ts_to_datetime(
            stripe_subscription.get("current_period_end")
        )
        subscription.cancel_at_period_end = bool(
            stripe_subscription.get("cancel_at_period_end")
        )
        subscription.cancel_at = _stripe_ts_to_datetime(
            stripe_subscription.get("cancel_at")
        )
        subscription.stripe_customer_id = (
            stripe_subscription.get("customer") or subscription.stripe_customer_id
        )
        subscription.stripe_subscription_id = (
            stripe_subscription.get("id") or subscription.stripe_subscription_id
        )
        subscription.save()

    def _get_subscription_from_stripe_refs(
        self,
        *,
        stripe_subscription_id=None,
        stripe_customer_id=None,
        organisation_id=None,
    ):
        organisation = None

        if organisation_id:
            organisation = Organisation.objects.filter(id=organisation_id).first()

        if organisation is None and stripe_subscription_id:
            organisation = Organisation.objects.filter(
                subscription__stripe_subscription_id=stripe_subscription_id
            ).first()

        if organisation is None and stripe_customer_id:
            organisation = Organisation.objects.filter(
                subscription__stripe_customer_id=stripe_customer_id
            ).first()

        if organisation is None:
            return None

        subscription, _ = Subscription.objects.get_or_create(
            organisation=organisation,
            defaults={"status": Subscription.Status.TRIALING},
        )
        return subscription

    def _handle_subscription_deleted(self, event):
        stripe_subscription = _extract_object_data(event)
        metadata = stripe_subscription.get("metadata", {}) or {}
        subscription = self._get_subscription_from_stripe_refs(
            stripe_subscription_id=stripe_subscription.get("id"),
            stripe_customer_id=stripe_subscription.get("customer"),
            organisation_id=metadata.get("organisation_id"),
        )
        if subscription is None:
            return

        subscription.status = Subscription.Status.CANCELED
        subscription.cancel_at_period_end = False
        subscription.cancel_at = _stripe_ts_to_datetime(
            stripe_subscription.get("cancel_at")
        )
        subscription.current_period_end = _stripe_ts_to_datetime(
            stripe_subscription.get("current_period_end")
            or stripe_subscription.get("canceled_at")
            or stripe_subscription.get("ended_at")
        )
        subscription.save(update_fields=["status", "current_period_end", "updated_at"])

    def _handle_invoice_paid(self, event):
        invoice = _extract_object_data(event)
        parent = invoice.get("parent", {}) or {}
        details = parent.get("subscription_details", {}) or {}
        metadata = details.get("metadata", {}) or {}
        period_end = (
            invoice.get("period_end")
            or details.get("current_period_end")
            or invoice.get("lines", {})
            .get("data", [{}])[0]
            .get("period", {})
            .get("end")
        )
        subscription = self._get_subscription_from_stripe_refs(
            stripe_subscription_id=invoice.get("subscription"),
            stripe_customer_id=invoice.get("customer"),
            organisation_id=metadata.get("organisation_id"),
        )
        if subscription is None:
            return

        subscription.status = Subscription.Status.ACTIVE
        subscription.current_period_end = (
            _stripe_ts_to_datetime(period_end) or subscription.current_period_end
        )
        subscription.cancel_at_period_end = False
        subscription.cancel_at = None
        subscription.stripe_customer_id = invoice.get("customer") or subscription.stripe_customer_id
        subscription.stripe_subscription_id = (
            invoice.get("subscription") or subscription.stripe_subscription_id
        )
        subscription.save()

    def _handle_invoice_payment_failed(self, event):
        invoice = _extract_object_data(event)
        parent = invoice.get("parent", {}) or {}
        details = parent.get("subscription_details", {}) or {}
        metadata = details.get("metadata", {}) or {}
        subscription = self._get_subscription_from_stripe_refs(
            stripe_subscription_id=invoice.get("subscription"),
            stripe_customer_id=invoice.get("customer"),
            organisation_id=metadata.get("organisation_id"),
        )
        if subscription is None:
            return

        subscription.stripe_customer_id = invoice.get("customer") or subscription.stripe_customer_id
        subscription.stripe_subscription_id = (
            invoice.get("subscription") or subscription.stripe_subscription_id
        )
        subscription.save(update_fields=["stripe_customer_id", "stripe_subscription_id", "updated_at"])
