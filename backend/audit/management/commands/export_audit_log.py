"""Export JSON signé HMAC-SHA256 d'une période du journal d'audit (#124).

Le contrôleur doit pouvoir vérifier l'intégrité de cet export sans accéder à la
base — voir `audit/verify_export.py` (#125), qui ne dépend que de ce fichier et de
la clé.
"""

import hashlib
import hmac
import json
import os
from datetime import datetime, timezone as dt_timezone

from django.core.management.base import BaseCommand, CommandError
from django.utils.dateparse import parse_datetime

from audit.models import AuditLog


def canonical_json(data: dict) -> bytes:
    """Sérialisation stable : mêmes clés, même ordre, mêmes séparateurs, à chaque
    appel — condition nécessaire pour qu'une signature HMAC soit reproductible."""
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")


class Command(BaseCommand):
    help = "Exporte le journal d'audit (période donnée) en JSON signé HMAC-SHA256, vérifiable hors ligne."

    def add_arguments(self, parser):
        parser.add_argument("--start", help="ISO 8601, borne inférieure incluse sur occurred_at.")
        parser.add_argument("--end", help="ISO 8601, borne supérieure incluse sur occurred_at.")
        parser.add_argument("--output", required=True, help="Chemin du fichier JSON à écrire.")

    def handle(self, *args, **options):
        key = os.environ.get("AUDIT_EXPORT_HMAC_KEY")
        if not key:
            raise CommandError("AUDIT_EXPORT_HMAC_KEY doit être défini dans l'environnement.")

        queryset = AuditLog.objects.order_by("id")

        if options["start"]:
            start = parse_datetime(options["start"])
            if start is None:
                raise CommandError("--start invalide, attendu au format ISO 8601.")
            queryset = queryset.filter(occurred_at__gte=start)

        if options["end"]:
            end = parse_datetime(options["end"])
            if end is None:
                raise CommandError("--end invalide, attendu au format ISO 8601.")
            queryset = queryset.filter(occurred_at__lte=end)

        records = [
            {
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
            for entry in queryset
        ]

        # Condensé de la chaîne pour la période exportée : indépendant du contenu du
        # fichier au-delà des hash eux-mêmes, sert de résumé rapide à comparer.
        chain_digest = hashlib.sha256(
            "\x1f".join(r["hash"] for r in records).encode("utf-8")
        ).hexdigest()

        envelope = {
            "generated_at": datetime.now(dt_timezone.utc).isoformat(),
            "period": {"start": options["start"], "end": options["end"]},
            "count": len(records),
            "chain_digest": chain_digest,
            "records": records,
        }

        # Signature calculée AVANT d'ajouter le champ hmac_sha256 lui-même : le
        # vérificateur devra retirer ce champ et reproduire exactement cette étape.
        signature = hmac.new(key.encode("utf-8"), canonical_json(envelope), hashlib.sha256).hexdigest()
        envelope["hmac_sha256"] = signature

        with open(options["output"], "w", encoding="utf-8") as f:
            json.dump(envelope, f, indent=2, ensure_ascii=False)
            f.write("\n")

        self.stdout.write(self.style.SUCCESS(
            f"Export écrit : {options['output']} "
            f"({len(records)} enregistrement(s), signature {signature[:12]}…)"
        ))
