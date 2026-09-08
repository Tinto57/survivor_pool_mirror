from decimal import Decimal

from rest_framework import status

from audit.models import AuditLog
from transactions.models import Transaction
from .base import BaseAPITestCase, STRONG_PASSWORD


class AccountCreatedAuditTestCase(BaseAPITestCase):
    def test_registration_writes_an_audit_entry(self):
        response = self.client.post(
            "/api/v1/users/",
            {
                "username": "nouveau_salarie",
                "password": "Un-Mot-De-Passe-Solide-2026!",
                "role": "employee",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        entry = AuditLog.objects.filter(action="ACCOUNT_CREATED").latest("id")
        self.assertEqual(entry.target_type, "User")
        self.assertEqual(entry.payload["username"], "nouveau_salarie")
        self.assertEqual(entry.payload["role"], "employee")


class AccountUpdatedAuditTestCase(BaseAPITestCase):
    def test_profile_update_writes_an_audit_entry_with_changed_fields(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.patch(
            f"/api/v1/users/{self.employee_user.id}/",
            {"first_name": "Nouveau Prénom"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        entry = AuditLog.objects.filter(action="ACCOUNT_UPDATED").latest("id")
        self.assertEqual(entry.target_id, self.employee_user.id)
        self.assertIn("first_name", entry.payload["changed_fields"])
        self.assertEqual(entry.payload["changed_fields"]["first_name"]["after"], "Nouveau Prénom")

    def test_update_without_changes_writes_nothing(self):
        self.client.force_authenticate(user=self.employee_user)
        before = AuditLog.objects.count()
        response = self.client.patch(
            f"/api/v1/users/{self.employee_user.id}/",
            {"first_name": self.employee_user.first_name},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(AuditLog.objects.count(), before)


class RoleChangedAuditTestCase(BaseAPITestCase):
    def test_admin_can_change_role_and_it_is_audited(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            f"/api/v1/users/{self.employee_user.id}/role/",
            {"role": "admin"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        entry = AuditLog.objects.filter(action="ROLE_CHANGED").latest("id")
        self.assertEqual(entry.target_id, self.employee_user.id)
        self.assertEqual(entry.payload, {"before": "employee", "after": "admin"})

    def test_non_admin_cannot_change_role(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.patch(
            f"/api/v1/users/{self.employee_user.id}/role/",
            {"role": "admin"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_setting_the_same_role_writes_nothing(self):
        self.client.force_authenticate(user=self.admin)
        before = AuditLog.objects.count()
        response = self.client.patch(
            f"/api/v1/users/{self.employee_user.id}/role/",
            {"role": "employee"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(AuditLog.objects.count(), before)


class PartnerDecisionAuditTestCase(BaseAPITestCase):
    def test_partner_acceptance_is_audited(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            f"/api/v1/partners/{self.pending_partner.id}/decision/",
            {"decision": "accepted"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        entry = AuditLog.objects.filter(action="PARTNER_DECISION").latest("id")
        self.assertEqual(entry.target_id, self.pending_partner.id)
        self.assertEqual(entry.payload["decision"], "accepted")


class BalanceTopupAuditTestCase(BaseAPITestCase):
    def test_topup_is_audited(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            f"/api/v1/employees/{self.employee.id}/balance/",
            {"amount": "25.00"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        entry = AuditLog.objects.filter(action="BALANCE_TOPUP").latest("id")
        self.assertEqual(entry.target_id, self.employee.id)
        self.assertEqual(entry.payload["amount"], "25.00")


class TransactionAuditTestCase(BaseAPITestCase):
    def _get_token(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.post("/api/v1/payments/")
        return response.data["token"]

    def test_validated_payment_is_audited(self):
        token = self._get_token()
        self.client.force_authenticate(user=self.partner_user)
        response = self.client.post(f"/api/v1/payments/{token}/", {"amount": "10.00"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        entry = AuditLog.objects.filter(action="TRANSACTION_VALIDATED").latest("id")
        self.assertEqual(entry.payload["amount"], "10.00")
        self.assertEqual(entry.target_type, "Transaction")

    def test_rejected_payment_is_audited(self):
        token = self._get_token()
        self.client.force_authenticate(user=self.partner_user)
        response = self.client.post(f"/api/v1/payments/{token}/", {"amount": "999999.00"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        entry = AuditLog.objects.filter(action="TRANSACTION_REJECTED").latest("id")
        self.assertEqual(entry.target_type, "Employee")
        self.assertEqual(entry.target_id, self.employee.id)
        self.assertEqual(entry.payload["reason"], "insufficient_balance")


class CounterEntryAuditTestCase(BaseAPITestCase):
    def test_counter_entry_is_audited_as_admin_action(self):
        tx = Transaction.objects.create(
            transaction_type=Transaction.ABONDMENT,
            employee=self.employee,
            amount=Decimal("15.00"),
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(f"/api/v1/transactions/{tx.id}/counter-entry/")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        entry = AuditLog.objects.filter(action="ADMIN_ACTION").latest("id")
        self.assertEqual(entry.payload["detail"], "COUNTER_ENTRY_CREATED")
        self.assertEqual(entry.payload["counter_entry_of"], tx.id)


class LoginFailedAuditTestCase(BaseAPITestCase):
    def test_wrong_password_is_audited(self):
        response = self.client.post(
            "/api/v1/auth/",
            {"username": self.employee_user.username, "password": "wrong-password"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        entry = AuditLog.objects.filter(action="LOGIN_FAILED").latest("id")
        self.assertEqual(entry.payload["username"], self.employee_user.username)
        self.assertIsNone(entry.actor_id)

    def test_correct_password_writes_no_login_failed_entry(self):
        response = self.client.post(
            "/api/v1/auth/",
            {"username": self.employee_user.username, "password": STRONG_PASSWORD},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(AuditLog.objects.filter(action="LOGIN_FAILED").exists())


class AuditChainAcrossOperationsTestCase(BaseAPITestCase):
    """La chaîne doit rester valide même quand des événements de types différents
    s'intercalent, produits par des vues différentes."""

    def test_chain_stays_linked_across_mixed_operations(self):
        self.client.force_authenticate(user=self.admin)
        self.client.post(
            f"/api/v1/partners/{self.pending_partner.id}/decision/",
            {"decision": "accepted"},
            format="json",
        )
        self.client.patch(
            f"/api/v1/employees/{self.employee.id}/balance/",
            {"amount": "5.00"},
            format="json",
        )

        entries = list(AuditLog.objects.order_by("id"))
        self.assertGreaterEqual(len(entries), 2)
        for previous, current in zip(entries, entries[1:]):
            self.assertEqual(current.prev_hash, previous.hash)
