"""Calcul du chaînage d'intégrité SHA-256 du journal d'audit (#110).

Ordre documenté des champs concaténés, exigé par le cabinet : chaque enregistrement
porte le SHA-256 de l'enregistrement précédent. Le PK auto-incrémenté (`id`) n'entre
volontairement PAS dans le calcul : le hash d'une ligne doit être connu avant son
INSERT (pour être écrit dans la même requête — voir `audit/services.py`), or `id`
n'est attribué qu'au moment de l'insertion sur un `BigAutoField`. L'intégrité ne perd
rien à son absence : `occurred_at` + `prev_hash` suffisent à garantir l'ordre et
l'unicité de la position dans la chaîne.

Les champs sont séparés par le caractère ASCII "unit separator" (0x1F), qui n'apparaît
jamais dans un JSON sérialisé ni dans les valeurs métier attendues ici — contrairement
à des séparateurs comme "|" ou ",", il ne peut pas être produit accidentellement par
une valeur de champ et créer une ambiguïté de concaténation.
"""

import hashlib
import json

CHAIN_FIELD_ORDER = (
    "occurred_at",
    "actor_id",
    "actor_role",
    "action",
    "target_type",
    "target_id",
    "payload",
    "ip",
    "prev_hash",
)

_SEPARATOR = "\x1f"


def canonical_representation(fields: dict) -> str:
    """Représentation textuelle stable et déterministe d'un enregistrement, dans
    `CHAIN_FIELD_ORDER`. Deux appels avec des valeurs équivalentes produisent
    toujours exactement la même chaîne."""
    parts = []
    for name in CHAIN_FIELD_ORDER:
        value = fields.get(name)
        if value is None:
            parts.append("")
        elif name == "occurred_at":
            parts.append(value.isoformat() if hasattr(value, "isoformat") else str(value))
        elif name == "payload":
            parts.append(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str))
        else:
            parts.append(str(value))
    return _SEPARATOR.join(parts)


def compute_hash(fields: dict) -> str:
    """SHA-256 hexadécimal (64 caractères) de la représentation canonique."""
    return hashlib.sha256(canonical_representation(fields).encode("utf-8")).hexdigest()
