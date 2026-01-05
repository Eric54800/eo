# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

# évite import circulaire : on n'importe Organisation que typiquement dans serializers/views
# si besoin, utiliser settings.AUTH_USER_MODEL côté relations inverses

class User(AbstractUser):
    """
    Utilisateur personnalisé.
    """

    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=30, blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)

    date_created = models.DateTimeField(default=timezone.now)

    ROLE_CHOICES = [
        ("owner", "Owner"),
        ("admin", "Admin"),
        ("user", "User"),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="user")

    organisation = models.ForeignKey(
        "core.Organisation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.email

    # --- Helpers Éo ---

    @property
    def current_membership(self):
        return self.memberships.first()

    @property
    def current_organisation(self):
        membership = self.current_membership
        return membership.organisation if membership else None

    @property
    def current_role(self):
        membership = self.current_membership
        return membership.role if membership else None

    @property
    def is_owner(self):
        return self.current_role == "owner"

    @property
    def is_admin(self):
        return self.current_role in ["owner", "admin"]