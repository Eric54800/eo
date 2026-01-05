from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from core.views import (
    OrganisationViewSet,
    PublicationViewSet,
    PublicationAttachmentViewSet,
    MembershipViewSet,
)

router = DefaultRouter()
router.register(r"organisations", OrganisationViewSet, basename="organisation")
router.register(r"publications", PublicationViewSet, basename="publication")
router.register(r"attachments", PublicationAttachmentViewSet, basename="attachment")
router.register(r"memberships", MembershipViewSet, basename="membership")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/users/", include("users.urls")),
    path("api/", include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)