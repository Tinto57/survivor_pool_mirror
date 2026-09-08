from django.test import TestCase

from audit.hashing import canonical_representation, compute_hash
from audit.models import AuditLog
from audit.services import record_audit_event


class HashingTestCase(TestCase):
    def test_same_fields_produce_same_hash(self):
        fields = {
            "occurred_at": "2026-09-08T10:00:00",
            "actor_id": 1,
            "actor_role": "admin",
            "action": "TEST",
            "target_type": "X",
            "target_id": 1,
            "payload": {"a": 1, "b": 2},
            "ip": "127.0.0.1",
            "prev_hash": "",
        }
        self.assertEqual(compute_hash(fields), compute_hash(dict(fields)))

    def test_payload_key_order_does_not_change_the_hash(self):
        base = {
            "occurred_at": "2026-09-08T10:00:00",
            "actor_id": 1,
            "actor_role": "admin",
            "action": "TEST",
            "target_type": "X",
            "target_id": 1,
            "ip": "127.0.0.1",
            "prev_hash": "",
        }
        h1 = compute_hash({**base, "payload": {"a": 1, "b": 2}})
        h2 = compute_hash({**base, "payload": {"b": 2, "a": 1}})
        self.assertEqual(h1, h2)

    def test_any_field_change_changes_the_hash(self):
        fields = {
            "occurred_at": "2026-09-08T10:00:00",
            "actor_id": 1,
            "actor_role": "admin",
            "action": "TEST",
            "target_type": "X",
            "target_id": 1,
            "payload": {},
            "ip": "127.0.0.1",
            "prev_hash": "",
        }
        original = compute_hash(fields)
        altered = compute_hash({**fields, "action": "TAMPERED"})
        self.assertNotEqual(original, altered)

    def test_hash_is_a_64_char_hex_digest(self):
        h = compute_hash({"occurred_at": "x", "action": "TEST"})
        self.assertEqual(len(h), 64)
        int(h, 16)  # ne lève pas si c'est bien de l'hexadécimal

    def test_none_fields_do_not_crash_the_canonical_representation(self):
        canonical_representation({"action": "TEST"})  # tous les autres champs absents


class RecordAuditEventTestCase(TestCase):
    def test_first_entry_has_no_prev_hash(self):
        entry = record_audit_event(actor_id=None, actor_role="", action="GENESIS")
        self.assertEqual(entry.prev_hash, "")
        self.assertTrue(entry.hash)

    def test_chain_links_consecutive_entries(self):
        first = record_audit_event(actor_id=1, actor_role="admin", action="A")
        second = record_audit_event(actor_id=1, actor_role="admin", action="B")
        third = record_audit_event(actor_id=1, actor_role="admin", action="C")

        self.assertEqual(second.prev_hash, first.hash)
        self.assertEqual(third.prev_hash, second.hash)

    def test_hash_matches_recomputation_from_stored_fields(self):
        entry = record_audit_event(
            actor_id=7, actor_role="partner", action="PARTNER_DECISION",
            target_type="Partner", target_id=3, payload={"decision": "accepted"},
            ip="10.0.0.1",
        )
        recomputed = compute_hash({
            "occurred_at": entry.occurred_at,
            "actor_id": entry.actor_id,
            "actor_role": entry.actor_role,
            "action": entry.action,
            "target_type": entry.target_type,
            "target_id": entry.target_id,
            "payload": entry.payload,
            "ip": entry.ip,
            "prev_hash": entry.prev_hash,
        })
        self.assertEqual(recomputed, entry.hash)

    def test_tampering_a_stored_field_breaks_hash_verification(self):
        """Sanity-check de bas niveau du principe de détection : modifier un champ en
        base (via update() SQL brut, en contournant `save()`) doit faire diverger le
        hash recalculé du hash stocké. La garantie réelle contre ce contournement est
        le REVOKE UPDATE/DELETE posé par `audit.0002` sur Postgres — non testable ici
        car ce test tourne sur la base de test (rôle propriétaire, sans restriction)."""
        entry = record_audit_event(actor_id=1, actor_role="admin", action="ORIGINAL")

        AuditLog.objects.filter(id=entry.id).update(action="TAMPERED")
        entry.refresh_from_db()

        recomputed = compute_hash({
            "occurred_at": entry.occurred_at,
            "actor_id": entry.actor_id,
            "actor_role": entry.actor_role,
            "action": entry.action,
            "target_type": entry.target_type,
            "target_id": entry.target_id,
            "payload": entry.payload,
            "ip": entry.ip,
            "prev_hash": entry.prev_hash,
        })
        self.assertNotEqual(recomputed, entry.hash)

    def test_events_are_ordered_by_id(self):
        record_audit_event(actor_id=1, actor_role="admin", action="A")
        record_audit_event(actor_id=1, actor_role="admin", action="B")

        actions = list(AuditLog.objects.values_list("action", flat=True))
        self.assertEqual(actions, ["A", "B"])
