from django.test import TestCase

from audit.models import AuditLog
from audit.services import record_audit_event


class AuditGenesisTestCase(TestCase):
    def test_genesis_entry_exists_after_migrations(self):
        self.assertEqual(AuditLog.objects.filter(action="AUDIT_LOG_GENESIS").count(), 1)

    def test_genesis_entry_has_no_prev_hash(self):
        genesis = AuditLog.objects.get(action="AUDIT_LOG_GENESIS")
        self.assertEqual(genesis.prev_hash, "")

    def test_genesis_is_first_in_chain(self):
        genesis = AuditLog.objects.order_by("id").first()
        self.assertEqual(genesis.action, "AUDIT_LOG_GENESIS")

    def test_subsequent_entries_chain_from_genesis(self):
        genesis = AuditLog.objects.get(action="AUDIT_LOG_GENESIS")
        entry = record_audit_event(actor_id=1, actor_role="admin", action="SOME_EVENT")
        self.assertEqual(entry.prev_hash, genesis.hash)
