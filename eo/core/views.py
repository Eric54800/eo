# core/views.py
from datetime import timedelta

from django.utils import timezone
from django.contrib.auth import get_user_model

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import (
    Organisation,
    OrganisationPublicDocument,
    Publication,
    Membership,
    MembershipInvitationInterest,
    PublicationAttachment,
    Subscription,
)
from .serializers import (
    OrganisationSerializer,
    OrganisationPublicDocumentSerializer,
    OrganisationPublicSerializer,
    PublicPublicationDetailSerializer,
    PublicationSerializer,
    PublicationListSerializer,
    PublicationAttachmentSerializer,
    MembershipSerializer,
    MembershipInviteSerializer,
    SubscriptionSerializer,
)
from .permissions import IsOrganisationAdmin
from .services.notifications import record_publication_published_dispatch

User = get_user_model()


# -------------------------------------------------------
# Organisations
# -------------------------------------------------------
class OrganisationViewSet(viewsets.ModelViewSet):
    serializer_class = OrganisationSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "slug"
    parser_classes = [JSONParser, MultiPartParser, FormParser]

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

    @action(
        detail=True,
        methods=["get", "post", "delete"],
        url_path="public-documents",
        parser_classes=[MultiPartParser, FormParser],
    )
    def public_documents(self, request, slug=None):
        org = self.get_object()

        if request.method.lower() == "get":
            qs = org.public_documents.all().order_by("-created_at")
            ser = OrganisationPublicDocumentSerializer(
                qs, many=True, context={"request": request}
            )
            return Response(ser.data, status=status.HTTP_200_OK)

        if not IsOrganisationAdmin().has_object_permission(request, self, org):
            raise PermissionDenied("Vous n'avez pas les droits pour modifier la page publique.")

        if request.method.lower() == "post":
            ser = OrganisationPublicDocumentSerializer(
                data={
                    "organisation": org.id,
                    "display_name": request.data.get("display_name", ""),
                    "file": request.data.get("file"),
                },
                context={"request": request},
            )
            ser.is_valid(raise_exception=True)
            ser.save()
            return Response(ser.data, status=status.HTTP_201_CREATED)

        document_id = request.query_params.get("document_id")
        if not document_id:
            return Response(
                {"detail": "document_id est requis (query param)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        document = org.public_documents.filter(id=document_id).first()
        if not document:
            return Response(
                {"detail": "Document public introuvable pour cette organisation."},
                status=status.HTTP_404_NOT_FOUND,
            )

        document.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

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

    @action(detail=True, methods=["post"], url_path="member-invitation-interest")
    def member_invitation_interest(self, request, slug=None):
        org = self.get_object()

        if not IsOrganisationAdmin().has_object_permission(request, self, org):
            raise PermissionDenied(
                "Vous n'avez pas les droits pour gérer les membres de cette structure."
            )

        interest, _ = MembershipInvitationInterest.objects.get_or_create(
            organisation=org,
            defaults={
                "click_count": 0,
                "last_requested_by": request.user,
            },
        )
        interest.click_count += 1
        interest.last_requested_by = request.user
        interest.save(update_fields=["click_count", "last_requested_by", "last_requested_at"])

        return Response(
            {
                "detail": "Le module d'invitation est en cours de développement. Votre intérêt a bien été pris en compte.",
                "click_count": interest.click_count,
            },
            status=status.HTTP_200_OK,
        )


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

    def _get_org_subscription(self, organisation):
        return Subscription.objects.filter(organisation=organisation).first()

    def get_queryset(self):
        user = self.request.user

        qs = (
            Publication.objects.filter(organisation__memberships__user=user)
            .select_related("organisation")
            .distinct()
        )

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

        target_status = serializer.validated_data.get("status", Publication.STATUS_DRAFT)
        subscription = self._get_org_subscription(org)
        if target_status == Publication.STATUS_PUBLISHED and (
            subscription is None or not subscription.publication_access_active()
        ):
            raise PermissionDenied(
                "Votre essai ou votre abonnement ne vous permet plus de publier. Vous pouvez encore enregistrer un brouillon."
            )

        publication = serializer.save(organisation=org)
        if publication.status == Publication.STATUS_PUBLISHED:
            record_publication_published_dispatch(publication)

    def perform_update(self, serializer):
        publication = self.get_object()
        previous_status = publication.status
        target_status = serializer.validated_data.get("status", publication.status)
        subscription = self._get_org_subscription(publication.organisation)

        if target_status == Publication.STATUS_PUBLISHED and (
            subscription is None or not subscription.publication_access_active()
        ):
            raise PermissionDenied(
                "Votre essai ou votre abonnement ne vous permet plus de publier. Vous pouvez encore enregistrer un brouillon."
            )

        publication = serializer.save()
        if (
            previous_status != Publication.STATUS_PUBLISHED
            and publication.status == Publication.STATUS_PUBLISHED
        ):
            record_publication_published_dispatch(publication)

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

    def _can_manage_organisation(self, user, organisation) -> bool:
        if user.is_staff or user.is_superuser:
            return True
        return organisation.memberships.filter(
            user=user,
            role__in=["owner", "admin"],
        ).exists()

    def _validate_role_change(self, request, membership, next_role: str):
        if next_role == "owner":
            raise PermissionDenied(
                "Le rôle propriétaire est réservé à la création de la structure."
            )

        if membership.role == "owner":
            raise PermissionDenied(
                "Le propriétaire ne peut pas être modifié depuis la gestion des membres."
            )

        if not self._can_manage_organisation(request.user, membership.organisation):
            raise PermissionDenied(
                "Vous n'avez pas les droits pour modifier ce membre."
            )

    def _validate_delete(self, request, membership):
        if membership.role == "owner":
            raise PermissionDenied(
                "Le propriétaire ne peut pas être retiré depuis la gestion des membres."
            )

        if not self._can_manage_organisation(request.user, membership.organisation):
            raise PermissionDenied(
                "Vous n'avez pas les droits pour retirer ce membre."
            )

    def create(self, request, *args, **kwargs):
        serializer = MembershipInviteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        role = serializer.validated_data["role"]
        organisation_id = request.data.get("organisation")

        if not organisation_id:
            return Response({"detail": "Le champ organisation est requis."}, status=status.HTTP_400_BAD_REQUEST)

        organisation = Organisation.objects.filter(id=organisation_id).first()
        if not organisation:
            return Response({"detail": "Organisation introuvable."}, status=status.HTTP_404_NOT_FOUND)

        if not self._can_manage_organisation(request.user, organisation):
            raise PermissionDenied("Vous n'avez pas les droits pour inviter un membre.")

        if role == "owner":
            raise PermissionDenied(
                "Le rôle propriétaire est réservé à la création de la structure."
            )

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

    def perform_update(self, serializer):
        membership = self.get_object()
        next_role = serializer.validated_data.get("role", membership.role)
        self._validate_role_change(self.request, membership, next_role)
        serializer.save()

    def perform_destroy(self, instance):
        self._validate_delete(self.request, instance)
        instance.delete()


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


# -------------------------------------------------------
# API publique (sans auth)
# -------------------------------------------------------
class PublicOrganisationViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [AllowAny]
    serializer_class = OrganisationPublicSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return Organisation.objects.select_related("subscription").order_by("nom")


class PublicPublicationViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [AllowAny]
    serializer_class = PublicationListSerializer

    def get_queryset(self):
        qs = Publication.objects.filter(
            status=Publication.STATUS_PUBLISHED
        ).select_related(
            "organisation",
            "organisation__subscription",
        ).order_by(
            "-date_publication",
            "-id",
        )
        slug = (
            self.request.query_params.get("organisation_slug")
            or self.request.query_params.get("organisation__slug")
        )
        if slug:
            qs = qs.filter(organisation__slug=slug)
        return qs

    def get_serializer_class(self):
        if self.action == "retrieve":
            return PublicPublicationDetailSerializer
        return PublicationListSerializer
