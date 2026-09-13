from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0016_notificationdispatch"),
    ]

    operations = [
        migrations.AlterField(
            model_name="notificationdispatch",
            name="provider",
            field=models.CharField(
                choices=[("internal", "Internal"), ("web_push", "Web Push")],
                default="internal",
                max_length=50,
            ),
        ),
        migrations.CreateModel(
            name="WebPushSubscription",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("endpoint", models.TextField()),
                ("p256dh", models.CharField(max_length=512)),
                ("auth", models.CharField(max_length=255)),
                ("user_agent", models.CharField(blank=True, max_length=500)),
                ("active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("organisation", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="web_push_subscriptions", to="core.organisation")),
            ],
            options={"ordering": ("-updated_at",)},
        ),
        migrations.AddConstraint(
            model_name="webpushsubscription",
            constraint=models.UniqueConstraint(fields=("organisation", "endpoint"), name="unique_web_push_endpoint_per_organisation"),
        ),
    ]
