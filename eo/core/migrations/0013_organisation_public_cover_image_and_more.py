from django.db import migrations, models


def copy_existing_public_image(apps, schema_editor):
    Organisation = apps.get_model("core", "Organisation")

    for organisation in Organisation.objects.exclude(public_image="").exclude(public_image__isnull=True):
        image_name = organisation.public_image.name
        if not organisation.public_cover_image:
            organisation.public_cover_image = image_name
        if not organisation.public_avatar_image:
            organisation.public_avatar_image = image_name
        organisation.save(update_fields=["public_cover_image", "public_avatar_image"])


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0012_organisation_horaires_organisationpublicdocument"),
    ]

    operations = [
        migrations.AddField(
            model_name="organisation",
            name="cover_position_x",
            field=models.PositiveSmallIntegerField(default=50),
        ),
        migrations.AddField(
            model_name="organisation",
            name="cover_position_y",
            field=models.PositiveSmallIntegerField(default=50),
        ),
        migrations.AddField(
            model_name="organisation",
            name="public_avatar_image",
            field=models.ImageField(blank=True, null=True, upload_to="org_public/avatars/"),
        ),
        migrations.AddField(
            model_name="organisation",
            name="public_cover_image",
            field=models.ImageField(blank=True, null=True, upload_to="org_public/covers/"),
        ),
        migrations.RunPython(copy_existing_public_image, migrations.RunPython.noop),
    ]
