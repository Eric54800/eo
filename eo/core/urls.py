from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrganisationViewSet, PublicationViewSet, SubscriptionViewSet

router = DefaultRouter()
router.register("organisations", OrganisationViewSet, basename="organisation")
router.register("publications", PublicationViewSet, basename="publication")
router.register(r"subscriptions", SubscriptionViewSet, basename="subscription")

urlpatterns = [
    path("", include(router.urls)),
]