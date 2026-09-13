import json
import logging

from django.conf import settings
from django.utils import timezone

from core.models import NotificationDispatch, Publication, WebPushSubscription

logger = logging.getLogger(__name__)


def topic_for_organisation_slug(slug: str) -> str:
    return f"eo_org_{slug}"


def _build_publication_title(publication: Publication) -> str:
    if publication.type == Publication.TYPE_EVENEMENT:
        return f"Nouvel événement · {publication.organisation.nom}"
    return f"Nouvelle criée · {publication.organisation.nom}"


def _build_publication_body(publication: Publication) -> str:
    preview = (publication.contenu or "").strip().replace("\n", " ")
    if len(preview) > 120:
        preview = f"{preview[:117].rstrip()}..."
    return preview or publication.titre


def record_publication_published_dispatch(publication: Publication) -> NotificationDispatch:
    topic = topic_for_organisation_slug(publication.organisation.slug)
    dispatch = NotificationDispatch.objects.create(
        organisation=publication.organisation,
        publication=publication,
        event_type=NotificationDispatch.EVENT_PUBLICATION_PUBLISHED,
        topic=topic,
        title=_build_publication_title(publication),
        body=_build_publication_body(publication),
        payload={
            "organisation_slug": publication.organisation.slug,
            "publication_id": publication.id,
            "publication_type": publication.type,
            "topic": topic,
        },
        provider=NotificationDispatch.PROVIDER_INTERNAL,
        status=NotificationDispatch.STATUS_RECORDED,
    )

    logger.info(
        "Notification enregistrée pour %s sur le topic %s",
        publication.organisation.slug,
        topic,
    )
    return dispatch


def send_web_push_dispatch(dispatch: NotificationDispatch) -> NotificationDispatch:
    """Envoie une notification visible sans jamais bloquer la publication métier."""
    if not settings.WEB_PUSH_ENABLED or not settings.WEB_PUSH_VAPID_PRIVATE_KEY:
        return dispatch

    try:
        from pywebpush import WebPushException, webpush
    except ImportError:
        logger.exception("pywebpush n'est pas installé; notification conservée en attente.")
        return dispatch

    subscriptions = list(
        WebPushSubscription.objects.filter(
            organisation=dispatch.organisation,
            active=True,
        )
    )
    if not subscriptions:
        return dispatch

    message = json.dumps(
        {
            "title": dispatch.title,
            "body": dispatch.body,
            "url": (
                f"/app?source={dispatch.organisation.slug}"
                f"&criee={dispatch.publication_id}"
            ),
        },
        ensure_ascii=False,
    )
    sent_count = 0
    errors = []

    for subscription in subscriptions:
        try:
            webpush(
                subscription_info={
                    "endpoint": subscription.endpoint,
                    "keys": {
                        "p256dh": subscription.p256dh,
                        "auth": subscription.auth,
                    },
                },
                data=message,
                vapid_private_key=settings.WEB_PUSH_VAPID_PRIVATE_KEY,
                vapid_claims={"sub": settings.WEB_PUSH_VAPID_SUBJECT},
                ttl=24 * 60 * 60,
                timeout=5,
            )
            sent_count += 1
        except WebPushException as exc:
            response_status = getattr(getattr(exc, "response", None), "status_code", None)
            if response_status in (404, 410):
                subscription.active = False
                subscription.save(update_fields=["active", "updated_at"])
            errors.append(f"{response_status or 'erreur'}:{subscription.id}")
            logger.warning("Échec Web Push abonnement %s: %s", subscription.id, exc)
        except Exception as exc:
            errors.append(f"erreur:{subscription.id}")
            logger.exception("Échec inattendu Web Push abonnement %s: %s", subscription.id, exc)

    dispatch.provider = NotificationDispatch.PROVIDER_WEB_PUSH
    dispatch.payload = {
        **dispatch.payload,
        "subscriptions_count": len(subscriptions),
        "sent_count": sent_count,
    }
    dispatch.status = (
        NotificationDispatch.STATUS_SENT
        if sent_count > 0
        else NotificationDispatch.STATUS_FAILED
    )
    dispatch.delivered_at = timezone.now() if sent_count > 0 else None
    dispatch.last_error = ", ".join(errors)
    dispatch.save(
        update_fields=[
            "provider",
            "payload",
            "status",
            "delivered_at",
            "last_error",
        ]
    )
    return dispatch
