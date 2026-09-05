from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status

from transactions.models import Transaction
from wallet.models import Employee
from .base import BaseAPITestCase, STRONG_PASSWORD

User = get_user_model()


class EmployeeListCreateTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.unattached_user = User.objects.create_user(
            username="fresh_employee", password=STRONG_PASSWORD, role="employee",
        )

    def test_admin_can_list_employees(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/v1/employees/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)

    def test_employee_cannot_list_employees(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.get("/api/v1/employees/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_cannot_list_employees(self):
        response = self.client.get("/api/v1/employees/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_can_create_employee_for_existing_user(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/v1/employees/",
            {"user": self.unattached_user.id, "employer": "Nouvelle Boîte"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Decimal(response.data["balance"]), Decimal("0.00"))
        self.assertTrue(Employee.objects.filter(user=self.unattached_user).exists())

    def test_non_admin_cannot_create_employee(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.post(
            "/api/v1/employees/",
            {"user": self.unattached_user.id, "employer": "Nouvelle Boîte"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_employee_for_already_attached_user_is_rejected(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/v1/employees/",
            {"user": self.employee_user.id, "employer": "Doublon SA"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_employee_unknown_user_is_rejected(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/v1/employees/",
            {"user": 999999, "employer": "Fantôme SA"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_employee_missing_employer_is_rejected(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/v1/employees/",
            {"user": self.unattached_user.id},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_employee_ignores_client_supplied_balance(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/v1/employees/",
            {"user": self.unattached_user.id, "employer": "Boîte", "balance": "9999.00"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Decimal(response.data["balance"]), Decimal("0.00"))


class EmployeeMeTests(BaseAPITestCase):
    def test_me_returns_own_employee_profile(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.get("/api/v1/employees/me/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.employee.id)

    def test_me_404_when_not_an_employee(self):
        self.client.force_authenticate(user=self.partner_user)
        response = self.client.get("/api/v1/employees/me/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_me_requires_authentication(self):
        response = self.client.get("/api/v1/employees/me/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class SingleEmployeeTests(BaseAPITestCase):
    def test_owner_can_view_own_employee(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.get(f"/api/v1/employees/{self.employee.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_other_employee_cannot_view(self):
        self.client.force_authenticate(user=self.other_employee_user)
        response = self.client.get(f"/api/v1/employees/{self.employee.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_view_any_employee(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(f"/api/v1/employees/{self.employee.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unknown_employee_is_404(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/v1/employees/999999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_owner_can_delete_own_employee(self):
        self.client.force_authenticate(user=self.other_employee_user)
        response = self.client.delete(f"/api/v1/employees/{self.other_employee.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Employee.objects.filter(id=self.other_employee.id).exists())

    def test_other_employee_cannot_delete(self):
        self.client.force_authenticate(user=self.other_employee_user)
        response = self.client.delete(f"/api/v1/employees/{self.employee.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_cannot_delete_employee_with_existing_transactions(self):
        # `Transaction.employee` est en `on_delete=PROTECT` : la suppression
        # doit échouer proprement (409), sans exception non gérée, et sans
        # supprimer le salarié.
        Transaction.objects.create(
            employee=self.employee, partner=self.partner, amount=Decimal("5.00")
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(f"/api/v1/employees/{self.employee.id}/")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertTrue(Employee.objects.filter(id=self.employee.id).exists())

    def test_put_not_allowed(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.put(f"/api/v1/employees/{self.employee.id}/", {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class EmployeeBalanceTests(BaseAPITestCase):
    def test_owner_can_view_own_balance(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.get(f"/api/v1/employees/{self.employee.id}/balance/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(response.data["balance"]), Decimal("100.00"))

    def test_other_employee_cannot_view_balance(self):
        self.client.force_authenticate(user=self.other_employee_user)
        response = self.client.get(f"/api/v1/employees/{self.employee.id}/balance/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_view_balance(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(f"/api/v1/employees/{self.employee.id}/balance/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unknown_employee_balance_is_404(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/v1/employees/999999/balance/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_can_credit_balance(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            f"/api/v1/employees/{self.employee.id}/balance/",
            {"amount": "25.50"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.balance, Decimal("125.50"))

    def test_owner_cannot_credit_own_balance(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.patch(
            f"/api/v1/employees/{self.employee.id}/balance/",
            {"amount": "25.50"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.balance, Decimal("100.00"))

    def test_partner_cannot_credit_balance(self):
        self.client.force_authenticate(user=self.partner_user)
        response = self.client.patch(
            f"/api/v1/employees/{self.employee.id}/balance/",
            {"amount": "25.50"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_credit_zero_amount_is_rejected(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            f"/api/v1/employees/{self.employee.id}/balance/",
            {"amount": "0.00"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_credit_negative_amount_is_rejected(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            f"/api/v1/employees/{self.employee.id}/balance/",
            {"amount": "-10.00"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_credit_missing_amount_is_rejected(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            f"/api/v1/employees/{self.employee.id}/balance/",
            {},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_credit_non_numeric_amount_is_rejected(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            f"/api/v1/employees/{self.employee.id}/balance/",
            {"amount": "not-a-number"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_credit_too_many_decimal_places_is_rejected(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            f"/api/v1/employees/{self.employee.id}/balance/",
            {"amount": "10.123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_credit_amount_exceeding_max_digits_is_rejected(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            f"/api/v1/employees/{self.employee.id}/balance/",
            {"amount": "123456789.00"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_credit_unknown_employee_is_404(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            "/api/v1/employees/999999/balance/",
            {"amount": "10.00"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_balance_endpoint_requires_authentication(self):
        response = self.client.get(f"/api/v1/employees/{self.employee.id}/balance/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
