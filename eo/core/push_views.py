from urllib.parse import urlparse

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .models import Organisation, WebPushSubscription


def _validated_payload(request):
    organisation_slug = str(request.data.get("organisation_slug", "")).strip()
    subscription = request.data.get("subscription") or {}
    endpoint = str(subscription.get("endpoint", "")).strip()
    keys = subscription.get("keys") or {}
    p256dh = str(keys.get("p256dh", "")).strip()
    auth = str(keys.get("auth", "")).strip()

    if not organisation_slug or not endpoint:
        return None, Response(
            {"detail": "organisation_slug et subscription.endpoint sont requis."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if len(endpoint) > 2048 or len(p256dh) > 512 or len(auth) > 255:
        return None, Response(
            {"detail": "Les données d’abonnement push sont trop longues."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    parsed_endpoint = urlparse(endpoint)
    if parsed_endpoint.scheme != "https" or not parsed_endpoint.netloc:
        return None, Response(
            {"detail": "Le point de terminaison push doit utiliser HTTPS."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    organisation = Organisation.objects.filter(slug=organisation_slug).first()
    if not organisation:
        return None, Response(
            {"detail": "Source publique introuvable."},
            status=status.HTTP_404_NOT_FOUND,
        )

    return {
        "organisation": organisation,
        "endpoint": endpoint,
        "p256dh": p256dh,
        "auth": auth,
    }, None


class PublicWebPushSubscriptionView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "web_push_subscription"

    def post(self, request):
        payload, error = _validated_payload(request)
        if error:
            return error
        if not payload["p256dh"] or not payload["auth"]:
            return Response(
                {"detail": "Les clés p256dh et auth sont requises."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        subscription, created = WebPushSubscription.objects.update_or_create(
            organisation=payload["organisation"],
            endpoint=payload["endpoint"],
            defaults={
                "p256dh": payload["p256dh"],
                "auth": payload["auth"],
                "user_agent": request.headers.get("User-Agent", "")[:500],
                "active": True,
            },
        )
        return Response(
            {"active": subscription.active},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    def delete(self, request):
        payload, error = _validated_payload(request)
        if error:
            return error
        WebPushSubscription.objects.filter(
            organisation=payload["organisation"],
            endpoint=payload["endpoint"],
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
