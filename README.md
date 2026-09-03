<div align="center">

# 🎟️ Ticket Tout

**La carte pro qui permet aux salariés de dépenser leur budget avantages partout où le Ministère l'autorise.**
**The employee benefits card that lets you spend anywhere the Ministry allows.**

[![Next.js](https://img.shields.io/badge/Next.js-16-black?logo=next.js)](frontend)
[![Django](https://img.shields.io/badge/Django-6.1-092E20?logo=django&logoColor=white)](backend)
[![DRF](https://img.shields.io/badge/DRF-3.18-A30000?logo=django&logoColor=white)](backend)
[![JWT](https://img.shields.io/badge/Auth-JWT-black?logo=jsonwebtokens)](backend/accounts)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript&logoColor=white)](frontend)

[🇫🇷 Français](#-français) · [🇬🇧 English](#-english)

</div>

---

## 🇫🇷 Français

### Le projet

Sur mandat du **Ministère du Job et Bonheur**, Ticket Tout modernise le principe du
titre-restaurant : chaque salarié reçoit un budget crédité par son employeur, à dépenser
chez n'importe quel partenaire référencé — pas seulement pour manger.

Trois espaces, un seul compte :

| Espace | Ce qu'on y fait |
|---|---|
| 👤 **Salarié** | Consulter son solde, générer un QR code de paiement, historique, catalogue des partenaires |
| 🏪 **Partenaire** | Candidater, encaisser les paiements, suivre son tableau de bord financier |
| 🏛️ **Ministère (admin)** | Valider les partenaires, créditer les salariés, mettre en avant un « Coup de cœur du Ministre » |

### Stack technique

```
frontend/   Next.js 16 · React 19 · TypeScript · CSS Modules
backend/    Django 6.1 · Django REST Framework · SimpleJWT · SQLite (dev) / PostgreSQL (prod)
```

Authentification par JWT (access + refresh), rôle porté par `accounts.User.role`
(`employee` / `partner` / `admin`), CORS ouvert en développement.

### Démarrage rapide

```bash
# Backend — API Django sur :8000 (ensure that you have docker installed!)
docker compose up

# Frontend — Next.js sur :3000
cd frontend
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev
```

### Structure du dépôt

```
.
├── backend/            API Django (accounts, wallet, partners, transactions, api)
├── frontend/            App Next.js (espaces salarié, partenaire, admin)
└── docs/                Documentation du modèle de données, en français et en anglais
```

### Documentation

La base de données est entièrement documentée, app par app : modèles, champs,
relations, cycle de vie d'un paiement. 👉 [docs/](docs/README.md)

---

## 🇬🇧 English

### The project

Commissioned by the **Ministry of Job and Happiness**, Ticket Tout modernizes the
meal-voucher concept: every employee gets a budget funded by their employer, to spend
at any referenced partner — not just for lunch.

Three spaces, one account:

| Space | What happens there |
|---|---|
| 👤 **Employee** | Check balance, generate a payment QR code, transaction history, partner catalog |
| 🏪 **Partner** | Apply, cash in payments, track a financial dashboard |
| 🏛️ **Ministry (admin)** | Approve partners, credit employees, feature a "Minister's Pick" |

### Tech stack

```
frontend/   Next.js 16 · React 19 · TypeScript · CSS Modules
backend/    Django 6.1 · Django REST Framework · SimpleJWT · SQLite (dev) / PostgreSQL (prod)
```

JWT authentication (access + refresh), role carried by `accounts.User.role`
(`employee` / `partner` / `admin`), CORS open in development.

### Quick start

```bash
# Backend — Django API on :8000
cd backend
python -m venv ../venv && source ../venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

# Frontend — Next.js on :3000
cd frontend
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev
```

### Repository structure

```
.
├── backend/            Django API (accounts, wallet, partners, transactions, api)
├── frontend/            Next.js app (employee, partner and admin spaces)
└── docs/                Data model documentation, in French and English
```

### Documentation

The database is fully documented, app by app: models, fields, relations, payment
lifecycle. 👉 [docs/](docs/README.md)
