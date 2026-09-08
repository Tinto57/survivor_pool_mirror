#!/usr/bin/env python3
"""Vérification hors ligne de l'intégrité d'un export du journal d'audit (#125).

« Si votre vérification a besoin de se connecter à la base, elle ne vaut rien » —
ce script ne dépend ni de Django (pas de `django.setup()`), ni d'une connexion base
de données : uniquement le fichier exporté (`export_audit_log`, #124) et la clé HMAC.
Il importe `audit.hashing`, qui est lui-même dépourvu de toute dépendance Django.

Deux vérifications distinctes, rapportées séparément :
- la signature HMAC de l'export protège contre une altération du FICHIER après
  l'export (intégrité du transport) ;
- la chaîne SHA-256 embarquée dans chaque enregistrement protège contre une
  altération de la BASE avant l'export (intégrité des données elles-mêmes) — c'est
  elle qui détecte, et localise précisément, une modification ou une suppression.

Usage :
    python verify_export.py --file export.json [--key <clé>]
    (la clé peut aussi venir de $AUDIT_EXPORT_HMAC_KEY)

Code de sortie : 0 si conforme, 1 si une anomalie est détectée, 2 en cas d'erreur
d'usage (fichier illisible, clé manquante).
"""

import argparse
import hashlib
import hmac
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from audit.hashing import compute_hash  # noqa: E402


def canonical_json(data: dict) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")


def verify_signature(envelope: dict, key: str) -> bool:
    signature = envelope.get("hmac_sha256")
    if not signature:
        return False
    payload = {k: v for k, v in envelope.items() if k != "hmac_sha256"}
    expected = hmac.new(key.encode("utf-8"), canonical_json(payload), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def verify_chain(records: list) -> list[str]:
    """Anomalies détectées, précisément localisées. Liste vide = chaîne conforme."""
    issues = []
    self_ok = {}

    for record in records:
        fields = {
            "occurred_at": record["occurred_at"],
            "actor_id": record["actor_id"],
            "actor_role": record["actor_role"],
            "action": record["action"],
            "target_type": record["target_type"],
            "target_id": record["target_id"],
            "payload": record["payload"],
            "ip": record["ip"],
            "prev_hash": record["prev_hash"],
        }
        recomputed = compute_hash(fields)
        ok = recomputed == record["hash"]
        self_ok[record["id"]] = ok
        if not ok:
            issues.append(
                f"MODIFICATION détectée : enregistrement id={record['id']} "
                f"(action={record['action']!r}) — hash stocké {record['hash'][:12]}… "
                f"≠ hash recalculé {recomputed[:12]}…"
            )

    for previous, current in zip(records, records[1:]):
        if current["prev_hash"] != previous["hash"] and self_ok.get(previous["id"], True):
            # Le précédent n'est lui-même pas altéré (sinon l'anomalie ci-dessus
            # suffit déjà à le désigner) : le lien casse parce qu'un ou plusieurs
            # enregistrements manquent entre les deux — signature d'une suppression.
            issues.append(
                f"SUPPRESSION probable : rupture de chaîne entre id={previous['id']} "
                f"(hash {previous['hash'][:12]}…) et id={current['id']} "
                f"(prev_hash attendu {current['prev_hash'][:12]}…) — un ou plusieurs "
                f"enregistrements manquent entre les deux."
            )

    return issues


def main():
    parser = argparse.ArgumentParser(description="Vérifie l'intégrité d'un export du journal d'audit CartePro.")
    parser.add_argument("--file", required=True, help="Fichier JSON exporté (export_audit_log).")
    parser.add_argument("--key", help="Clé HMAC. Sinon lue depuis $AUDIT_EXPORT_HMAC_KEY.")
    args = parser.parse_args()

    key = args.key or os.environ.get("AUDIT_EXPORT_HMAC_KEY")
    if not key:
        print("Clé HMAC manquante (--key ou $AUDIT_EXPORT_HMAC_KEY).", file=sys.stderr)
        sys.exit(2)

    try:
        with open(args.file, encoding="utf-8") as f:
            envelope = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Impossible de lire {args.file} : {exc}", file=sys.stderr)
        sys.exit(2)

    signature_ok = verify_signature(envelope, key)
    print(f"Signature du fichier exporté : {'CONFORME' if signature_ok else 'NON CONFORME'}")

    records = envelope.get("records", [])
    issues = verify_chain(records)
    if issues:
        print(f"Chaîne d'intégrité : NON CONFORME ({len(issues)} anomalie(s))")
        for issue in issues:
            print(f"  · {issue}")
    else:
        print(f"Chaîne d'intégrité : CONFORME ({len(records)} enregistrement(s))")

    verdict_ok = signature_ok and not issues
    print(f"\nVERDICT : {'CONFORME' if verdict_ok else 'NON CONFORME'}")
    sys.exit(0 if verdict_ok else 1)


if __name__ == "__main__":
    main()
