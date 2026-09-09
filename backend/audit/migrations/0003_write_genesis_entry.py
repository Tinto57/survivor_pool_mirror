# Point 2 de la demande du cabinet (08/09) : « Le journal démarre aujourd'hui,
# votre base a une semaine [...] Vous ne pouvez pas inventer des écritures
# antérieures [...] Vous pouvez en revanche écrire un enregistrement d'origine qui
# dit ce qu'il est. » Décision documentée dans docs/fr/journal-audit-genese.md.

from django.db import migrations
from django.utils import timezone

from audit.hashing import compute_hash

GENESIS_ACTION = "AUDIT_LOG_GENESIS"

GENESIS_MESSAGE = (
    "Démarrage du journal d'audit. Aucune opération antérieure à cette ligne "
    "(partenaires déjà validés, abondements déjà réalisés, migrations déjà "
    "exécutées la semaine passée) n'est couverte par ce dispositif — les "
    "reconstruire rétroactivement serait exactement la fraude que ce journal est "
    "censé rendre visible. Voir docs/fr/journal-audit-genese.md."
)


def write_genesis_entry(apps, schema_editor):
    AuditLog = apps.get_model('audit', 'AuditLog')

    # Idempotent : ne jamais écrire une seconde genèse, quelle que soit la raison
    # pour laquelle cette migration serait rejouée.
    if AuditLog.objects.filter(action=GENESIS_ACTION).exists():
        return

    last = AuditLog.objects.order_by("-id").first()
    prev_hash = last.hash if last else ""

    fields = {
        "occurred_at": timezone.now(),
        "actor_id": None,
        "actor_role": "",
        "action": GENESIS_ACTION,
        "target_type": "",
        "target_id": None,
        "payload": {"message": GENESIS_MESSAGE},
        "ip": None,
        "prev_hash": prev_hash,
    }
    AuditLog.objects.create(hash=compute_hash(fields), **fields)


class Migration(migrations.Migration):

    dependencies = [
        ('audit', '0002_restrict_app_role'),
    ]

    operations = [
        migrations.RunPython(write_genesis_entry, migrations.RunPython.noop),
    ]
