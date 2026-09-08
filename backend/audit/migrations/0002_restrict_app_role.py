# Pose la garantie réelle exigée par le cabinet : « un REVOKE UPDATE, DELETE sur
# cette table suffit, et il tient dans votre script de migration ». Ce n'est PAS une
# vérification applicative — c'est un droit retiré au niveau du serveur Postgres, au
# rôle utilisé par le processus applicatif en service (`APP_DATABASE_URL`), distinct
# du rôle propriétaire (`DATABASE_URL`) qui exécute cette migration et garde, lui,
# tous les droits (nécessaire pour la démonstration d'altération du #127).
#
# No-op sur tout backend non-Postgres (SQLite en dev/CI sans base dédiée) : SQLite
# n'a pas de système de rôles, `REVOKE` n'y a pas de sens. C'est un choix assumé, pas
# un oubli — voir la doc du #107.

import os

from django.db import migrations

APP_ROLE = "cartepro_app"
AUDIT_TABLE = "audit_auditlog"


def restrict_app_role(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        print(f"[audit.0002] Backend non-Postgres ({schema_editor.connection.vendor}) : rien à faire.")
        return

    password = os.environ.get("AUDIT_APP_DB_PASSWORD")
    if not password:
        raise RuntimeError(
            "AUDIT_APP_DB_PASSWORD doit être défini pour créer/mettre à jour le rôle "
            "applicatif restreint sur Postgres."
        )

    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            f"""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '{APP_ROLE}') THEN
                    CREATE ROLE {APP_ROLE} LOGIN PASSWORD %s;
                ELSE
                    ALTER ROLE {APP_ROLE} PASSWORD %s;
                END IF;
            END
            $$;
            """,
            [password, password],
        )

        cursor.execute(f"GRANT CONNECT ON DATABASE {schema_editor.connection.settings_dict['NAME']} TO {APP_ROLE};")
        cursor.execute(f"GRANT USAGE ON SCHEMA public TO {APP_ROLE};")
        cursor.execute(f"GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO {APP_ROLE};")
        cursor.execute(f"GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO {APP_ROLE};")
        # Tables/séquences créées par de futures migrations : accès accordé par défaut.
        cursor.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO {APP_ROLE};")
        cursor.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON SEQUENCES TO {APP_ROLE};")

        # La restriction demandée : le rôle applicatif garde SELECT/INSERT sur le
        # journal d'audit, mais ne peut plus jamais le modifier ni le vider.
        # TRUNCATE est révoqué en plus d'UPDATE/DELETE : il vide la table tout aussi
        # efficacement qu'un DELETE et n'était pas couvert par défaut.
        cursor.execute(f"REVOKE UPDATE, DELETE, TRUNCATE ON {AUDIT_TABLE} FROM {APP_ROLE};")

    print(f"[audit.0002] Rôle {APP_ROLE} configuré, UPDATE/DELETE révoqués sur {AUDIT_TABLE}.")


def unrestrict_app_role(apps, schema_editor):
    """Réversibilité pour le confort de développement local uniquement — regrant et
    suppression du rôle. Ne reflète jamais un état à reproduire en déploiement réel."""
    if schema_editor.connection.vendor != "postgresql":
        return

    with schema_editor.connection.cursor() as cursor:
        cursor.execute(f"GRANT UPDATE, DELETE, TRUNCATE ON {AUDIT_TABLE} TO {APP_ROLE};")


class Migration(migrations.Migration):

    dependencies = [
        ("audit", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(restrict_app_role, unrestrict_app_role),
    ]
