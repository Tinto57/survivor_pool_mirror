# Journal d'audit — fixtures de test (#122)

## Ce qui a été vérifié

Le `REVOKE UPDATE, DELETE, TRUNCATE` (#109) ne casse aucun test : la suite
(`manage.py test`) se connecte toujours via `DATABASE_URL` (rôle propriétaire),
jamais via `APP_DATABASE_URL` (rôle applicatif restreint) — voir
`docs/fr/journal-audit-postgres.md`. Le test runner Django doit de toute façon créer
et détruire la base de test, ce qu'un rôle restreint ne peut pas faire. Confirmé sur
Postgres réel pendant les fondations (#129) : 264 tests passants avec le REVOKE actif.
Aucun test du projet n'utilise `TransactionTestCase`/`TRUNCATE` entre deux tests —
l'isolation se fait par rollback de transaction, une opération que le rôle
propriétaire des tests effectue de toute façon.

**Conclusion sur le point précis soulevé par Thomas (le REVOKE casse les tests) :
non applicable ici**, par construction — pas parce que le risque n'existe pas en
général, mais parce que la suite de tests n'a jamais utilisé le rôle restreint.

## Ce qui a réellement cassé (et a été corrigé)

L'ajout de la migration de genèse (#121, `audit.0003`) fait qu'il existe désormais
**une ligne dans `audit_auditlog` dès la création de la base de test** — 3 tests
écrits avant cette migration supposaient une table vide et ont cassé :
- `test_events_are_ordered_by_id`
- `test_first_entry_has_no_prev_hash`
- `test_export_contains_every_record_in_order`

Corrigés en excluant explicitement `action="AUDIT_LOG_GENESIS"` (ou en comparant à la
genèse plutôt qu'à une chaîne vide) — pas en modifiant les fixtures partagées
(`tests/base.py`), qui ne touchent pas au journal d'audit.

## Recommandation pour la suite

Toute nouvelle instrumentation (#112-120, déjà faite) qui écrit un événement dans un
test doit s'attendre à ce que la ligne de genèse précède les siennes dans
`AuditLog.objects.order_by("id")` — filtrer ou n'assertionner que sur les événements
créés par le test lui-même, comme fait ici.
