# Database overview

> 🇫🇷 Version française : [../fr/overview.md](../fr/overview.md)

## Global relational schema

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

## Table summary

| SQL table | Model | App | Purpose |
|---|---|---|---|
| `accounts_user` | `User` | accounts | Login account, carries the business role |
| `wallet_employee` | `Employee` | wallet | Employee profile + balance |
| `wallet_topup` | `TopUp` | wallet | Credit history |
| `partners_partner` | `Partner` | partners | Merchant record |
| `partners_partnerdecision` | `PartnerDecision` | partners | Approval decision log |
| `transactions_qrcode` | `QRCode` | transactions | Short-lived payment token |
| `transactions_transaction` | `Transaction` | transactions | Completed payment |

## Relation summary

| From | Field | To | Type | `on_delete` | Effect |
|---|---|---|---|---|---|
| `wallet.Employee` | `user` | `accounts.User` | OneToOne | `CASCADE` | Deleting the user deletes the employee profile |
| `wallet.TopUp` | `user` | `wallet.Employee` | OneToOne ⚠️ | `CASCADE` | See the note in [wallet.md](wallet.md) |
| `wallet.TopUp` | `created_by` | `accounts.User` | ForeignKey | `SET_NULL` | History survives the admin's deletion |
| `partners.Partner` | `user` | `accounts.User` | OneToOne | `CASCADE` | Deleting the user deletes the partner record |
| `partners.PartnerDecision` | `partner` | `partners.Partner` | ForeignKey | `CASCADE` | Decisions vanish with the partner |
| `partners.PartnerDecision` | `agent` | `accounts.User` | ForeignKey | `SET_NULL` | Decision stays, agent becomes `NULL` |
| `transactions.QRCode` | `employee` | `wallet.Employee` | ForeignKey | `CASCADE` | QR codes follow the employee |
| `transactions.Transaction` | `qr_code` | `transactions.QRCode` | OneToOne | `PROTECT` | A redeemed QR can no longer be deleted |
| `transactions.Transaction` | `employee` | `wallet.Employee` | ForeignKey | `PROTECT` | Protects accounting integrity |
| `transactions.Transaction` | `partner` | `partners.Partner` | ForeignKey | `PROTECT` | Protects accounting integrity |
| `transactions.Transaction` | `cancelled_by` | `accounts.User` | ForeignKey | `SET_NULL` | Cancellation trace is kept |

### Reading the `on_delete` strategies

- **`CASCADE`** — used for *profile* data: it is meaningless without its user, so it is
  deleted along with it.
- **`PROTECT`** — used for *accounting* data: Django raises a `ProtectedError` and
  refuses the deletion, guaranteeing a transaction can never be orphaned.
- **`SET_NULL`** — used for *audit* fields ("who did what"): the history row must survive
  even when the agent leaves the company.

## Payment lifecycle

```
1. TopUp created by an admin       →  Employee.balance increases
2. Employee requests a QR          →  QRCode(token, amount, expires_at = now + 30min, is_used = False)
3. Partner scans the token         →  checks: is_used == False AND is_expired() == False
4. Validation                      →  Transaction created
                                      QRCode.is_used = True
                                      Employee.balance -= amount
5. (optional) Cancellation         →  is_cancelled = True, cancelled_at, cancelled_by, reason
                                      Employee.balance += amount
```

> ⚠️ Steps 4 and 5 write to several tables: they must run inside a
> `transaction.atomic()` with a `select_for_update()` on the `Employee` to prevent double
> spending on concurrent scans.

## Project conventions

- **One model, one responsibility.** Models are deliberately thin; business logic
  (debiting, QR validation) is not implemented yet.
- **String references** (`'accounts.User'`, `'wallet.Employee'`) instead of direct
  imports: this avoids circular imports between apps.
- **Amounts**: always `DecimalField(max_digits=10, decimal_places=2)`, never
  `FloatField` — floating-point rounding is unacceptable for money.
  Maximum representable value: `99,999,999.99 €`.
- **Creation timestamps**: `DateTimeField(auto_now_add=True)`, non-editable.
- **Choices**: `*_CHOICES` constants declared at the top of the class.
- **Labels**: values stored in the database are English, displayed labels are French.

## Known improvement points

These are not blockers, but they should be addressed before production. Details live in
each app's documentation.

| # | App | Issue |
|---|---|---|
| 1 | wallet | `TopUp.user` is a `OneToOneField`: an employee can only ever be credited once |
| 2 | wallet | `TopUp.__str__` references `self.employee`, a field that does not exist → `AttributeError` |
| 3 | accounts | `role` has no `default`: `createsuperuser` produces an empty role |
| 4 | partners | `siren` is not `unique=True` |
| 5 | transactions | No index on `QRCode.is_used` / `expires_at`, nor on transaction dates |
| 6 | global | No `Meta` at all (no `ordering`, no `verbose_name`, no `constraints`) |
| 7 | global | No positivity constraint on amounts (`amount > 0`, `balance >= 0`) |
| 8 | global | No `admin.site.register()`: models are invisible in the Django admin |

## Database configuration

Currently (`backend/config/settings.py`):

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

`dj-database-url` and `psycopg` are already installed: moving to PostgreSQL means
replacing this block with a read of the `DATABASE_URL` environment variable.

> ⚠️ `db.sqlite3` is currently tracked by Git. A database should not be versioned: add it
> to `.gitignore`.
