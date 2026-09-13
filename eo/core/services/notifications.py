import logging

from core.models import NotificationDispatch, Publication

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
