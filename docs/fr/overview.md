# Vue d'ensemble de la base de données

> 🇬🇧 English version: [../en/overview.md](../en/overview.md)

## Schéma relationnel global

```
┌──────────────────────────────────────────────────────────────────────┐
│                        accounts.User  (AUTH_USER_MODEL)              │
│  id · username · password · email · first_name · last_name           │
│  role (employee | partner | admin) · is_staff · is_superuser · ...   │
└──┬──────────────┬───────────────┬───────────────┬────────────────┬───┘
   │ 1—1          │ 1—1           │ 1—N           │ 1—N            │ 1—N
   │              │               │ (agent)       │ (created_by)   │ (cancelled_by)
   ▼              ▼               ▼               ▼                ▼
┌──────────┐  ┌───────────┐  ┌──────────────┐  ┌─────────┐  ┌───────────────┐
│ wallet.  │  │ partners. │  │ partners.    │  │ wallet. │  │ transactions. │
│ Employee │  │ Partner   │◄─┤PartnerDecision│  │ TopUp   │  │ Transaction   │
│          │  │           │ N│              │  │         │  │               │
│ employer │  │business_  │  │ decision     │  │ amount  │  │ amount        │
│ balance  │  │  name     │  │ reason       │  │         │  │ is_cancelled  │
└──┬───┬───┘  │ siren     │  └──────────────┘  └────┬────┘  └───┬───────┬───┘
   │   │      │ status    │                         │           │       │
   │   │      │ lat/lng   │◄────────────────────────┼───────────┘       │
   │   │      └───────────┘        N—1 (partner)    │ N—1 (user)        │
   │   │                                            │                   │
   │   └────────────────────────────────────────────┘                   │
   │                  N—1 (employee)                                    │
   │                                                                    │
   │ 1—N                                                                │
   ▼                                                                    │
┌──────────────────────┐                                                │
│ transactions.QRCode  │◄───────────────────────────────────────────────┘
│ token · amount       │                 1—1 (qr_code)
│ expires_at · is_used │
└──────────────────────┘
```

## Récapitulatif des tables

| Table SQL | Modèle | App | Rôle |
|---|---|---|---|
| `accounts_user` | `User` | accounts | Compte de connexion, porte le rôle métier |
| `wallet_employee` | `Employee` | wallet | Profil salarié + solde |
| `wallet_topup` | `TopUp` | wallet | Historique des créditations |
| `partners_partner` | `Partner` | partners | Fiche commerçant |
| `partners_partnerdecision` | `PartnerDecision` | partners | Journal des décisions d'agrément |
| `transactions_qrcode` | `QRCode` | transactions | Jeton de paiement éphémère |
| `transactions_transaction` | `Transaction` | transactions | Paiement effectué |

## Récapitulatif des relations

| Depuis | Champ | Vers | Type | `on_delete` | Effet |
|---|---|---|---|---|---|
| `wallet.Employee` | `user` | `accounts.User` | OneToOne | `CASCADE` | Supprimer le user supprime le profil salarié |
| `wallet.TopUp` | `user` | `wallet.Employee` | OneToOne ⚠️ | `CASCADE` | Voir la remarque dans [wallet.md](wallet.md) |
| `wallet.TopUp` | `created_by` | `accounts.User` | ForeignKey | `SET_NULL` | L'historique survit à la suppression de l'admin |
| `partners.Partner` | `user` | `accounts.User` | OneToOne | `CASCADE` | Supprimer le user supprime la fiche partenaire |
| `partners.PartnerDecision` | `partner` | `partners.Partner` | ForeignKey | `CASCADE` | Les décisions disparaissent avec le partenaire |
| `partners.PartnerDecision` | `agent` | `accounts.User` | ForeignKey | `SET_NULL` | La décision reste, l'agent devient `NULL` |
| `transactions.QRCode` | `employee` | `wallet.Employee` | ForeignKey | `CASCADE` | Les QR codes suivent le salarié |
| `transactions.Transaction` | `qr_code` | `transactions.QRCode` | OneToOne | `PROTECT` | Un QR consommé ne peut plus être supprimé |
| `transactions.Transaction` | `employee` | `wallet.Employee` | ForeignKey | `PROTECT` | Protège l'intégrité comptable |
| `transactions.Transaction` | `partner` | `partners.Partner` | ForeignKey | `PROTECT` | Protège l'intégrité comptable |
| `transactions.Transaction` | `cancelled_by` | `accounts.User` | ForeignKey | `SET_NULL` | Trace d'annulation conservée |

### Lecture des stratégies `on_delete`

- **`CASCADE`** — utilisé pour les données de *profil* : elles n'ont aucun sens sans leur
  utilisateur, elles sont donc supprimées avec lui.
- **`PROTECT`** — utilisé pour les données *comptables* : Django lève une
  `ProtectedError` et refuse la suppression, ce qui garantit qu'une transaction ne peut
  jamais devenir orpheline.
- **`SET_NULL`** — utilisé pour les champs d'*audit* (« qui a fait quoi ») : on veut
  garder la ligne d'historique même si l'agent quitte l'entreprise.

## Cycle de vie d'un paiement

```
1. TopUp créé par un admin        →  Employee.balance augmente
2. Salarié demande un QR          →  QRCode(token, amount, expires_at = now + 30min, is_used = False)
3. Partenaire scanne le token     →  vérification : is_used == False ET is_expired() == False
4. Validation                     →  Transaction créée
                                     QRCode.is_used = True
                                     Employee.balance -= amount
5. (optionnel) Annulation         →  is_cancelled = True, cancelled_at, cancelled_by, raison
                                     Employee.balance += amount
```

> ⚠️ Les étapes 4 et 5 modifient plusieurs tables : elles doivent impérativement être
> exécutées dans une `transaction.atomic()` avec un `select_for_update()` sur
> l'`Employee` pour éviter les doubles dépenses en cas de scan simultané.

## Conventions du projet

- **Un modèle = une responsabilité.** Les modèles restent volontairement fins ; la
  logique métier (débit, validation de QR) n'est pas encore implémentée.
- **Références par chaîne** (`'accounts.User'`, `'wallet.Employee'`) plutôt que par
  import direct : cela évite les imports circulaires entre apps.
- **Montants** : toujours `DecimalField(max_digits=10, decimal_places=2)`, jamais
  `FloatField` — les arrondis flottants sont interdits sur de la monnaie.
  Maximum représentable : `99 999 999,99 €`.
- **Dates de création** : `DateTimeField(auto_now_add=True)`, non modifiable.
- **Choix** : constantes `*_CHOICES` déclarées en tête de classe.
- **Libellés** : les valeurs stockées en base sont en anglais, les libellés affichés
  sont en français.

## Points d'amélioration identifiés

Ces points ne sont pas des blocages mais méritent d'être traités avant la mise en
production. Le détail est donné dans la documentation de chaque app.

| # | App | Sujet |
|---|---|---|
| 1 | wallet | `TopUp.user` est un `OneToOneField` : un salarié ne peut être crédité qu'une seule fois |
| 2 | wallet | `TopUp.__str__` référence `self.employee`, champ inexistant → `AttributeError` |
| 3 | accounts | `role` n'a ni `default` ni `blank=False` explicite : un `createsuperuser` produit un rôle vide |
| 4 | partners | `siren` n'est pas `unique=True` |
| 5 | transactions | Aucun index sur `QRCode.is_used` / `expires_at`, ni sur les dates de transaction |
| 6 | global | Aucun `Meta` (ni `ordering`, ni `verbose_name`, ni `constraints`) |
| 7 | global | Aucune contrainte de positivité sur les montants (`amount > 0`, `balance >= 0`) |
| 8 | global | Aucun `admin.site.register()` : les modèles sont invisibles dans l'admin Django |

## Configuration base de données

Actuellement (`backend/config/settings.py`) :

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

`dj-database-url` et `psycopg` sont déjà installés : le passage à PostgreSQL se fera en
remplaçant ce bloc par une lecture de la variable d'environnement `DATABASE_URL`.

> ⚠️ `db.sqlite3` est actuellement suivi par Git. Une base de données ne devrait pas être
> versionnée : il faut l'ajouter au `.gitignore`.
