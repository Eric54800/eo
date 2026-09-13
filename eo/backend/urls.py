from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from core.billing_views import (
    CheckoutSessionView,
    CustomerPortalSessionView,
    StripeWebhookView,
)
from core.views import (
    OrganisationViewSet,
    PublicationViewSet,
    PublicationAttachmentViewSet,
    MembershipViewSet,
    PublicOrganisationViewSet,
    PublicPublicationViewSet,
)

router = DefaultRouter()
router.register(r"organisations", OrganisationViewSet, basename="organisation")
router.register(r"publications", PublicationViewSet, basename="publication")
router.register(r"attachments", PublicationAttachmentViewSet, basename="attachment")
router.register(r"memberships", MembershipViewSet, basename="membership")

# ✅ API publiques (sans auth)
router.register(
    r"public/organisations",
    PublicOrganisationViewSet,
    basename="public-organisation",
)
router.register(
    r"public/publications",
    PublicPublicationViewSet,
    basename="public-publication",
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/users/", include("users.urls")),
    path("api/billing/checkout-session/", CheckoutSessionView.as_view(), name="billing-checkout-session"),
    path("api/billing/customer-portal/", CustomerPortalSessionView.as_view(), name="billing-customer-portal"),
    path("api/billing/webhook/", StripeWebhookView.as_view(), name="billing-webhook"),
    path("api/", include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
