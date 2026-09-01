# Documentation de la base de données — Survivor Pool

> 🇬🇧 English version: [../en/README.md](../en/README.md)

Cette documentation décrit le **modèle de données** du backend Django, app par app.
Chaque fichier détaille les modèles, les champs, les relations, les contraintes et le
cycle de vie des données.

## Sommaire

| App | Rôle | Documentation |
|---|---|---|
| `accounts` | Utilisateurs et rôles (socle d'authentification) | [accounts.md](accounts.md) |
| `wallet` | Salariés et solde de leur porte-monnaie | [wallet.md](wallet.md) |
| `partners` | Commerçants partenaires et validation de leur dossier | [partners.md](partners.md) |
| `transactions` | QR codes de paiement et transactions | [transactions.md](transactions.md) |
| `api` | Couche d'exposition HTTP (aucun modèle) | [api.md](api.md) |
| — | Vue d'ensemble, schéma global, conventions | [overview.md](overview.md) |

## Contexte fonctionnel

Survivor Pool est une plateforme de type « titres-restaurant dématérialisés » :

1. Un **employeur** crédite le porte-monnaie d'un **salarié** (`wallet.TopUp` → `wallet.Employee.balance`).
2. Le salarié génère un **QR code** d'un certain montant (`transactions.QRCode`).
3. Un **partenaire** (commerçant) scanne ce QR code, ce qui crée une **transaction**
   (`transactions.Transaction`) et débite le solde du salarié.
4. Les partenaires sont préalablement **validés** par un agent administrateur
   (`partners.PartnerDecision`).

## Stack technique

- **Django 6.1** + **Django REST Framework 3.18**
- **Base de données** : SQLite en développement (`backend/db.sqlite3`), PostgreSQL prévu
  en production (`psycopg` et `dj-database-url` sont déjà dans `requirements.txt`)
- **Modèle utilisateur personnalisé** : `AUTH_USER_MODEL = 'accounts.User'`

## Commandes utiles

```bash
cd backend

# Créer les migrations après modification d'un models.py
python manage.py makemigrations <app>

# Appliquer les migrations
python manage.py migrate

# Voir l'état des migrations
python manage.py showmigrations

# Voir le SQL généré par une migration
python manage.py sqlmigrate <app> 0001

# Vérifier la cohérence des modèles
python manage.py check

# Shell interactif avec les modèles chargés
python manage.py shell

# Shell enrichi (django-extensions est installé)
python manage.py shell_plus

# Afficher tous les modèles et leurs champs
python manage.py show_urls
python manage.py graph_models -a -o ../docs/schema.png   # nécessite pygraphviz
```
