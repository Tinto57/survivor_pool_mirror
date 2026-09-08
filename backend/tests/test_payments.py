from decimal import Decimal

from django.core.cache import cache
from rest_framework import status

from transactions.models import Transaction
from .base import BaseAPITestCase


class PaymentIntentCreateTests(BaseAPITestCase):
    def test_employee_can_create_intent_without_amount(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.post("/api/v1/payments/")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("token", response.data)
        self.assertEqual(response.data["expires_in"], 300)
        self.assertNotIn("amount", response.data)

    def test_created_intent_is_stored_without_amount(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.post("/api/v1/payments/")
        token = response.data["token"]
        payload = cache.get(f"PaymentIntent:{token}")
        self.assertIsNotNone(payload)
        self.assertEqual(payload["employee_id"], self.employee.id)
        self.assertNotIn("amount", payload)

    def test_employee_can_create_intent_even_with_zero_balance(self):
        # Le montant n'étant plus fixé à la création, le solde du salarié
        # n'a plus à être vérifié à cette étape.
        self.employee.balance = Decimal("0.00")
        self.employee.save(update_fields=["balance"])
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.post("/api/v1/payments/")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_partner_cannot_create_intent(self):
        self.client.force_authenticate(user=self.partner_user)
        response = self.client.post("/api/v1/payments/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_cannot_create_intent(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post("/api/v1/payments/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_cannot_create_intent(self):
        response = self.client.post("/api/v1/payments/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_body_is_ignored_on_create(self):
        # Même si un client envoie encore un montant (ancien comportement),
        # il est totalement ignoré désormais.
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.post("/api/v1/payments/", {"amount": "999.00"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        token = response.data["token"]
        payload = cache.get(f"PaymentIntent:{token}")
        self.assertNotIn("amount", payload)

    def test_two_intents_from_same_employee_get_different_tokens(self):
        self.client.force_authenticate(user=self.employee_user)
        first = self.client.post("/api/v1/payments/")
        second = self.client.post("/api/v1/payments/")
        self.assertNotEqual(first.data["token"], second.data["token"])


class PaymentIntentInspectTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.token = "inspect-token"
        cache.set(
            f"PaymentIntent:{self.token}",
            {"token": self.token, "employee_id": self.employee.id},
            timeout=300,
        )

    def test_creator_employee_can_inspect(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.get(f"/api/v1/payments/{self.token}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["token"], self.token)
        self.assertNotIn("amount", response.data)

    def test_other_employee_cannot_inspect(self):
        self.client.force_authenticate(user=self.other_employee_user)
        response = self.client.get(f"/api/v1/payments/{self.token}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_active_partner_can_inspect(self):
        self.client.force_authenticate(user=self.partner_user)
        response = self.client.get(f"/api/v1/payments/{self.token}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_pending_partner_cannot_inspect(self):
        self.client.force_authenticate(user=self.pending_partner_user)
        response = self.client.get(f"/api/v1/payments/{self.token}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_suspended_partner_cannot_inspect(self):
        self.client.force_authenticate(user=self.suspended_partner_user)
        response = self.client.get(f"/api/v1/payments/{self.token}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_inspect(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(f"/api/v1/payments/{self.token}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_anonymous_cannot_inspect(self):
        response = self.client.get(f"/api/v1/payments/{self.token}/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unknown_token_is_404(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/v1/payments/does-not-exist/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_expired_token_is_404(self):
        cache.delete(f"PaymentIntent:{self.token}")
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.get(f"/api/v1/payments/{self.token}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class PaymentIntentConfirmTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.token = "confirm-token"
        cache.set(
            f"PaymentIntent:{self.token}",
            {"token": self.token, "employee_id": self.employee.id},
            timeout=300,
        )

    def _confirm(self, user, amount=None, token=None):
        self.client.force_authenticate(user=user)
        body = {} if amount is None else {"amount": amount}
        return self.client.post(f"/api/v1/payments/{token or self.token}/", body, format="json")

    def test_active_partner_sets_amount_and_confirms(self):
        response = self._confirm(self.partner_user, amount="42.50")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(response.data["amount"]), Decimal("42.50"))
        self.assertEqual(response.data["partner"], self.partner.id)
        self.assertEqual(response.data["employee"], self.employee.id)

        self.employee.refresh_from_db()
        self.assertEqual(self.employee.balance, Decimal("57.50"))

        tx = Transaction.objects.get(token=self.token)
        self.assertEqual(tx.amount, Decimal("42.50"))
        self.assertEqual(tx.partner_id, self.partner.id)

    def test_confirm_consumes_the_cache_entry(self):
        self._confirm(self.partner_user, amount="10.00")
        self.assertIsNone(cache.get(f"PaymentIntent:{self.token}"))

    def test_confirm_missing_amount_is_rejected(self):
        response = self._confirm(self.partner_user, amount=None)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.balance, Decimal("100.00"))
        self.assertIsNotNone(cache.get(f"PaymentIntent:{self.token}"))

    def test_confirm_zero_amount_is_rejected(self):
        response = self._confirm(self.partner_user, amount="0.00")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_confirm_negative_amount_is_rejected(self):
        response = self._confirm(self.partner_user, amount="-5.00")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_confirm_non_numeric_amount_is_rejected(self):
        response = self._confirm(self.partner_user, amount="free-lunch")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_confirm_too_many_decimal_places_is_rejected(self):
        response = self._confirm(self.partner_user, amount="10.999")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_confirm_amount_exceeding_balance_is_rejected(self):
        response = self._confirm(self.partner_user, amount="1000.00")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.balance, Decimal("100.00"))
        self.assertFalse(Transaction.objects.filter(token=self.token).exists())
        # Le token n'est pas consommé par un échec : le partenaire peut réessayer.
        self.assertIsNotNone(cache.get(f"PaymentIntent:{self.token}"))

    def test_confirm_amount_equal_to_balance_succeeds(self):
        response = self._confirm(self.partner_user, amount="100.00")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.balance, Decimal("0.00"))

    def test_employee_cannot_confirm_own_intent(self):
        response = self._confirm(self.employee_user, amount="10.00")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_cannot_confirm(self):
        response = self._confirm(self.admin, amount="10.00")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_pending_partner_cannot_confirm(self):
        response = self._confirm(self.pending_partner_user, amount="10.00")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_suspended_partner_cannot_confirm(self):
        response = self._confirm(self.suspended_partner_user, amount="10.00")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_cannot_confirm(self):
        response = self.client.post(f"/api/v1/payments/{self.token}/", {"amount": "10.00"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_confirm_unknown_token_is_404(self):
        response = self._confirm(self.partner_user, amount="10.00", token="ghost-token")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_confirm_expired_token_is_404(self):
        cache.delete(f"PaymentIntent:{self.token}")
        response = self._confirm(self.partner_user, amount="10.00")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_replay_by_same_partner_returns_same_transaction_without_double_debit(self):
        first = self._confirm(self.partner_user, amount="30.00")
        self.assertEqual(first.status_code, status.HTTP_200_OK)

        second = self._confirm(self.partner_user, amount="30.00")
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertEqual(first.data["id"], second.data["id"])

        self.employee.refresh_from_db()
        self.assertEqual(self.employee.balance, Decimal("70.00"))
        self.assertEqual(Transaction.objects.filter(token=self.token).count(), 1)

    def test_replay_ignores_a_different_amount_in_the_body(self):
        first = self._confirm(self.partner_user, amount="30.00")
        second = self._confirm(self.partner_user, amount="999.00")
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(second.data["amount"]), Decimal("30.00"))

    def test_replay_by_a_different_partner_is_not_found(self):
        first = self._confirm(self.partner_user, amount="30.00")
        self.assertEqual(first.status_code, status.HTTP_200_OK)

        second = self._confirm(self.other_partner_user, amount="30.00")
        self.assertEqual(second.status_code, status.HTTP_404_NOT_FOUND)

        self.employee.refresh_from_db()
        self.assertEqual(self.employee.balance, Decimal("70.00"))
        self.assertEqual(Transaction.objects.filter(token=self.token).count(), 1)

    def test_full_round_trip_employee_creates_partner_sets_amount(self):
        self.client.force_authenticate(user=self.employee_user)
        create_response = self.client.post("/api/v1/payments/")
        token = create_response.data["token"]

        self.client.force_authenticate(user=self.partner_user)
        inspect_response = self.client.get(f"/api/v1/payments/{token}/")
        self.assertEqual(inspect_response.status_code, status.HTTP_200_OK)

        confirm_response = self.client.post(
            f"/api/v1/payments/{token}/", {"amount": "17.00"}, format="json"
        )
        self.assertEqual(confirm_response.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(confirm_response.data["amount"]), Decimal("17.00"))

        self.employee.refresh_from_db()
        self.assertEqual(self.employee.balance, Decimal("83.00"))
