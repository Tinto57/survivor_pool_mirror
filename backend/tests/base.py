from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APITestCase

from partners.models import Category, Partner
from wallet.models import Employee

User = get_user_model()

STRONG_PASSWORD = "TicketTout-2026!"


class BaseAPITestCase(APITestCase):
    """Fixture commune à toute la suite : admin, salariés et partenaires
    (actifs, en attente, suspendu) déjà en base, prêts à être authentifiés
    avec `force_authenticate`."""

    def setUp(self):
        cache.clear()

        self.admin = User.objects.create_user(
            username="admin_user",
            password=STRONG_PASSWORD,
            role="admin",
        )

        self.employee_user = User.objects.create_user(
            username="employee_one",
            password=STRONG_PASSWORD,
            role="employee",
        )
        self.employee = Employee.objects.create(
            user=self.employee_user,
            employer="ACME",
            balance=Decimal("100.00"),
        )

        self.other_employee_user = User.objects.create_user(
            username="employee_two",
            password=STRONG_PASSWORD,
            role="employee",
        )
        self.other_employee = Employee.objects.create(
            user=self.other_employee_user,
            employer="ACME",
            balance=Decimal("10.00"),
        )

        self.category = Category.objects.create(name="Restauration")
        self.other_category = Category.objects.create(name="Mobilité")

        self.partner_user = User.objects.create_user(
            username="partner_active",
            password=STRONG_PASSWORD,
            role="partner",
        )
        self.partner = Partner.objects.create(
            user=self.partner_user,
            business_name="Café Actif",
            siren="111111111",
            business_purpose="Café",
            address="1 rue Test",
            category=self.category,
            status="active",
        )

        self.other_partner_user = User.objects.create_user(
            username="partner_active_two",
            password=STRONG_PASSWORD,
            role="partner",
        )
        self.other_partner = Partner.objects.create(
            user=self.other_partner_user,
            business_name="Café Actif 2",
            siren="222222222",
            business_purpose="Café",
            address="2 rue Test",
            category=self.category,
            status="active",
        )

        self.pending_partner_user = User.objects.create_user(
            username="partner_pending",
            password=STRONG_PASSWORD,
            role="partner",
        )
        self.pending_partner = Partner.objects.create(
            user=self.pending_partner_user,
            business_name="Café En Attente",
            siren="333333333",
            business_purpose="Café",
            address="3 rue Test",
            category=self.category,
            status="pending",
        )

        self.suspended_partner_user = User.objects.create_user(
            username="partner_suspended",
            password=STRONG_PASSWORD,
            role="partner",
        )
        self.suspended_partner = Partner.objects.create(
            user=self.suspended_partner_user,
            business_name="Café Suspendu",
            siren="444444444",
            business_purpose="Café",
            address="4 rue Test",
            category=self.category,
            status="suspended",
        )
