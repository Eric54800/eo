from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.conf import settings


class StripeConfigurationError(RuntimeError):
    pass


def _load_stripe_module():
    try:
        import stripe  # type: ignore
    except ImportError as exc:
        raise StripeConfigurationError(
            "La librairie Stripe n'est pas installée. Ajoutez `stripe` aux dépendances du backend."
        ) from exc

    if not settings.STRIPE_SECRET_KEY:
        raise StripeConfigurationError("STRIPE_SECRET_KEY n'est pas configurée.")

    stripe.api_key = settings.STRIPE_SECRET_KEY
    return stripe


@dataclass(frozen=True)
class StripeCheckoutContext:
    organisation_id: int
    organisation_slug: str
    organisation_name: str
    customer_email: str
    trial_days: int = 0


class StripeService:
    """
    Point d'entree unique pour les interactions Stripe.
    Aucun endpoint metier n'est branche ici pour l'instant:
    on prepare seulement le socle reutilisable.
    """

    def __init__(self):
        self._stripe = _load_stripe_module()

    def create_checkout_session(self, ctx: StripeCheckoutContext) -> Any:
        if not settings.STRIPE_PRICE_ID:
            raise StripeConfigurationError("STRIPE_PRICE_ID n'est pas configuré.")

        success_url = settings.STRIPE_SUCCESS_URL.format(slug=ctx.organisation_slug)
        cancel_url = settings.STRIPE_CANCEL_URL.format(slug=ctx.organisation_slug)
        subscription_data = {
            "metadata": {
                "organisation_id": str(ctx.organisation_id),
                "organisation_slug": ctx.organisation_slug,
            }
        }
        if ctx.trial_days > 0:
            subscription_data["trial_period_days"] = ctx.trial_days

        return self._stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": settings.STRIPE_PRICE_ID, "quantity": 1}],
            customer_email=ctx.customer_email,
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "organisation_id": str(ctx.organisation_id),
                "organisation_slug": ctx.organisation_slug,
                "organisation_name": ctx.organisation_name,
            },
            subscription_data=subscription_data,
        )

    def create_customer_portal_session(
        self,
        *,
        customer_id: str,
        organisation_slug: str,
    ) -> Any:
        return self._stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=settings.STRIPE_SUCCESS_URL.format(slug=organisation_slug),
        )

    def construct_webhook_event(self, payload: bytes, signature: str | None) -> Any:
        if not settings.STRIPE_WEBHOOK_SECRET:
            raise StripeConfigurationError("STRIPE_WEBHOOK_SECRET n'est pas configurée.")
        if not signature:
            raise StripeConfigurationError(
                "La signature Stripe est manquante."
            )

        return self._stripe.Webhook.construct_event(
            payload=payload,
            sig_header=signature,
            secret=settings.STRIPE_WEBHOOK_SECRET,
        )
