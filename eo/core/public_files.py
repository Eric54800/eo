import mimetypes

from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from .models import Publication, PublicationAttachment


@api_view(["GET"])
@permission_classes([AllowAny])
def public_publication_attachment_file(request, attachment_id):
    attachment = get_object_or_404(
        PublicationAttachment.objects.select_related("publication"),
        pk=attachment_id,
        publication__status=Publication.STATUS_PUBLISHED,
    )
    content_type = mimetypes.guess_type(attachment.file.name)[0] or "application/octet-stream"
    return FileResponse(
        attachment.file.open("rb"),
        content_type=content_type,
        as_attachment=True,
        filename=attachment.file.name.rsplit("/", 1)[-1],
        headers={"X-Content-Type-Options": "nosniff"},
    )
