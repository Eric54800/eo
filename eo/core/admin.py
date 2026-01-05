from django.contrib import admin
from django.utils.html import format_html

from .models import Organisation, Publication, Membership, PublicationAttachment


# ---------------------------------------------------------------------------
# UTILITAIRES D'AFFICHAGE
# ---------------------------------------------------------------------------

def badge(text, color):
    return format_html(
        '<span style="background:{}; color:white; padding:3px 8px; border-radius:6px; font-size:12px;">{}</span>',
        color,
        text
    )


# ---------------------------------------------------------------------------
# ADMIN : Organisation
# ---------------------------------------------------------------------------

@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    list_display = (
        "nom",
        "created_by",
        "ville",
        "pays",
        "email",
        "telephone",
        "date_creation",
        "badge_nb_publications",
    )

    search_fields = ("nom", "ville", "email")
    list_filter = ("pays", "date_creation", "created_by")
    ordering = ("nom",)

    prepopulated_fields = {"slug": ("nom",)}
    readonly_fields = ("date_creation",)

    fieldsets = (
        ("Informations générales", {"fields": ("nom", "slug", "created_by")}),
        ("Adresse", {"fields": ("adresse", "code_postal", "ville", "pays")}),
        ("Contact", {"fields": ("email", "telephone")}),
        ("Paramètres", {"fields": ("periode_gratuite_jours",)}),
        ("Dates", {"fields": ("date_creation",)}),
    )

    def badge_nb_publications(self, obj):
        count = obj.publications.count()
        color = "#0a7cff" if count > 0 else "gray"
        return badge(str(count), color)

    badge_nb_publications.short_description = "Publications"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(memberships__user=request.user).distinct()


# ---------------------------------------------------------------------------
# ADMIN : Publication (avec inline attachments)
# ---------------------------------------------------------------------------

class PublicationAttachmentInline(admin.TabularInline):
    model = PublicationAttachment
    extra = 0
    fields = ("display_name", "file", "created_at")
    readonly_fields = ("created_at",)


@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    list_display = (
        "titre",
        "organisation",
        "date_publication",
        "badge_is_published",
        "preview_contenu",
    )

    list_filter = ("status", "type", "date_publication", "organisation")
    search_fields = ("titre", "contenu")
    ordering = ("-date_publication",)
    list_per_page = 20

    readonly_fields = ("date_publication",)
    inlines = [PublicationAttachmentInline]

    fieldsets = (
        ("Informations principales", {"fields": ("titre", "organisation", "contenu")}),
        ("Publication", {"fields": ("date_publication", "is_published")}),
    )

    def badge_is_published(self, obj):
        if obj.status == obj.STATUS_PUBLISHED:
            return badge("Publié", "#28a745")
        if obj.status == obj.STATUS_ARCHIVED:
            return badge("Archivé", "#6c757d")
        return badge("Brouillon", "#dc3545")

    badge_is_published.short_description = "Statut"

    def preview_contenu(self, obj):
        text = (obj.contenu[:50] + "...") if len(obj.contenu) > 50 else obj.contenu
        return format_html("<span style='color:#555;'>{}</span>", text)

    preview_contenu.short_description = "Aperçu"

    @admin.action(description="Publier la sélection")
    def publier(self, request, queryset):
        queryset.update(is_published=True)

    @admin.action(description="Dépublier la sélection")
    def depublier(self, request, queryset):
        queryset.update(is_published=False)

    actions = ["publier", "depublier"]


# ---------------------------------------------------------------------------
# ADMIN : Membership
# ---------------------------------------------------------------------------

@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "organisation", "role", "created_at")
    list_filter = ("role", "organisation")
    search_fields = ("user__email", "organisation__nom")
    ordering = ("organisation", "user")