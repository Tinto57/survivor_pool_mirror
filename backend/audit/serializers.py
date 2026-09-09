from rest_framework import serializers

from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    """Entrée du journal d'audit, telle qu'écrite par `audit.services.record_audit_event`."""

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "occurred_at",
            "actor_id",
            "actor_role",
            "action",
            "target_type",
            "target_id",
            "payload",
            "ip",
            "prev_hash",
            "hash",
        ]
        read_only_fields = list(fields)
