from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Lecture seule : l'admin Django ne doit pas offrir de moyen d'écrire une ligne
    en dehors de `audit.services.record_audit_event` (qui calcule le chaînage), ni de
    modifier/supprimer une ligne existante — la base l'interdit de toute façon au
    rôle applicatif restreint, mais autant ne pas le proposer dans l'UI."""

    list_display = ("occurred_at", "actor_role", "action", "target_type", "target_id")
    list_filter = ("actor_role", "action")
    search_fields = ("action", "target_type", "actor_role")
    ordering = ("-id",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
