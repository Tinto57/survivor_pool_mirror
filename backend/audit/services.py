"""Point d'entrée unique pour écrire une ligne d'audit (#111).

Toute instrumentation (comptes, décisions partenaires, transactions, connexions,
etc. — voir les issues dédiées à chaque type d'opération) doit appeler
`record_audit_event`, jamais `AuditLog.objects.create()` directement : c'est ici, et
uniquement ici, que le chaînage est calculé et que les écritures concurrentes sont
sérialisées.
"""

from django.db import connection, transaction
from django.utils import timezone

from .hashing import compute_hash
from .models import AuditLog

# Clé arbitraire mais stable pour le verrou consultatif Postgres qui sérialise les
# écritures : deux requêtes concurrentes ne doivent jamais lire le même "dernier
# hash" et produire deux lignes qui prétendent toutes les deux lui succéder.
_ADVISORY_LOCK_KEY = 0x41554449  # "AUDI" en ASCII, tient sur un int32 signé Postgres


@transaction.atomic
def record_audit_event(
    *,
    actor_id=None,
    actor_role="",
    action: str,
    target_type: str = "",
    target_id=None,
    payload: dict | None = None,
    ip: str | None = None,
) -> AuditLog:
    """Écrit une ligne d'audit chaînée à la précédente et la retourne.

    `actor_id`/`actor_role` : None/"" pour un événement système sans acteur humain
    (ex. genèse du journal).
    """
    if connection.vendor == "postgresql":
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_xact_lock(%s)", [_ADVISORY_LOCK_KEY])

    # Pas de select_for_update() ici : `SELECT ... FOR UPDATE` exige le privilège
    # UPDATE sous Postgres, précisément celui que le rôle applicatif restreint n'a
    # plus. Le verrou consultatif ci-dessus suffit à sérialiser les écritures — tout
    # appelant passe par cette fonction et attend son tour avant de lire "la dernière
    # ligne", donc une lecture simple derrière le verrou est déjà race-free.
    last = AuditLog.objects.order_by("-id").first()
    prev_hash = last.hash if last else ""

    fields = {
        "occurred_at": timezone.now(),
        "actor_id": actor_id,
        "actor_role": actor_role or "",
        "action": action,
        "target_type": target_type or "",
        "target_id": target_id,
        "payload": payload or {},
        "ip": ip,
        "prev_hash": prev_hash,
    }

    entry = AuditLog(hash=compute_hash(fields), **fields)
    entry.save()
    return entry
