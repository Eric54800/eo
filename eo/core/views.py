# core/views.py
from datetime import timedelta

from django.utils import timezone
from django.contrib.auth import get_user_model

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response

from .models import (
    Organisation,
    Publication,
    Membership,
    PublicationAttachment,
    Subscription,
)
from .serializers import (
    OrganisationSerializer,
    PublicationSerializer,
    PublicationListSerializer,
    PublicationAttachmentSerializer,
    MembershipSerializer,
    MembershipInviteSerializer,
    SubscriptionSerializer,
)
from .permissions import IsOrganisationAdmin

User = get_user_model()


# -------------------------------------------------------
# Organisations
# -------------------------------------------------------
class OrganisationViewSet(viewsets.ModelViewSet):
    serializer_class = OrganisationSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "slug"

    def get_queryset(self):
        # Un utilisateur ne voit que ses organisations
        return Organisation.objects.filter(memberships__user=self.request.user).distinct()

    def perform_create(self, serializer):
        org = serializer.save()

        # 1) Owner membership (toujours)
        Membership.objects.get_or_create(
            user=self.request.user,
            organisation=org,
            defaults={"role": "owner"},
        )

        # 2) Subscription (trial)
        trial_days = int(org.periode_gratuite_jours or 0)

        Subscription.objects.get_or_create(
            organisation=org,
            defaults={
                "status": Subscription.Status.TRIALING,
                "trial_end": timezone.now() + timedelta(days=trial_days) if trial_days > 0 else None,
            },
        )

    @action(detail=True, methods=["get", "patch"], url_path="subscription")
    def subscription(self, request, slug=None):
        org = self.get_object()

        if request.method.upper() == "GET":
            return Response(
                SubscriptionSerializer(org.subscription).data,
                status=status.HTTP_200_OK,
            )

        # PATCH : seulement admin/owner
        if not IsOrganisationAdmin().has_object_permission(request, self, org):
            raise PermissionDenied("Vous n'avez pas les droits pour modifier l'abonnement.")

        serializer = SubscriptionSerializer(org.subscription, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


# -------------------------------------------------------
# Publications
# -------------------------------------------------------
class PublicationViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]

    filterset_fields = ["organisation__slug", "type", "status"]
    ordering_fields = ["date_publication", "event_start", "titre"]
    ordering = ["-date_publication"]
    search_fields = ["titre", "contenu", "event_location"]

    def get_queryset(self):
        user = self.request.user

        qs = (
            Publication.objects.filter(organisation__memberships__user=user)
            .select_related("organisation")
            .distinct()
        )

        # Member (non staff/superuser) -> seulement published
        if not user.is_staff and not user.is_superuser:
            qs = qs.filter(status=Publication.STATUS_PUBLISHED)

        return qs.order_by("-date_publication")

    def get_serializer_class(self):
        if self.action == "list":
            return PublicationListSerializer
        return PublicationSerializer

    def get_permissions(self):
        # Écriture publications : admin/owner
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated(), IsOrganisationAdmin()]

        # Nested attachments : POST/DELETE admin/owner ; GET auth
        if self.action == "attachments":
            if self.request.method.upper() in ["POST", "DELETE"]:
                return [permissions.IsAuthenticated(), IsOrganisationAdmin()]
            return [permissions.IsAuthenticated()]

        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        user = self.request.user

        # On privilégie organisation envoyée (API propre)
        org_id = self.request.data.get("organisation")
        org = None

        if org_id:
            org = Organisation.objects.filter(id=org_id).first()
        else:
            # fallback: première org du user (pratique en dev)
            m = Membership.objects.filter(user=user).select_related("organisation").first()
            org = m.organisation if m else None

        if not org:
            raise PermissionDenied("Organisation manquante ou introuvable.")

        # user doit être admin/owner de l'orga pour créer une publication
        if not (user.is_staff or user.is_superuser) and not org.memberships.filter(
            user=user, role__in=["owner", "admin"]
        ).exists():
            raise PermissionDenied("Vous n'avez pas les droits pour publier dans cette organisation.")

        serializer.save(organisation=org, created_by=user)

    @action(
        detail=True,
        methods=["get", "post", "delete"],
        url_path="attachments",
        parser_classes=[MultiPartParser, FormParser],
    )
    def attachments(self, request, pk=None):
        publication = self.get_object()

        if request.method.lower() == "get":
            qs = publication.attachments.all().order_by("-created_at")
            ser = PublicationAttachmentSerializer(qs, many=True, context={"request": request})
            return Response(ser.data, status=status.HTTP_200_OK)

        if request.method.lower() == "post":
            ser = PublicationAttachmentSerializer(
                data={
                    "publication": publication.id,
                    "display_name": request.data.get("display_name", ""),
                    "file": request.data.get("file"),
                },
                context={"request": request},
            )
            ser.is_valid(raise_exception=True)
            ser.save()
            return Response(ser.data, status=status.HTTP_201_CREATED)

        attachment_id = request.query_params.get("attachment_id")
        if not attachment_id:
            return Response(
                {"detail": "attachment_id est requis (query param)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        attachment = publication.attachments.filter(id=attachment_id).first()
        if not attachment:
            return Response(
                {"detail": "Pièce jointe introuvable pour cette publication."},
                status=status.HTTP_404_NOT_FOUND,
            )

        attachment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"], url_path="upcoming")
    def upcoming(self, request):
        now = timezone.now()
        qs = (
            self.get_queryset()
            .filter(
                status=Publication.STATUS_PUBLISHED,
                type=Publication.TYPE_EVENEMENT,
                event_start__gte=now,
            )
            .order_by("event_start")
        )

        page = self.paginate_queryset(qs)
        if page is not None:
            ser = PublicationListSerializer(page, many=True, context={"request": request})
            return self.get_paginated_response(ser.data)

        ser = PublicationListSerializer(qs, many=True, context={"request": request})
        return Response(ser.data, status=status.HTTP_200_OK)


# -------------------------------------------------------
# Attachments (endpoint non-nested)
# -------------------------------------------------------
class PublicationAttachmentViewSet(viewsets.ModelViewSet):
    serializer_class = PublicationAttachmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        user = self.request.user

        qs = (
            PublicationAttachment.objects.filter(
                publication__organisation__memberships__user=user
            )
            .select_related("publication", "publication__organisation")
            .distinct()
        )

        if not user.is_staff and not user.is_superuser:
            qs = qs.filter(publication__status=Publication.STATUS_PUBLISHED)

        return qs.order_by("-created_at")

    def _is_org_admin_for_publication(self, publication) -> bool:
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return True

        return publication.organisation.memberships.filter(
            user=user, role__in=["owner", "admin"]
        ).exists()

    def perform_create(self, serializer):
        publication = serializer.validated_data["publication"]
        if not self._is_org_admin_for_publication(publication):
            raise PermissionDenied("Vous n'avez pas les droits pour ajouter une pièce jointe.")
        serializer.save()

    def perform_update(self, serializer):
        attachment = self.get_object()
        if not self._is_org_admin_for_publication(attachment.publication):
            raise PermissionDenied("Vous n'avez pas les droits pour modifier une pièce jointe.")
        serializer.save()

    def perform_destroy(self, instance):
        if not self._is_org_admin_for_publication(instance.publication):
            raise PermissionDenied("Vous n'avez pas les droits pour supprimer une pièce jointe.")
        instance.delete()


# -------------------------------------------------------
# Memberships
# /api/memberships?organisation=<id>
# /api/memberships?organisation_slug=<slug>
# -------------------------------------------------------
class MembershipViewSet(viewsets.ModelViewSet):
    serializer_class = MembershipSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Membership.objects.filter(
            organisation__memberships__user=user
        ).select_related("user", "organisation")

        org_id = self.request.query_params.get("organisation")
        if org_id:
            qs = qs.filter(organisation_id=org_id)

        org_slug = self.request.query_params.get("organisation_slug")
        if org_slug:
            qs = qs.filter(organisation__slug=org_slug)

        return qs.order_by("-created_at")

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), IsOrganisationAdmin()]

    def create(self, request, *args, **kwargs):
        serializer = MembershipInviteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        role = serializer.validated_data["role"]
        organisation_id = request.data.get("organisation")

        if not organisation_id:
            return Response({"detail": "organisation est requis."}, status=status.HTTP_400_BAD_REQUEST)

        organisation = Organisation.objects.filter(id=organisation_id).first()
        if not organisation:
            return Response({"detail": "Organisation introuvable."}, status=status.HTTP_404_NOT_FOUND)

        # Vérifie droits (admin/owner) sur l'orga cible
        if not (request.user.is_staff or request.user.is_superuser) and not organisation.memberships.filter(
            user=request.user, role__in=["owner", "admin"]
        ).exists():
            raise PermissionDenied("Vous n'avez pas les droits pour inviter un membre.")

        target = User.objects.filter(email__iexact=email).first()
        if not target:
            return Response({"detail": "Aucun utilisateur avec cet email."}, status=status.HTTP_400_BAD_REQUEST)

        membership, created = Membership.objects.get_or_create(
            organisation=organisation,
            user=target,
            defaults={"role": role},
        )

        if not created:
            membership.role = role
            membership.save(update_fields=["role"])

        return Response(
            MembershipSerializer(membership, context={"request": request}).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


# -------------------------------------------------------
# Subscriptions (read-only)
# -------------------------------------------------------
class SubscriptionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Subscription.objects.filter(
            organisation__memberships__user=self.request.user
        ).select_related("organisation")