from rest_framework import status

from audit.services import record_audit_event
from .base import BaseAPITestCase


class AdminAuditLogViewTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.entries = [
            record_audit_event(
                actor_id=self.admin.id,
                actor_role="admin",
                action="PARTNER_DECISION",
                target_type="Partner",
                target_id=self.partner.id,
            ),
            record_audit_event(
                actor_id=self.employee_user.id,
                actor_role="employee",
                action="TRANSACTION_VALIDATED",
                target_type="Transaction",
                target_id=1,
            ),
            record_audit_event(
                actor_id=None,
                actor_role="",
                action="LOGIN_FAILED",
                target_type="User",
                target_id=self.employee_user.id,
            ),
        ]

    def test_admin_can_list_audit_log(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/v1/admin/audit/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 4)  # + la ligne de genèse (#121)

    def test_results_are_ordered_most_recent_first(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/v1/admin/audit/")
        ids = [row["id"] for row in response.data["results"]]
        self.assertEqual(ids, sorted(ids, reverse=True))

    def test_entry_exposes_chain_fields(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/v1/admin/audit/")
        row = response.data["results"][0]
        for field in ("id", "occurred_at", "actor_id", "actor_role", "action",
                       "target_type", "target_id", "payload", "ip", "prev_hash", "hash"):
            self.assertIn(field, row)

    def test_non_admin_cannot_list_audit_log(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.get("/api/v1/admin/audit/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_cannot_list_audit_log(self):
        response = self.client.get("/api/v1/admin/audit/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_filter_by_action(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/v1/admin/audit/?action=LOGIN_FAILED")
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["action"], "LOGIN_FAILED")

    def test_filter_by_actor_id(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(f"/api/v1/admin/audit/?actor_id={self.admin.id}")
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["action"], "PARTNER_DECISION")

    def test_filter_by_actor_role(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/v1/admin/audit/?actor_role=employee")
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["action"], "TRANSACTION_VALIDATED")

    def test_filter_by_target_type(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/v1/admin/audit/?target_type=User")
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["action"], "LOGIN_FAILED")

    def test_filter_by_start_excludes_earlier_records(self):
        # Passe par le dict du client de test (pas une f-string dans l'URL) pour que
        # le "+00:00" du décalage horaire soit correctement url-encodé — sinon
        # Django le décode en espace (convention application/x-www-form-urlencoded)
        # et parse_datetime échoue, comme le ferait un vrai "+" non encodé côté client.
        self.client.force_authenticate(user=self.admin)
        cutoff = self.entries[1].occurred_at.isoformat()
        response = self.client.get("/api/v1/admin/audit/", {"start": cutoff})
        actions = {row["action"] for row in response.data["results"]}
        self.assertEqual(actions, {"TRANSACTION_VALIDATED", "LOGIN_FAILED"})

    def test_filter_by_end_excludes_later_records(self):
        self.client.force_authenticate(user=self.admin)
        cutoff = self.entries[1].occurred_at.isoformat()
        response = self.client.get("/api/v1/admin/audit/", {"end": cutoff})
        actions = {row["action"] for row in response.data["results"]}
        self.assertEqual(actions, {"AUDIT_LOG_GENESIS", "PARTNER_DECISION", "TRANSACTION_VALIDATED"})

    def test_non_numeric_actor_id_is_rejected(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/v1/admin/audit/?actor_id=not-a-number")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_malformed_start_is_rejected(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/v1/admin/audit/?start=not-a-date")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_malformed_end_is_rejected(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/v1/admin/audit/?end=not-a-date")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unknown_action_filter_returns_empty(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/v1/admin/audit/?action=NOPE")
        self.assertEqual(response.data["count"], 0)
