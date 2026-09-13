from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0014_membershipinvitationinterest"),
    ]

    operations = [
        migrations.AddField(
            model_name="subscription",
            name="cancel_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="subscription",
            name="cancel_at_period_end",
            field=models.BooleanField(default=False),
        ),
    ]
