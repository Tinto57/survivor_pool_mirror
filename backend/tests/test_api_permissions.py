from decimal import Decimal

from django.core.cache import cache
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from partners.models import Category, Partner
from transactions.models import Transaction
from wallet.models import Employee

User = get_user_model()

STRONG_PASSWORD = "TicketTout-2026!"


class PermissionApiTests(APITestCase):
    def setUp(self):
        cache.clear()

        self.employee_user = User.objects.create_user(
            username="emp_one",
            password=STRONG_PASSWORD,
            role="employee",
        )
        self.employee = Employee.objects.create(
            user=self.employee_user,
            employer="Ministère",
            balance=Decimal("50.00"),
        )

        self.other_employee_user = User.objects.create_user(
            username="emp_two",
            password=STRONG_PASSWORD,
            role="employee",
        )
        self.other_employee = Employee.objects.create(
            user=self.other_employee_user,
            employer="Ministère",
            balance=Decimal("20.00"),
        )

        self.category = Category.objects.create(name="Restauration")
        self.partner_user = User.objects.create_user(
            username="partner_one",
            password=STRONG_PASSWORD,
            role="partner",
        )
        self.partner = Partner.objects.create(
            user=self.partner_user,
            business_name="Café A",
            siren="123456789",
            business_purpose="Café",
            address="1 rue Test",
            category=self.category,
            status="active",
        )

        self.other_partner_user = User.objects.create_user(
            username="partner_two",
            password=STRONG_PASSWORD,
            role="partner",
        )
        self.other_partner = Partner.objects.create(
            user=self.other_partner_user,
            business_name="Café B",
            siren="987654321",
            business_purpose="Café",
            address="2 rue Test",
            category=self.category,
            status="active",
        )

        self.admin = User.objects.create_user(
            username="admin_role",
            password=STRONG_PASSWORD,
            role="admin",
            is_staff=False,
        )
        self.staff_employee = User.objects.create_user(
            username="staff_employee",
            password=STRONG_PASSWORD,
            role="employee",
            is_staff=True,
        )

    def test_employee_cannot_list_users_or_employees(self):
        self.client.force_authenticate(user=self.employee_user)
        self.assertEqual(self.client.get("/api/v1/users/").status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.get("/api/v1/employees/").status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_role_without_is_staff_can_credit_and_export_csv(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            f"/api/v1/employees/{self.employee.id}/balance/",
            {"amount": "5.00"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.balance, Decimal("55.00"))

        csv_response = self.client.get("/api/v1/admin/transactions.csv/")
        self.assertEqual(csv_response.status_code, status.HTTP_200_OK)

    def test_is_staff_without_admin_role_cannot_credit(self):
        self.client.force_authenticate(user=self.staff_employee)
        response = self.client.patch(
            f"/api/v1/employees/{self.employee.id}/balance/",
            {"amount": "5.00"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_can_only_access_own_profile(self):
        self.client.force_authenticate(user=self.employee_user)
        own = self.client.get(f"/api/v1/users/{self.employee_user.id}/")
        other = self.client.get(f"/api/v1/users/{self.other_employee_user.id}/")
        self.assertEqual(own.status_code, status.HTTP_200_OK)
        self.assertEqual(other.status_code, status.HTTP_403_FORBIDDEN)

        patch_other = self.client.patch(
            f"/api/v1/users/{self.other_employee_user.id}/",
            {"first_name": "Hacker"},
            format="json",
        )
        self.assertEqual(patch_other.status_code, status.HTTP_403_FORBIDDEN)

    def test_partner_cannot_replay_another_partners_token(self):
        token = "shared-qr-token"
        tx = Transaction.objects.create(
            token=token,
            employee=self.employee,
            partner=self.partner,
            amount=Decimal("10.00"),
        )
        self.client.force_authenticate(user=self.other_partner_user)
        response = self.client.post(f"/api/v1/payments/{token}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Transaction.objects.filter(id=tx.id).count(), 1)

    def test_employee_cannot_confirm_payment(self):
        token = "emp-cannot-confirm"
        cache.set(
            f"PaymentIntent:{token}",
            {"token": token, "employee_id": self.employee.id},
            timeout=300,
        )
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.post(f"/api/v1/payments/{token}/", {"amount": "10.00"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_other_employee_cannot_read_payment_intent(self):
        token = "private-intent"
        cache.set(
            f"PaymentIntent:{token}",
            {"token": token, "employee_id": self.employee.id},
            timeout=300,
        )
        self.client.force_authenticate(user=self.other_employee_user)
        response = self.client.get(f"/api/v1/payments/{token}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_register_partner_gets_default_category(self):
        response = self.client.post(
            "/api/v1/users/",
            {
                "username": "new_partner",
                "password": STRONG_PASSWORD,
                "role": "partner",
                "partner": {
                    "business_name": "Boulangerie",
                    "siren": "111222333",
                    "business_purpose": "Pain",
                    "address": "3 rue Test",
                },
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = Partner.objects.get(user__username="new_partner")
        self.assertEqual(created.category.name, "Non catégorisé")
        self.assertEqual(created.status, "pending")
