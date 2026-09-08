import json
import os
import tempfile

from django.core.management import call_command
from django.test import TestCase

from audit.services import record_audit_event
from audit.verify_export import canonical_json, verify_chain, verify_signature

HMAC_KEY = "test-hmac-key"


class ExportAuditLogTestCase(TestCase):
    def setUp(self):
        os.environ["AUDIT_EXPORT_HMAC_KEY"] = HMAC_KEY
        self.addCleanup(os.environ.pop, "AUDIT_EXPORT_HMAC_KEY", None)

        self.entries = [
            record_audit_event(actor_id=1, actor_role="admin", action=f"EVT_{i}", target_id=i)
            for i in range(3)
        ]

    def _export(self, **kwargs):
        fd, path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        self.addCleanup(os.remove, path)
        call_command("export_audit_log", output=path, **kwargs)
        with open(path, encoding="utf-8") as f:
            return json.load(f), path

    def test_export_contains_every_record_in_order(self):
        envelope, _ = self._export()
        actions = [r["action"] for r in envelope["records"]]
        self.assertEqual(actions, ["EVT_0", "EVT_1", "EVT_2"])
        self.assertEqual(envelope["count"], 3)

    def test_export_is_correctly_signed(self):
        envelope, _ = self._export()
        self.assertTrue(verify_signature(envelope, HMAC_KEY))

    def test_wrong_key_fails_signature_verification(self):
        envelope, _ = self._export()
        self.assertFalse(verify_signature(envelope, "wrong-key"))

    def test_start_filter_excludes_earlier_records(self):
        cutoff = self.entries[1].occurred_at.isoformat()
        envelope, _ = self._export(start=cutoff)
        actions = [r["action"] for r in envelope["records"]]
        self.assertEqual(actions, ["EVT_1", "EVT_2"])

    def test_intact_chain_has_no_verify_chain_issues(self):
        envelope, _ = self._export()
        self.assertEqual(verify_chain(envelope["records"]), [])


class VerifyChainTestCase(TestCase):
    """Teste `verify_chain` directement sur des enregistrements fabriqués, pour
    isoler la logique de détection de la commande d'export."""

    def _chain(self, n):
        return [
            record_audit_event(actor_id=1, actor_role="admin", action=f"EVT_{i}")
            for i in range(n)
        ]

    @staticmethod
    def _as_record(entry):
        return {
            "id": entry.id,
            "occurred_at": entry.occurred_at.isoformat(),
            "actor_id": entry.actor_id,
            "actor_role": entry.actor_role,
            "action": entry.action,
            "target_type": entry.target_type,
            "target_id": entry.target_id,
            "payload": entry.payload,
            "ip": entry.ip,
            "prev_hash": entry.prev_hash,
            "hash": entry.hash,
        }

    def test_modification_is_localized_to_the_altered_record(self):
        entries = self._chain(3)
        records = [self._as_record(e) for e in entries]
        records[1]["action"] = "TAMPERED"

        issues = verify_chain(records)

        self.assertEqual(len(issues), 1)
        self.assertIn(f"id={entries[1].id}", issues[0])
        self.assertIn("MODIFICATION", issues[0])

    def test_deletion_is_reported_as_a_gap_not_a_modification(self):
        entries = self._chain(3)
        records = [self._as_record(e) for e in entries]
        del records[1]  # simule une ligne supprimée puis absente de l'export

        issues = verify_chain(records)

        self.assertEqual(len(issues), 1)
        self.assertIn("SUPPRESSION", issues[0])
        self.assertNotIn("MODIFICATION", issues[0])

    def test_untampered_chain_has_no_issues(self):
        entries = self._chain(4)
        records = [self._as_record(e) for e in entries]
        self.assertEqual(verify_chain(records), [])


class CanonicalJsonTestCase(TestCase):
    def test_key_order_does_not_affect_output(self):
        self.assertEqual(
            canonical_json({"b": 2, "a": 1}),
            canonical_json({"a": 1, "b": 2}),
        )
