from django.db import models
from django.utils import timezone


class AuditLog(models.Model):
    """Journal d'audit en ajout seul (#108).

    Aucune méthode de mise à jour ou de suppression n'est exposée ici : ce n'est pas
    une garantie applicative (elle serait contournable), c'est la migration
    `audit.0002_restrict_app_role` qui retire réellement les droits `UPDATE`/`DELETE`
    sur cette table au rôle Postgres applicatif restreint.

    `actor_id`/`actor_role` sont des colonnes à plat, pas des clés étrangères : une
    ligne d'audit ne doit jamais pouvoir être modifiée en cascade (ex. suppression
    d'un compte déclenchant un `SET_NULL`), ce qui casserait à la fois l'immuabilité
    de principe et, concrètement, échouerait contre le rôle restreint.
    """

    occurred_at = models.DateTimeField(default=timezone.now, editable=False)
    actor_id = models.BigIntegerField(null=True, blank=True)
    actor_role = models.CharField(max_length=32, blank=True)
    action = models.CharField(max_length=64)
    target_type = models.CharField(max_length=64, blank=True)
    target_id = models.BigIntegerField(null=True, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    prev_hash = models.CharField(max_length=64, blank=True)
    hash = models.CharField(max_length=64, unique=True, editable=False)

    class Meta:
        ordering = ["id"]
        verbose_name = "entrée d'audit"
        verbose_name_plural = "journal d'audit"

    def __str__(self):
        return f"{self.occurred_at:%Y-%m-%d %H:%M:%S} · {self.action} ({self.actor_role or 'système'})"
