from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from wallet.models import Employee
from partners.models import Category, Partner

User = get_user_model()

DEMO_PASSWORD = "TicketTout2026!"


class Command(BaseCommand):
    """Crée un compte de démonstration par type d'utilisateur (salarié, partenaire, admin).

    Idempotent : peut être relancée à chaque déploiement sans dupliquer les comptes.
    """

    help = "Crée les comptes de démonstration Ticket Tout (salarié, partenaire, admin)."

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

        category, _ = Category.objects.get_or_create(name="Restauration")

        partner_user, created = self._get_or_create_user(
            username="partenaire.demo",
            defaults={
                "first_name": "Camille",
                "last_name": "Partenaire",
                "email": "partenaire.demo@ticket-tout.gouv.fr",
                "role": "partner",
            },
        )
        Partner.objects.get_or_create(
            user=partner_user,
            defaults={
                "status": "active",
                "business_name": "Café du Ministère",
                "siren": "123456789",
                "business_purpose": "Restauration rapide et salon de thé.",
                "category": category,
                "address": "1 place Vendôme, 75001 Paris",
                "is_featured": True,
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
