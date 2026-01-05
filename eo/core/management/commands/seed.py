from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Organisation, Publication, Membership

User = get_user_model()


class Command(BaseCommand):
    help = "Seed initial data for Éo"

    def handle(self, *args, **options):
        # USER
        user, created = User.objects.get_or_create(
            email="admin@eo.app",
            defaults={
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created:
            user.set_password("admin123")
            user.save()
            self.stdout.write(self.style.SUCCESS("✔ User created"))
        else:
            self.stdout.write("User already exists")

        # ORGANISATION
        organisation, created = Organisation.objects.get_or_create(
            nom="Organisation Démo",
            defaults={
                "ville": "Lisbonne",
                "pays": "Portugal",
                "email": "contact@organisation-demo.com",
            },
        )
        if created:
            self.stdout.write(self.style.SUCCESS("✔ Organisation created"))

        # MEMBERSHIP
        Membership.objects.get_or_create(
            user=user,
            organisation=organisation,
            defaults={"role": "owner"},
        )

        # PUBLICATIONS
        Publication.objects.get_or_create(
            titre="Bienvenue sur Éo",
            organisation=organisation,
            defaults={
                "contenu": "Première publication de démonstration.",
                "is_published": True,
            },
        )

        Publication.objects.get_or_create(
            titre="Deuxième publication",
            organisation=organisation,
            defaults={
                "contenu": "Une autre publication pour tester l’API.",
                "is_published": True,
            },
        )

        self.stdout.write(self.style.SUCCESS("🎉 Seed terminé avec succès"))