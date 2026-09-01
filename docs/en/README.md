# Database Documentation — Survivor Pool

This documentation describes the **data model** of the Django backend, app by app.
Each file details the models, fields, relations, constraints and data lifecycle.

> 🇫🇷 Version française : [../fr/README.md](../fr/README.md)

## Contents

| App | Purpose | Documentation |
|---|---|---|
| `accounts` | Users and roles (authentication foundation) | [accounts.md](accounts.md) |
| `wallet` | Employees and their wallet balance | [wallet.md](wallet.md) |
| `partners` | Merchant partners and application review | [partners.md](partners.md) |
| `transactions` | Payment QR codes and transactions | [transactions.md](transactions.md) |
| `api` | HTTP exposure layer (no models) | [api.md](api.md) |
| — | Big picture, global schema, conventions | [overview.md](overview.md) |

## Business context

Survivor Pool is a digital meal-voucher platform:

1. An **employer** credits an **employee**'s wallet (`wallet.TopUp` → `wallet.Employee.balance`).
2. The employee generates a **QR code** for a given amount (`transactions.QRCode`).
3. A **partner** (merchant) scans that QR code, which creates a **transaction**
   (`transactions.Transaction`) and debits the employee's balance.
4. Partners are **approved** beforehand by an administrative agent
   (`partners.PartnerDecision`).

## Tech stack

- **Django 6.1** + **Django REST Framework 3.18**
- **Database**: SQLite in development (`backend/db.sqlite3`), PostgreSQL planned for
  production (`psycopg` and `dj-database-url` are already in `requirements.txt`)
- **Custom user model**: `AUTH_USER_MODEL = 'accounts.User'`

## Useful commands

```bash
cd backend

# Create migrations after changing a models.py
python manage.py makemigrations <app>

# Apply migrations
python manage.py migrate

# Show migration state
python manage.py showmigrations

# Show the SQL a migration generates
python manage.py sqlmigrate <app> 0001

# Check model consistency
python manage.py check

# Interactive shell with models loaded
python manage.py shell

# Enhanced shell (django-extensions is installed)
python manage.py shell_plus

# Inspect routes and generate a schema diagram
python manage.py show_urls
python manage.py graph_models -a -o ../docs/schema.png   # requires pygraphviz
```
