from django.shortcuts import get_object_or_404

from rest_framework import permissions, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Organisation
from core.permissions import IsOrganisationAdmin
from core.services.stripe_service import (
    StripeCheckoutContext,
    StripeConfigurationError,
    StripeService,
)
from core.services.subscription_sync import SubscriptionSyncService


class CheckoutSessionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        organisation = self._get_organisation(request)

        if not IsOrganisationAdmin().has_object_permission(
            request, self, organisation
        ):
            raise PermissionDenied(
                "Vous n'avez pas les droits pour gérer l'abonnement de cette structure."
            )

        customer_email = request.user.email
        if not customer_email:
            raise ValidationError({"detail": "L'utilisateur courant n'a pas d'adresse e-mail."})

        try:
            session = StripeService().create_checkout_session(
                StripeCheckoutContext(
                    organisation_id=organisation.id,
                    organisation_slug=organisation.slug,
                    organisation_name=organisation.nom,
                    customer_email=customer_email,
                    trial_days=int(organisation.periode_gratuite_jours or 0),
                )
            )
        except StripeConfigurationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            {
                "sessionId": session.get("id") if isinstance(session, dict) else session.id,
                "url": session.get("url") if isinstance(session, dict) else session.url,
            },
            status=status.HTTP_200_OK,
        )

    def _get_organisation(self, request):
        organisation_id = request.data.get("organisation")
        organisation_slug = request.data.get("organisation_slug")

        if organisation_id:
            return get_object_or_404(Organisation, id=organisation_id)

        if organisation_slug:
            return get_object_or_404(Organisation, slug=organisation_slug)

        raise ValidationError(
            {"detail": "Le champ organisation ou organisation_slug est requis."}
        )


class CustomerPortalSessionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        organisation = CheckoutSessionView()._get_organisation(request)

        if not IsOrganisationAdmin().has_object_permission(
            request, self, organisation
        ):
            raise PermissionDenied(
                "Vous n'avez pas les droits pour gérer l'abonnement de cette structure."
            )

        subscription = getattr(organisation, "subscription", None)
        customer_id = getattr(subscription, "stripe_customer_id", None)
        if not customer_id:
            raise ValidationError(
                {"detail": "Aucun compte client Stripe n'est encore rattaché à cette structure."}
            )

        try:
            session = StripeService().create_customer_portal_session(
                customer_id=customer_id,
                organisation_slug=organisation.slug,
            )
        except StripeConfigurationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            {
                "url": session.get("url") if isinstance(session, dict) else session.url,
            },
            status=status.HTTP_200_OK,
        )


class StripeWebhookView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        payload = request.body
        signature = request.headers.get("Stripe-Signature")

        try:
            event = StripeService().construct_webhook_event(payload, signature)
        except StripeConfigurationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except Exception as exc:
            return Response(
                {"detail": f"Webhook Stripe invalide: {exc}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        event_type = event.get("type") if isinstance(event, dict) else getattr(event, "type", "")
        SubscriptionSyncService().handle_event(event)

        return Response(
            {
                "received": True,
                "type": event_type,
            },
            status=status.HTTP_200_OK,
        )
