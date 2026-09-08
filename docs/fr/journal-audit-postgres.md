# Journal d'audit — infrastructure Postgres (fondations #107-#111)

## Pourquoi Postgres

Le déploiement actuel (Render) tourne par défaut en SQLite (`DATABASE_URL` non
défini). SQLite n'a pas de système de rôles/permissions — impossible d'y faire un
`REVOKE UPDATE, DELETE` exigé pour le journal d'audit. Django continue de retomber
sur SQLite en l'absence de `DATABASE_URL`/`APP_DATABASE_URL` (dev courant), mais le
journal d'audit lui-même (migration `audit.0002`) ne s'active que sur Postgres — sur
SQLite, elle ne fait rien et l'affiche clairement.

## Deux rôles, un seul schéma

| Rôle | Variable d'env | Utilisé par | Droits sur `audit_auditlog` |
|---|---|---|---|
| Propriétaire | `DATABASE_URL` | `manage.py migrate` (DDL, création du rôle applicatif, GRANT/REVOKE) | Tous (nécessaire pour la démo d'altération, #127) |
| Applicatif restreint | `APP_DATABASE_URL` (si définie, prend le pas sur `DATABASE_URL` pour le serveur en service) | `gunicorn`/`runserver` en fonctionnement normal | `SELECT`, `INSERT` uniquement — `UPDATE`, `DELETE`, `TRUNCATE` révoqués |

Le rôle applicatif restreint garde tous ses droits normaux sur les autres tables
(`GRANT ALL ... IN SCHEMA public`, avec `ALTER DEFAULT PRIVILEGES` pour couvrir les
tables créées par de futures migrations) — seule la table d'audit est verrouillée en
écriture/suppression.

## Utilisation locale (Docker)

```bash
cp .env.example .env   # renseigner POSTGRES_PASSWORD, AUDIT_APP_DB_PASSWORD
docker compose up -d db
docker compose up web  # exécute manage.py migrate puis runserver, avec DATABASE_URL (rôle propriétaire)
```

Pour lancer le serveur **avec le rôle restreint** (pour tester/démontrer le
comportement réel, cf. #127) : décommenter `APP_DATABASE_URL` dans `.env`, puis
relancer `docker compose up web` — les migrations continuent de s'exécuter avec
`DATABASE_URL` (le `command` du service ne change pas), seul le serveur applicatif
bascule sur le rôle restreint.

## Tests

Les tests (`manage.py test`) utilisent toujours `DATABASE_URL` (rôle propriétaire),
jamais `APP_DATABASE_URL` : le test runner Django a besoin de créer/détruire la base
de test, ce qu'un rôle restreint ne peut de toute façon pas faire. Le `REVOKE` ne
gêne donc pas la suite de tests standard — #122 (réparation des fixtures) ne devrait
se poser que si un test est délibérément exécuté contre le rôle restreint.

## Vérifié manuellement (voir aussi les tests `tests/test_audit_foundations.py`)

Sur une instance Postgres locale (`docker compose`) :
- `manage.py migrate` avec `DATABASE_URL` crée le rôle `cartepro_app`, révoque
  `UPDATE`/`DELETE`/`TRUNCATE` sur `audit_auditlog`.
- Avec `APP_DATABASE_URL` pointant sur ce rôle : `record_audit_event()` écrit
  normalement (SELECT + INSERT), un `UPDATE`/`DELETE`/`TRUNCATE` direct sur la table
  échoue avec `permission denied`.
- Avec `DATABASE_URL` (rôle propriétaire) : un `UPDATE` direct en `psql` réussit —
  c'est le geste attendu pour la démo d'altération du #127.
- Le hash recalculé de la ligne modifiée diverge du hash stocké ; les autres lignes
  restent correctement chaînées.

## Ce qui reste à faire (hors fondations)

Provisionner une vraie base Postgres sur Render (`databases:` dans `render.yaml`,
non fait ici faute d'accès au dashboard Render), et y exécuter cette même migration
une première fois pour créer le rôle applicatif en conditions réelles.
