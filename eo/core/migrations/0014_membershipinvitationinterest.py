from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0013_organisation_public_cover_image_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="MembershipInvitationInterest",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("click_count", models.PositiveIntegerField(default=0)),
                ("first_requested_at", models.DateTimeField(auto_now_add=True)),
                ("last_requested_at", models.DateTimeField(auto_now=True)),
                (
                    "last_requested_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="membership_invitation_interests",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "organisation",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="member_invitation_interest",
                        to="core.organisation",
                    ),
                ),
            ],
        ),
    ]
