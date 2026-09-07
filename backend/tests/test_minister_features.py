from decimal import Decimal

from django.core.cache import cache
from django.db import IntegrityError, transaction
from rest_framework import status

from partners.models import MinisterSpotlight
from wallet.models import Employee

from .base import BaseAPITestCase


class OverdraftTestCase(BaseAPITestCase):
    """Le solde salarié peut descendre jusqu'à -150€, jamais en-deçà."""

    def setUp(self):
        super().setUp()
        cache.clear()
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.post("/api/v1/payments/", format="json")
        self.token = response.data["token"]

    def _confirm(self, amount):
        self.client.force_authenticate(user=self.partner_user)
        return self.client.post(
            f"/api/v1/payments/{self.token}/", {"amount": amount}, format="json"
        )

    def test_payment_can_push_balance_into_overdraft(self):
        # self.employee a un solde de 100.00 ; on paie 200.00 -> -100.00, dans la limite.
        response = self._confirm("200.00")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.balance, Decimal("-100.00"))

    def test_payment_can_reach_overdraft_limit_exactly(self):
        # 100.00 - 250.00 = -150.00, exactement la limite : doit passer.
        response = self._confirm("250.00")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.balance, Decimal("-150.00"))

    def test_payment_beyond_overdraft_limit_is_rejected(self):
        # 100.00 - 250.01 = -150.01, au-delà de la limite : doit être refusé.
        response = self._confirm("250.01")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.balance, Decimal("100.00"))

    def test_model_constraint_rejects_balance_below_limit(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.employee.balance = Decimal("-150.01")
                self.employee.save()

    def test_abondment_regularizes_overdraft(self):
        self.employee.balance = Decimal("-80.00")
        self.employee.save(update_fields=["balance"])

        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/v1/transactions/abondments/",
            {"employee": self.employee.id, "amount": "30.00"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.balance, Decimal("-50.00"))


class OverdraftTotalTestCase(BaseAPITestCase):
    def test_admin_sees_total_advanced(self):
        self.employee.balance = Decimal("-40.00")
        self.employee.save(update_fields=["balance"])
        self.other_employee.balance = Decimal("-10.00")
        self.other_employee.save(update_fields=["balance"])

        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/v1/employees/decouvert-total/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(response.data["total_advanced"]), Decimal("50.00"))

    def test_employee_cannot_see_total_advanced(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.get("/api/v1/employees/decouvert-total/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class MinisterSpotlightTestCase(BaseAPITestCase):
    def test_public_can_read_active_spotlight_without_auth(self):
        MinisterSpotlight.objects.create(
            partner=self.partner, message="Un café qui a du cœur.", is_active=True
        )
        response = self.client.get("/api/v1/ministre/coup-de-coeur/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["partner"]["id"], self.partner.id)

    def test_public_read_without_active_spotlight_is_no_content(self):
        response = self.client.get("/api/v1/ministre/coup-de-coeur/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_public_list_shows_all_entries_without_click_count(self):
        MinisterSpotlight.objects.create(
            partner=self.partner, message="Actif.", is_active=True, click_count=42
        )
        MinisterSpotlight.objects.create(
            partner=self.other_partner, message="Archivé.", is_active=False, click_count=9
        )
        response = self.client.get("/api/v1/ministre/coup-de-coeur/toutes/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        self.assertNotIn("click_count", response.data["results"][0])

    def test_public_click_increments_counter_without_auth(self):
        spotlight = MinisterSpotlight.objects.create(
            partner=self.partner, message="Un café qui a du cœur.", is_active=True
        )
        response = self.client.post("/api/v1/ministre/coup-de-coeur/click/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        spotlight.refresh_from_db()
        self.assertEqual(spotlight.click_count, 1)

    def test_click_without_active_spotlight_is_not_found(self):
        response = self.client.post("/api/v1/ministre/coup-de-coeur/click/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_publish_deactivates_previous_active(self):
        old = MinisterSpotlight.objects.create(
            partner=self.partner, message="Ancien.", is_active=True
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/v1/ministre/coup-de-coeur/historique/",
            {"partner": self.other_partner.id, "message": "Nouveau coup de cœur."},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        old.refresh_from_db()
        self.assertFalse(old.is_active)

    def test_employee_cannot_publish_spotlight(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.post(
            "/api/v1/ministre/coup-de-coeur/historique/",
            {"partner": self.partner.id, "message": "Nouveau coup de cœur."},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_republish_reactivates_without_resetting_clicks(self):
        old = MinisterSpotlight.objects.create(
            partner=self.partner, message="Ancien.", is_active=False, click_count=7
        )
        current = MinisterSpotlight.objects.create(
            partner=self.other_partner, message="Actuel.", is_active=True
        )

        self.client.force_authenticate(user=self.admin)
        response = self.client.post(f"/api/v1/ministre/coup-de-coeur/{old.id}/republier/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        old.refresh_from_db()
        current.refresh_from_db()
        self.assertTrue(old.is_active)
        self.assertEqual(old.click_count, 7)
        self.assertFalse(current.is_active)
