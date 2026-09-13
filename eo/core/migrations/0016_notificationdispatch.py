from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0015_subscription_cancel_schedule"),
    ]

    operations = [
        migrations.CreateModel(
            name="NotificationDispatch",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("event_type", models.CharField(choices=[("publication_published", "Publication published")], max_length=50)),
                ("topic", models.CharField(max_length=255)),
                ("title", models.CharField(max_length=255)),
                ("body", models.TextField()),
                ("payload", models.JSONField(blank=True, default=dict)),
                ("provider", models.CharField(choices=[("internal", "Internal")], default="internal", max_length=50)),
                ("status", models.CharField(choices=[("recorded", "Recorded"), ("sent", "Sent"), ("failed", "Failed")], default="recorded", max_length=20)),
                ("external_message_id", models.CharField(blank=True, max_length=255)),
                ("last_error", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("delivered_at", models.DateTimeField(blank=True, null=True)),
                ("organisation", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notification_dispatches", to="core.organisation")),
                ("publication", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="notification_dispatches", to="core.publication")),
            ],
            options={
                "ordering": ("-created_at",),
            },
        ),
    ]
