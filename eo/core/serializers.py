from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.urls import reverse

from .models import (
    Organisation,
    OrganisationPublicDocument,
    Publication,
    PublicationAttachment,
    Membership,
    Subscription,
)

User = get_user_model()



# ---------------------------------------------------------------------------
# SERIALIZER : Subscription
# ---------------------------------------------------------------------------

class SubscriptionPublicSerializer(serializers.ModelSerializer):
    publication_access_active = serializers.SerializerMethodField()
    """
    Serializer "public" (embeddé dans Organisation) : pas d'id/organisation
    """
    class Meta:
        model = Subscription
        fields = [
            "status",
            "trial_end",
            "current_period_end",
            "cancel_at_period_end",
            "cancel_at",
            "publication_access_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_publication_access_active(self, obj):
        return obj.publication_access_active()


class SubscriptionSerializer(serializers.ModelSerializer):
    """
    Serializer complet (pour /api/subscriptions/)
    """
    organisation = serializers.PrimaryKeyRelatedField(read_only=True)
    publication_access_active = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = [
            "id",
            "organisation",
            "status",
            "trial_end",
            "current_period_end",
            "cancel_at_period_end",
            "cancel_at",
            "publication_access_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "organisation", "created_at", "updated_at"]

    def validate(self, attrs):
        # Si le client essaye de forcer organisation => on refuse explicitement (400)
        if "organisation" in getattr(self, "initial_data", {}):
            raise serializers.ValidationError(
                {"organisation": "Ce champ est en lecture seule."}
            )
        return attrs

    def get_publication_access_active(self, obj):
        return obj.publication_access_active()




# ---------------------------------------------------------------------------
# SERIALIZER : Organisation (complet)
# ---------------------------------------------------------------------------

class OrganisationSerializer(serializers.ModelSerializer):
    subscription = SubscriptionPublicSerializer(read_only=True)
    public_cover_image_url = serializers.SerializerMethodField()
    public_avatar_image_url = serializers.SerializerMethodField()
    public_documents = serializers.SerializerMethodField()
    billing_portal_available = serializers.SerializerMethodField()

    class Meta:
        model = Organisation
        fields = [
            "id",
            "nom",
            "slug",
            "created_by",
            "adresse",
            "code_postal",
            "ville",
            "pays",
            "email",
            "telephone",
            "presentation",
            "public_email",
            "public_image",
            "public_cover_image",
            "public_cover_image_url",
            "public_avatar_image",
            "public_avatar_image_url",
            "cover_position_x",
            "cover_position_y",
            "horaires",
            "date_creation",
            "periode_gratuite_jours",
            "subscription",
            "public_documents",
            "billing_portal_available",
        ]

    def get_public_cover_image_url(self, obj):
        request = self.context.get("request")
        if not obj.public_cover_image:
            return None
        if request is not None:
            return request.build_absolute_uri(obj.public_cover_image.url)
        return obj.public_cover_image.url

    def get_public_avatar_image_url(self, obj):
        request = self.context.get("request")
        if not obj.public_avatar_image:
            return None
        if request is not None:
            return request.build_absolute_uri(obj.public_avatar_image.url)
        return obj.public_avatar_image.url

    def get_public_documents(self, obj):
        request = self.context.get("request")
        return PublicOrganisationDocumentSerializer(
            obj.public_documents.all().order_by("-created_at"),
            many=True,
            context={"request": request},
        ).data

    def get_billing_portal_available(self, obj):
        subscription = getattr(obj, "subscription", None)
        return bool(subscription and subscription.stripe_customer_id)


# ---------------------------------------------------------------------------
# SERIALIZER : Organisation (mini pour les listes)
# ---------------------------------------------------------------------------

class OrganisationMiniSerializer(serializers.ModelSerializer):
    subscription = SubscriptionPublicSerializer(read_only=True)

    class Meta:
        model = Organisation
        fields = ["id", "nom", "slug", "subscription"]


class PublicOrganisationMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organisation
        fields = ["id", "nom", "slug"]
        read_only_fields = fields


class OrganisationPublicSerializer(serializers.ModelSerializer):
    subscription = SubscriptionPublicSerializer(read_only=True)
    public_cover_image_url = serializers.SerializerMethodField()
    public_avatar_image_url = serializers.SerializerMethodField()
    public_documents = serializers.SerializerMethodField()

    class Meta:
        model = Organisation
        fields = [
            "id",
            "nom",
            "slug",
            "adresse",
            "code_postal",
            "ville",
            "pays",
            "presentation",
            "public_email",
            "telephone",
            "public_cover_image_url",
            "public_avatar_image_url",
            "cover_position_x",
            "cover_position_y",
            "horaires",
            "public_documents",
            "subscription",
        ]
        read_only_fields = fields

    def get_public_cover_image_url(self, obj):
        request = self.context.get("request")
        if not obj.public_cover_image:
            return None
        if request is not None:
            return request.build_absolute_uri(obj.public_cover_image.url)
        return obj.public_cover_image.url

    def get_public_avatar_image_url(self, obj):
        request = self.context.get("request")
        if not obj.public_avatar_image:
            return None
        if request is not None:
            return request.build_absolute_uri(obj.public_avatar_image.url)
        return obj.public_avatar_image.url

    def get_public_documents(self, obj):
        request = self.context.get("request")
        return PublicOrganisationDocumentSerializer(
            obj.public_documents.all().order_by("-created_at"),
            many=True,
            context={"request": request},
        ).data


class OrganisationPublicDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganisationPublicDocument
        fields = ["id", "organisation", "file", "display_name", "created_at"]
        read_only_fields = ["id", "created_at"]


class PublicOrganisationDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganisationPublicDocument
        fields = ["id", "file", "display_name"]
        read_only_fields = fields


# ---------------------------------------------------------------------------
# SERIALIZER : PublicationAttachment
# ---------------------------------------------------------------------------

class PublicationAttachmentSerializer(serializers.ModelSerializer):
    file_size = serializers.SerializerMethodField()

    class Meta:
        model = PublicationAttachment
        fields = ["id", "publication", "file", "display_name", "file_size", "created_at"]
        read_only_fields = ["id", "created_at", "file_size"]

    def get_file_size(self, obj):
        try:
            return obj.file.size
        except Exception:
            return 0


class PublicPublicationAttachmentSerializer(serializers.ModelSerializer):
    file = serializers.SerializerMethodField()

    class Meta:
        model = PublicationAttachment
        fields = ["id", "file", "display_name"]
        read_only_fields = fields

    def get_file(self, obj):
        request = self.context.get("request")
        path = reverse("public-publication-attachment-file", args=[obj.pk])
        return request.build_absolute_uri(path) if request else path


# ---------------------------------------------------------------------------
# SERIALIZER : Publication (LISTE)
# - léger : organisation mini + preview + count PJ
# ---------------------------------------------------------------------------

class PublicationListSerializer(serializers.ModelSerializer):
    organisation = OrganisationMiniSerializer(read_only=True)
    contenu_preview = serializers.SerializerMethodField()
    attachments_count = serializers.IntegerField(source="attachments.count", read_only=True)
    attachments = PublicPublicationAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = Publication
        fields = [
            "id",
            "organisation",
            "type",
            "status",
            "titre",
            "contenu_preview",
            "date_publication",
            "event_start",
            "event_end",
            "event_location",
            "attachments_count",
            "attachments",
        ]
        read_only_fields = fields

    def get_contenu_preview(self, obj):
        if not obj.contenu:
            return ""
        return obj.contenu[:120] + ("…" if len(obj.contenu) > 120 else "")


class PublicPublicationDetailSerializer(serializers.ModelSerializer):
    organisation = PublicOrganisationMiniSerializer(read_only=True)
    attachments = PublicPublicationAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = Publication
        fields = [
            "id",
            "organisation",
            "type",
            "status",
            "titre",
            "contenu",
            "date_publication",
            "event_start",
            "event_end",
            "event_location",
            "attachments",
        ]
        read_only_fields = fields


# ---------------------------------------------------------------------------
# SERIALIZER : Publication (DETAIL / CREATE / UPDATE)
# - inclut PJ + validations event
# ---------------------------------------------------------------------------

class PublicationSerializer(serializers.ModelSerializer):
    organisation = OrganisationMiniSerializer(read_only=True)
    attachments = PublicationAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = Publication
        fields = [
            "id",
            "organisation",
            "attachments",
            "type",
            "status",
            "titre",
            "contenu",
            "date_publication",
            "event_start",
            "event_end",
            "event_location",
        ]
        read_only_fields = [
            "id",
            "organisation",
            "date_publication",
            "attachments",
        ]

    def validate(self, attrs):
        """
        Règles métier :
        - si type == 'evenement' → event_start obligatoire
        - event_end doit être >= event_start
        """
        publication_type = attrs.get("type", self.instance.type if self.instance else None)
        event_start = attrs.get("event_start", self.instance.event_start if self.instance else None)
        event_end = attrs.get("event_end", self.instance.event_end if self.instance else None)

        if publication_type == Publication.TYPE_EVENEMENT and not event_start:
            raise serializers.ValidationError({
                "event_start": "Ce champ est obligatoire pour une publication de type 'evenement'."
            })

        if event_start and event_end and event_end < event_start:
            raise serializers.ValidationError({
                "event_end": "event_end doit être postérieur à event_start."
            })

        return attrs


# ---------------------------------------------------------------------------
# SERIALIZER : Membership (liste / update)
# ---------------------------------------------------------------------------

class MembershipSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    organisation_slug = serializers.SlugField(source="organisation.slug", read_only=True)

    class Meta:
        model = Membership
        fields = [
            "id",
            "organisation",
            "organisation_slug",
            "user",
            "user_email",
            "role",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "organisation",
            "user",
            "created_at",
            "user_email",
            "organisation_slug",
        ]


# ---------------------------------------------------------------------------
# SERIALIZER : Membership (invite/create via email)
# ---------------------------------------------------------------------------

class MembershipInviteSerializer(serializers.ModelSerializer):
    """
    Utilisé pour POST /api/memberships/ avec: {"organisation": <id>, "email": "...", "role": "..."}
    L'email est résolu vers un User existant.
    """
    email = serializers.EmailField(write_only=True, required=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Membership
        fields = [
            "id",
            "organisation",
            "user",
            "user_email",
            "role",
            "created_at",
            "email",
        ]
        read_only_fields = ["id", "user", "user_email", "created_at"]

    def validate_email(self, value):
        if not User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Aucun utilisateur avec cet email.")
        return value
