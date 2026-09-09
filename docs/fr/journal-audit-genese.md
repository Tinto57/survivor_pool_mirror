# Journal d'audit — traitement des écritures antérieures (#121)

## Décision

Aucune écriture rétroactive. Le journal démarre à la migration `audit.0003`, qui
écrit une unique ligne de genèse (`action="AUDIT_LOG_GENESIS"`) avant toute autre
opération auditée.

## Justification

Le cabinet a été explicite : « Vous ne pouvez pas inventer des écritures
antérieures, ce serait exactement la fraude que le dispositif est censé rendre
visible. » Reconstruire après coup les décisions de partenaires, abondements et
migrations de la semaine passée produirait des horodatages fictifs — indiscernables,
pour un contrôleur, d'une falsification. Un enregistrement de genèse explicite est
au contraire honnête sur ce qu'il est : un point de départ, pas un historique
reconstitué.

## Ce qui n'est PAS couvert par le journal

Tout ce qui s'est passé avant le déploiement de `audit.0003` : validations de
partenaires, abondements, la migration de régularisation du découvert (#98), le
renommage des partenaires (#98/#104). Ces opérations restent tracées par les moyens
existants (tables métier, `PartnerDecision`, historique des transactions immuables)
mais pas par le journal d'audit chaîné.

## Comportement de la migration

`audit/migrations/0003_write_genesis_entry.py` : idempotente (une seule ligne de
genèse possible, vérifiée par filtre sur `action`), et chaîne correctement à la
dernière ligne existante si le journal contenait déjà des écritures au moment de son
exécution (cas qui ne devrait pas se produire en déploiement normal — les migrations
s'exécutent avant que le serveur applicatif ne commence à servir du trafic — mais
géré proprement si c'était le cas).
