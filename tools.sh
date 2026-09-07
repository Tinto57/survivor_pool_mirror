#!/usr/bin/env bash

set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

case "$1" in
  run)
    echo "==> Démarrage des conteneurs Docker..."
    docker compose up -d

    echo "==> Lancement du frontend en arrière-plan..."
    if [ -d "frontend" ]; then
      (cd frontend && npm run dev) &
      echo "Frontend démarré en arrière-plan."
    else
      echo "Dossier 'frontend' introuvable à la racine."
    fi
    ;;

  seed)
    echo "==> Exécution du seed..."
    if docker compose ps --services --filter "status=running" | grep -q "web"; then
      docker compose exec web python manage.py seed
    else
      (cd backend && python manage.py seed)
    fi
    ;;

  tests)
    echo "==> Démarrage de l'environnement (run)..."
    docker compose up -d

    echo "==> Exécution des tests d'audit..."
    docker compose exec web python manage.py test tests.test_audit_thomas
    ;;

  *)
    echo "Usage: $0 {run|seed|tests}"
    exit 1
    ;;
esac
