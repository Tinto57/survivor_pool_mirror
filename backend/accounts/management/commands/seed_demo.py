from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from wallet.models import Employee
from partners.models import Category, Partner

User = get_user_model()

DEMO_PASSWORD = "CartePro2026!"


class Command(BaseCommand):
    """Crée un compte de démonstration par type d'utilisateur (salarié, partenaire, admin).

    Idempotent : peut être relancée à chaque déploiement sans dupliquer les comptes.
    """

    help = "Crée les comptes de démonstration CartePro (salarié, partenaire, admin)."

    def handle(self, *args, **options):
        employee_user, created = self._get_or_create_user(
            username="salarie.demo",
            defaults={
                "first_name": "Camille",
                "last_name": "Salarié",
                "email": "salarie.demo@ticket-tout.gouv.fr",
                "role": "employee",
            },
        )
        Employee.objects.get_or_create(
            user=employee_user,
            defaults={"employer": "Ministère du Job et Bonheur", "balance": 132.50},
        )
        self._report("Salarié", employee_user.username, created)

        # Au moins 5 partenaires fictifs référencés (cahier des charges §4, livrable
        # semaine 1). Seul le premier ("partenaire.demo") sert de compte de connexion
        # de démonstration ; les autres n'existent que pour peupler le catalogue.
        demo_partners = [
            {
                "username": "partenaire.demo",
                "business_name": "Café du Ministère",
                "category": "Restauration",
                "siren": "123456789",
                "business_purpose": "Restauration rapide et salon de thé.",
                "address": "1 place Vendôme, 75001 Paris",
                "is_featured": True,
            },
            {
                "username": "partenaire.demo2",
                "business_name": "Librairie des Ministères",
                "category": "Culture",
                "siren": "223456789",
                "business_purpose": "Librairie généraliste et papeterie.",
                "address": "12 rue de Rivoli, 75004 Paris",
            },
            {
                "username": "partenaire.demo3",
                "business_name": "Pharmacie Bonaparte",
                "category": "Santé",
                "siren": "323456789",
                "business_purpose": "Pharmacie de quartier et parapharmacie.",
                "address": "8 rue Bonaparte, 75006 Paris",
            },
            {
                "username": "partenaire.demo4",
                "business_name": "Épicerie du Marché",
                "category": "Alimentation",
                "siren": "423456789",
                "business_purpose": "Épicerie fine et produits locaux.",
                "address": "15 rue Montorgueil, 75001 Paris",
            },
            {
                "username": "partenaire.demo5",
                "business_name": "Sport Nation",
                "category": "Sport",
                "siren": "523456789",
                "business_purpose": "Équipements et vêtements de sport.",
                "address": "3 place de la Nation, 75011 Paris",
            },
        ]

        for entry in demo_partners:
            category, _ = Category.objects.get_or_create(name=entry["category"])

            partner_user, created = self._get_or_create_user(
                username=entry["username"],
                defaults={
                    "first_name": "Camille",
                    "last_name": "Partenaire",
                    "email": f"{entry['username']}@ticket-tout.gouv.fr",
                    "role": "partner",
                },
            )
            Partner.objects.get_or_create(
                user=partner_user,
                defaults={
                    "status": "active",
                    "business_name": entry["business_name"],
                    "siren": entry["siren"],
                    "business_purpose": entry["business_purpose"],
                    "category": category,
                    "address": entry["address"],
                    "is_featured": entry.get("is_featured", False),
                },
            )
            self._report("Partenaire", partner_user.username, created)

        admin_user, created = self._get_or_create_user(
            username="admin.demo",
            defaults={
                "first_name": "Camille",
                "last_name": "Admin",
                "email": "admin.demo@ticket-tout.gouv.fr",
                "role": "admin",
                "is_staff": True,
            },
        )
        self._report("Admin", admin_user.username, created)

        self.stdout.write(self.style.SUCCESS(f"Mot de passe commun aux 3 comptes : {DEMO_PASSWORD}"))

    def _get_or_create_user(self, username, defaults):
        user, created = User.objects.get_or_create(username=username, defaults=defaults)
        if created:
            user.set_password(DEMO_PASSWORD)
            user.save()
        return user, created

    def _report(self, label, username, created):
        state = "créé" if created else "déjà présent"
        self.stdout.write(f"{label} : {username} ({state})")
