from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.conf import settings


# ---------------------------------------------------------------------------
# MODELE : Organisation
# ---------------------------------------------------------------------------

class Organisation(models.Model):
    nom = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="organisations_creees",
    )
    adresse = models.CharField(max_length=255, blank=True)
    code_postal = models.CharField(max_length=20, blank=True)
    ville = models.CharField(max_length=100, blank=True)
    pays = models.CharField(max_length=100, blank=True)

    email = models.EmailField(blank=True)
    telephone = models.CharField(max_length=50, blank=True)

    date_creation = models.DateTimeField(auto_now_add=True)
    periode_gratuite_jours = models.PositiveIntegerField(default=90)

    def fin_periode_gratuite(self):
        if not self.date_creation:
            return None
        return self.date_creation + timezone.timedelta(
            days=self.periode_gratuite_jours
        )

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nom)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nom


# ---------------------------------------------------------------------------
# MODELE : Publication
# ---------------------------------------------------------------------------

class Publication(models.Model):

    TYPE_INFORMATION = "information"
    TYPE_EVENEMENT = "evenement"

    TYPE_CHOICES = [
        (TYPE_INFORMATION, "Information"),
        (TYPE_EVENEMENT, "Événement"),
    ]

    STATUS_DRAFT = "draft"
    STATUS_PUBLISHED = "published"
    STATUS_ARCHIVED = "archived"

    STATUS_CHOICES = [
        (STATUS_DRAFT, "Brouillon"),
        (STATUS_PUBLISHED, "Publié"),
        (STATUS_ARCHIVED, "Archivé"),
    ]

    organisation = models.ForeignKey(
        Organisation,
        on_delete=models.CASCADE,
        related_name="publications"
    )

    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default=TYPE_INFORMATION,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT,
    )
    is_published = models.BooleanField(default=False, db_index=True)

    titre = models.CharField(max_length=255)
    contenu = models.TextField()

    date_publication = models.DateTimeField(default=timezone.now)

    event_start = models.DateTimeField(null=True, blank=True)
    event_end = models.DateTimeField(null=True, blank=True)
    event_location = models.CharField(max_length=255, blank=True)

    def save(self, *args, **kwargs):
        # Source de vérité unique
        self.is_published = self.status == self.STATUS_PUBLISHED
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.titre} ({self.organisation.nom})"

class Membership(models.Model):
    ROLE_CHOICES = (
        ("owner", "Owner"),
        ("admin", "Admin"),
        ("member", "Member"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    organisation = models.ForeignKey(
        "core.Organisation",
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="member",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "organisation")

    def __str__(self):
        return f"{self.user} → {self.organisation} ({self.role})"
    
class PublicationAttachment(models.Model):
    publication = models.ForeignKey(
        "core.Publication",
        on_delete=models.CASCADE,
        related_name="attachments",
    )
    file = models.FileField(upload_to="attachments/")
    display_name = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.display_name or self.file.name
class Subscription(models.Model):
    class Status(models.TextChoices):
        TRIALING = "trialing", "Trialing"
        ACTIVE = "active", "Active"
        CANCELED = "canceled", "Canceled"

    organisation = models.OneToOneField(
        "Organisation",
        on_delete=models.CASCADE,
        related_name="subscription",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.TRIALING,
    )

    trial_end = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)

    # On les met maintenant, même si on n'utilise pas Stripe tout de suite
    stripe_customer_id = models.CharField(max_length=255, null=True, blank=True)
    stripe_subscription_id = models.CharField(max_length=255, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.organisation.slug} - {self.status}"