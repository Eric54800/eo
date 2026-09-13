from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from core.models import (
    Membership,
    MembershipInvitationInterest,
    NotificationDispatch,
    Organisation,
    Publication,
    Subscription,
    WebPushSubscription,
)


User = get_user_model()


class StructureWorkflowTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner",
            email="owner@example.com",
            password="Test1234!",
        )
        self.admin = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="Test1234!",
        )
        self.member = User.objects.create_user(
            username="member",
            email="member@example.com",
            password="Test1234!",
        )

        self.organisation = Organisation.objects.create(
            nom="Association Test",
            slug="association-test",
            created_by=self.owner,
            ville="Lisbonne",
            pays="Portugal",
        )
        Membership.objects.create(
            user=self.owner,
            organisation=self.organisation,
            role="owner",
        )
        Membership.objects.create(
            user=self.admin,
            organisation=self.organisation,
            role="admin",
        )
        Membership.objects.create(
            user=self.member,
            organisation=self.organisation,
            role="member",
        )
        Subscription.objects.create(
            organisation=self.organisation,
            status=Subscription.Status.TRIALING,
            trial_end=timezone.now() + timedelta(days=90),
        )

        self.draft_publication = Publication.objects.create(
            organisation=self.organisation,
            type=Publication.TYPE_INFORMATION,
            status=Publication.STATUS_DRAFT,
            titre="Brouillon interne",
            contenu="Contenu brouillon",
        )
        self.published_publication = Publication.objects.create(
            organisation=self.organisation,
            type=Publication.TYPE_INFORMATION,
            status=Publication.STATUS_PUBLISHED,
            titre="Publication publique",
            contenu="Visible publiquement",
        )

    def make_client(self, user=None):
        client = APIClient()
        if user is not None:
            client.force_authenticate(user=user)
        return client

    def test_creating_organisation_adds_owner_membership_and_trial_subscription(self):
        creator = User.objects.create_user(
            username="creator",
            email="creator@example.com",
            password="Test1234!",
        )
        client = self.make_client(creator)

        response = client.post(
            "/api/organisations/",
            {
                "nom": "Nouvelle Structure",
                "slug": "nouvelle-structure",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        organisation = Organisation.objects.get(slug="nouvelle-structure")

        self.assertTrue(
            Membership.objects.filter(
                organisation=organisation,
                user=creator,
                role="owner",
            ).exists()
        )
        self.assertTrue(
            Subscription.objects.filter(
                organisation=organisation,
                status=Subscription.Status.TRIALING,
            ).exists()
        )

    def test_owner_can_list_draft_and_published_publications(self):
        client = self.make_client(self.owner)

        response = client.get("/api/publications/")

        self.assertEqual(response.status_code, 200)
        statuses = {item["status"] for item in response.data["results"]}
        self.assertIn(Publication.STATUS_DRAFT, statuses)
        self.assertIn(Publication.STATUS_PUBLISHED, statuses)

    def test_public_publications_endpoint_hides_drafts(self):
        client = self.make_client()
        response = client.get(
            "/api/public/publications/",
            {"organisation_slug": self.organisation.slug},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(
            response.data["results"][0]["status"],
            Publication.STATUS_PUBLISHED,
        )

    def test_public_publication_detail_returns_published_content(self):
        client = self.make_client()

        response = client.get(
            f"/api/public/publications/{self.published_publication.id}/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.published_publication.id)
        self.assertEqual(response.data["titre"], "Publication publique")
        self.assertEqual(response.data["contenu"], "Visible publiquement")
        self.assertEqual(response.data["organisation"]["slug"], self.organisation.slug)

    def test_public_publication_detail_hides_draft(self):
        client = self.make_client()

        response = client.get(
            f"/api/public/publications/{self.draft_publication.id}/"
        )

        self.assertEqual(response.status_code, 404)

    def test_owner_cannot_be_modified_through_memberships_api(self):
        client = self.make_client(self.owner)
        owner_membership = Membership.objects.get(
            organisation=self.organisation,
            user=self.owner,
        )

        response = client.patch(
            f"/api/memberships/{owner_membership.id}/",
            {"role": "admin"},
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        owner_membership.refresh_from_db()
        self.assertEqual(owner_membership.role, "owner")

    def test_owner_cannot_be_deleted_through_memberships_api(self):
        client = self.make_client(self.owner)
        owner_membership = Membership.objects.get(
            organisation=self.organisation,
            user=self.owner,
        )

        response = client.delete(f"/api/memberships/{owner_membership.id}/")

        self.assertEqual(response.status_code, 403)
        self.assertTrue(
            Membership.objects.filter(id=owner_membership.id).exists()
        )

    def test_owner_can_delete_regular_member(self):
        client = self.make_client(self.owner)
        member_membership = Membership.objects.get(
            organisation=self.organisation,
            user=self.member,
        )

        response = client.delete(f"/api/memberships/{member_membership.id}/")

        self.assertEqual(response.status_code, 204)
        self.assertFalse(
            Membership.objects.filter(id=member_membership.id).exists()
        )

    def test_owner_can_signal_interest_for_member_invitation_module(self):
        client = self.make_client(self.owner)

        response = client.post(
            f"/api/organisations/{self.organisation.slug}/member-invitation-interest/"
        )

        self.assertEqual(response.status_code, 200)
        interest = MembershipInvitationInterest.objects.get(
            organisation=self.organisation
        )
        self.assertEqual(interest.click_count, 1)
        self.assertEqual(interest.last_requested_by, self.owner)

    def test_member_cannot_be_promoted_to_owner(self):
        client = self.make_client(self.owner)
        member_membership = Membership.objects.get(
            organisation=self.organisation,
            user=self.member,
        )

        response = client.patch(
            f"/api/memberships/{member_membership.id}/",
            {"role": "owner"},
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        member_membership.refresh_from_db()
        self.assertEqual(member_membership.role, "member")

    def test_expired_trial_blocks_published_publication_but_allows_draft(self):
        self.organisation.subscription.status = Subscription.Status.TRIALING
        self.organisation.subscription.trial_end = timezone.now() - timedelta(days=1)
        self.organisation.subscription.save(update_fields=["status", "trial_end"])

        client = self.make_client(self.owner)

        published_response = client.post(
            "/api/publications/",
            {
                "organisation": self.organisation.id,
                "type": "information",
                "status": "published",
                "titre": "Publication bloquee",
                "contenu": "Ne doit pas etre publiee",
            },
            format="json",
        )
        draft_response = client.post(
            "/api/publications/",
            {
                "organisation": self.organisation.id,
                "type": "information",
                "status": "draft",
                "titre": "Brouillon autorise",
                "contenu": "Peut etre enregistre",
            },
            format="json",
        )

        self.assertEqual(published_response.status_code, 403)
        self.assertEqual(draft_response.status_code, 201)

    def test_canceled_subscription_keeps_publication_rights_until_period_end(self):
        self.organisation.subscription.status = Subscription.Status.CANCELED
        self.organisation.subscription.current_period_end = timezone.now() + timedelta(days=7)
        self.organisation.subscription.save(
            update_fields=["status", "current_period_end"]
        )

        client = self.make_client(self.owner)
        response = client.post(
            "/api/publications/",
            {
                "organisation": self.organisation.id,
                "type": "information",
                "status": "published",
                "titre": "Publication encore autorisee",
                "contenu": "Acces maintenu jusqu'a la fin de periode",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)

    @patch("core.billing_views.StripeService")
    def test_owner_can_create_checkout_session(self, stripe_service_cls):
        stripe_service_cls.return_value.create_checkout_session.return_value = {
            "id": "cs_test_123",
            "url": "https://checkout.stripe.test/session/cs_test_123",
        }
        client = self.make_client(self.owner)

        response = client.post(
            "/api/billing/checkout-session/",
            {"organisation_slug": self.organisation.slug},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["sessionId"], "cs_test_123")
        self.assertEqual(
            response.data["url"],
            "https://checkout.stripe.test/session/cs_test_123",
        )
        stripe_service_cls.return_value.create_checkout_session.assert_called_once()
        ctx = stripe_service_cls.return_value.create_checkout_session.call_args.args[0]
        self.assertEqual(ctx.trial_days, 90)

    @patch("core.billing_views.StripeService")
    def test_member_cannot_create_checkout_session(self, stripe_service_cls):
        client = self.make_client(self.member)

        response = client.post(
            "/api/billing/checkout-session/",
            {"organisation_slug": self.organisation.slug},
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        stripe_service_cls.return_value.create_checkout_session.assert_not_called()

    @patch("core.billing_views.StripeService")
    def test_stripe_webhook_accepts_valid_signed_event(self, stripe_service_cls):
        stripe_service_cls.return_value.construct_webhook_event.return_value = {
            "type": "checkout.session.completed"
        }
        client = self.make_client()

        response = client.post(
            "/api/billing/webhook/",
            data=b'{"id":"evt_test"}',
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="t=123,v1=test",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            {"received": True, "type": "checkout.session.completed"},
        )
        stripe_service_cls.return_value.construct_webhook_event.assert_called_once()

    @patch("core.billing_views.StripeService")
    def test_stripe_webhook_rejects_invalid_event(self, stripe_service_cls):
        stripe_service_cls.return_value.construct_webhook_event.side_effect = ValueError(
            "Signature invalide"
        )
        client = self.make_client()

        response = client.post(
            "/api/billing/webhook/",
            data=b'{"id":"evt_test"}',
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="t=123,v1=bad",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Webhook Stripe invalide", response.data["detail"])

    @patch("core.billing_views.StripeService")
    def test_checkout_completed_links_stripe_ids_to_subscription(self, stripe_service_cls):
        stripe_service_cls.return_value.construct_webhook_event.return_value = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "customer": "cus_123",
                    "subscription": "sub_123",
                    "metadata": {
                        "organisation_id": str(self.organisation.id),
                        "organisation_slug": self.organisation.slug,
                    },
                }
            },
        }
        client = self.make_client()

        response = client.post(
            "/api/billing/webhook/",
            data=b'{"id":"evt_test"}',
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="t=123,v1=test",
        )

        self.assertEqual(response.status_code, 200)
        subscription = Subscription.objects.get(organisation=self.organisation)
        self.assertEqual(subscription.stripe_customer_id, "cus_123")
        self.assertEqual(subscription.stripe_subscription_id, "sub_123")

    @patch("core.billing_views.StripeService")
    def test_subscription_updated_syncs_local_subscription_fields(self, stripe_service_cls):
        stripe_service_cls.return_value.construct_webhook_event.return_value = {
            "type": "customer.subscription.updated",
            "data": {
                "object": {
                    "id": "sub_live_123",
                    "customer": "cus_live_123",
                    "status": "active",
                    "trial_end": 1776360000,
                    "current_period_end": 1779042000,
                    "metadata": {
                        "organisation_id": str(self.organisation.id),
                    },
                }
            },
        }
        client = self.make_client()

        response = client.post(
            "/api/billing/webhook/",
            data=b'{"id":"evt_test"}',
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="t=123,v1=test",
        )

        self.assertEqual(response.status_code, 200)
        subscription = Subscription.objects.get(organisation=self.organisation)
        self.assertEqual(subscription.status, Subscription.Status.ACTIVE)
        self.assertEqual(subscription.stripe_customer_id, "cus_live_123")
        self.assertEqual(subscription.stripe_subscription_id, "sub_live_123")
        self.assertIsNotNone(subscription.current_period_end)
        self.assertFalse(subscription.cancel_at_period_end)
        self.assertIsNone(subscription.cancel_at)

    @patch("core.billing_views.StripeService")
    def test_subscription_updated_syncs_scheduled_cancellation(self, stripe_service_cls):
        stripe_service_cls.return_value.construct_webhook_event.return_value = {
            "type": "customer.subscription.updated",
            "data": {
                "object": {
                    "id": "sub_live_123",
                    "customer": "cus_live_123",
                    "status": "trialing",
                    "trial_end": 1781834400,
                    "current_period_end": None,
                    "cancel_at_period_end": True,
                    "cancel_at": 1781834400,
                    "metadata": {
                        "organisation_id": str(self.organisation.id),
                    },
                }
            },
        }
        client = self.make_client()

        response = client.post(
            "/api/billing/webhook/",
            data=b'{"id":"evt_test"}',
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="t=123,v1=test",
        )

        self.assertEqual(response.status_code, 200)
        subscription = Subscription.objects.get(organisation=self.organisation)
        self.assertEqual(subscription.status, Subscription.Status.TRIALING)
        self.assertTrue(subscription.cancel_at_period_end)
        self.assertIsNotNone(subscription.cancel_at)

    @patch("core.billing_views.StripeService")
    def test_subscription_deleted_marks_local_subscription_canceled(self, stripe_service_cls):
        self.organisation.subscription.status = Subscription.Status.ACTIVE
        self.organisation.subscription.stripe_customer_id = "cus_live_123"
        self.organisation.subscription.stripe_subscription_id = "sub_live_123"
        self.organisation.subscription.current_period_end = timezone.now() + timedelta(days=30)
        self.organisation.subscription.save()

        stripe_service_cls.return_value.construct_webhook_event.return_value = {
            "type": "customer.subscription.deleted",
            "data": {
                "object": {
                    "id": "sub_live_123",
                    "customer": "cus_live_123",
                    "status": "canceled",
                    "current_period_end": 1779042000,
                }
            },
        }
        client = self.make_client()

        response = client.post(
            "/api/billing/webhook/",
            data=b'{"id":"evt_test"}',
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="t=123,v1=test",
        )

        self.assertEqual(response.status_code, 200)
        subscription = Subscription.objects.get(organisation=self.organisation)
        self.assertEqual(subscription.status, Subscription.Status.CANCELED)
        self.assertIsNotNone(subscription.current_period_end)
        self.assertFalse(subscription.cancel_at_period_end)

    @patch("core.billing_views.StripeService")
    def test_invoice_paid_confirms_active_subscription(self, stripe_service_cls):
        self.organisation.subscription.status = Subscription.Status.TRIALING
        self.organisation.subscription.stripe_customer_id = "cus_live_123"
        self.organisation.subscription.stripe_subscription_id = "sub_live_123"
        self.organisation.subscription.save()

        stripe_service_cls.return_value.construct_webhook_event.return_value = {
            "type": "invoice.paid",
            "data": {
                "object": {
                    "subscription": "sub_live_123",
                    "customer": "cus_live_123",
                    "lines": {
                        "data": [
                            {
                                "period": {
                                    "end": 1779042000,
                                }
                            }
                        ]
                    },
                }
            },
        }
        client = self.make_client()

        response = client.post(
            "/api/billing/webhook/",
            data=b'{"id":"evt_test"}',
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="t=123,v1=test",
        )

        self.assertEqual(response.status_code, 200)
        subscription = Subscription.objects.get(organisation=self.organisation)
        self.assertEqual(subscription.status, Subscription.Status.ACTIVE)
        self.assertIsNotNone(subscription.current_period_end)

    @patch("core.billing_views.StripeService")
    def test_invoice_payment_failed_keeps_subscription_but_refreshes_stripe_refs(
        self, stripe_service_cls
    ):
        self.organisation.subscription.status = Subscription.Status.ACTIVE
        self.organisation.subscription.save(update_fields=["status"])

        stripe_service_cls.return_value.construct_webhook_event.return_value = {
            "type": "invoice.payment_failed",
            "data": {
                "object": {
                    "subscription": "sub_live_456",
                    "customer": "cus_live_456",
                    "parent": {
                        "subscription_details": {
                            "metadata": {
                                "organisation_id": str(self.organisation.id),
                            }
                        }
                    },
                }
            },
        }
        client = self.make_client()

        response = client.post(
            "/api/billing/webhook/",
            data=b'{"id":"evt_test"}',
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="t=123,v1=test",
        )

        self.assertEqual(response.status_code, 200)
        subscription = Subscription.objects.get(organisation=self.organisation)
        self.assertEqual(subscription.status, Subscription.Status.ACTIVE)
        self.assertEqual(subscription.stripe_customer_id, "cus_live_456")
        self.assertEqual(subscription.stripe_subscription_id, "sub_live_456")

    @patch("core.billing_views.StripeService")
    def test_owner_can_open_customer_portal(self, stripe_service_cls):
        self.organisation.subscription.stripe_customer_id = "cus_live_123"
        self.organisation.subscription.save(update_fields=["stripe_customer_id"])
        stripe_service_cls.return_value.create_customer_portal_session.return_value = {
            "url": "https://billing.stripe.test/session/portal_123",
        }
        client = self.make_client(self.owner)

        response = client.post(
            "/api/billing/customer-portal/",
            {"organisation_slug": self.organisation.slug},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["url"],
            "https://billing.stripe.test/session/portal_123",
        )

    @patch("core.billing_views.StripeService")
    def test_customer_portal_requires_stripe_customer(self, stripe_service_cls):
        client = self.make_client(self.owner)

        response = client.post(
            "/api/billing/customer-portal/",
            {"organisation_slug": self.organisation.slug},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Aucun compte client Stripe", response.data["detail"])
        stripe_service_cls.return_value.create_customer_portal_session.assert_not_called()

    @patch("core.billing_views.StripeService")
    def test_member_cannot_open_customer_portal(self, stripe_service_cls):
        self.organisation.subscription.stripe_customer_id = "cus_live_123"
        self.organisation.subscription.save(update_fields=["stripe_customer_id"])
        client = self.make_client(self.member)

        response = client.post(
            "/api/billing/customer-portal/",
            {"organisation_slug": self.organisation.slug},
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        stripe_service_cls.return_value.create_customer_portal_session.assert_not_called()

    def test_creating_published_publication_records_notification_dispatch(self):
        client = self.make_client(self.owner)

        response = client.post(
            "/api/publications/",
            {
                "organisation": self.organisation.id,
                "type": "information",
                "status": "published",
                "titre": "Nouvelle criée mobile",
                "contenu": "Une notification doit être enregistrée.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        dispatch = NotificationDispatch.objects.get(
            publication_id=response.data["id"],
            event_type=NotificationDispatch.EVENT_PUBLICATION_PUBLISHED,
        )
        self.assertEqual(dispatch.topic, f"eo_org_{self.organisation.slug}")
        self.assertEqual(dispatch.status, NotificationDispatch.STATUS_RECORDED)

    def test_creating_draft_publication_does_not_record_notification_dispatch(self):
        client = self.make_client(self.owner)

        response = client.post(
            "/api/publications/",
            {
                "organisation": self.organisation.id,
                "type": "information",
                "status": "draft",
                "titre": "Brouillon silencieux",
                "contenu": "Aucune notification ne doit partir.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertFalse(
            NotificationDispatch.objects.filter(publication_id=response.data["id"]).exists()
        )

    def test_publishing_existing_draft_records_notification_dispatch_once(self):
        client = self.make_client(self.owner)

        response = client.patch(
            f"/api/publications/{self.draft_publication.id}/",
            {"status": "published"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            NotificationDispatch.objects.filter(
                publication=self.draft_publication,
                event_type=NotificationDispatch.EVENT_PUBLICATION_PUBLISHED,
            ).count(),
            1,
        )


class PublicWebPushSubscriptionTests(TestCase):
    def setUp(self):
        self.organisation = Organisation.objects.create(
            nom="Source Push",
            slug="source-push",
        )
        self.client = APIClient()
        self.payload = {
            "organisation_slug": self.organisation.slug,
            "subscription": {
                "endpoint": "https://push.example.test/subscription/abc",
                "keys": {"p256dh": "public-key", "auth": "auth-secret"},
            },
        }

    def test_anonymous_browser_can_subscribe_to_public_source(self):
        response = self.client.post(
            "/api/public/push-subscriptions/",
            self.payload,
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        subscription = WebPushSubscription.objects.get()
        self.assertEqual(subscription.organisation, self.organisation)
        self.assertTrue(subscription.active)

    def test_resubscribing_updates_existing_endpoint(self):
        self.client.post("/api/public/push-subscriptions/", self.payload, format="json")
        self.payload["subscription"]["keys"]["auth"] = "new-auth-secret"

        response = self.client.post(
            "/api/public/push-subscriptions/",
            self.payload,
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(WebPushSubscription.objects.count(), 1)
        self.assertEqual(WebPushSubscription.objects.get().auth, "new-auth-secret")

    def test_subscription_rejects_non_https_endpoint(self):
        self.payload["subscription"]["endpoint"] = "http://push.example.test/abc"

        response = self.client.post(
            "/api/public/push-subscriptions/",
            self.payload,
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(WebPushSubscription.objects.exists())

    def test_anonymous_browser_can_unsubscribe_from_one_source(self):
        self.client.post("/api/public/push-subscriptions/", self.payload, format="json")

        response = self.client.delete(
            "/api/public/push-subscriptions/",
            self.payload,
            format="json",
        )

        self.assertEqual(response.status_code, 204)
        self.assertFalse(WebPushSubscription.objects.exists())
