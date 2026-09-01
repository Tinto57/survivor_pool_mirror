# App `transactions`

> 🇫🇷 Version française : [../fr/transactions.md](../fr/transactions.md)

## Purpose

`transactions` implements the **payment mechanism**: an employee generates a QR code for
a given amount, a partner scans it, a transaction is recorded.

This is the most sensitive app in the project: it deals with money, concurrency and
auditability.

Source file: [backend/transactions/models.py](../../backend/transactions/models.py)

---

## Model `QRCode`

A **single-use, short-lived** payment token.

```python
class QRCode(models.Model):
    employee   = models.ForeignKey('wallet.Employee', on_delete=models.CASCADE)
    token      = models.CharField(max_length=100, unique=True, editable=False)
    amount     = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(editable=False)
    is_used    = models.BooleanField(default=False)
```

### Table: `transactions_qrcode`

| Field | SQL type | Constraints | Description |
|---|---|---|---|
| `id` | `BIGINT` | PK, auto | Technical identifier |
| `employee_id` | `BIGINT` | FK → `wallet_employee.id`, NOT NULL | Issuing employee |
| `token` | `VARCHAR(100)` | **UNIQUE**, NOT NULL, `editable=False` | Secret encoded in the QR |
| `amount` | `DECIMAL(10,2)` | NOT NULL | Payment amount in euros |
| `created_at` | `DATETIME` | NOT NULL, `auto_now_add` | Generation date |
| `expires_at` | `DATETIME` | NOT NULL, `editable=False` | Expiry date (creation + 30 min) |
| `is_used` | `BOOL` | NOT NULL, default `False` | Set to `True` once scanned |

### Automatic generation — the `save()` override

```python
def save(self, *args, **kwargs):
    if not self.token:
        self.token = secrets.token_urlsafe(32)
    if not self.expires_at:
        self.expires_at = timezone.now() + timedelta(minutes=30)
    super().save(*args, **kwargs)
```

Two values are computed on the first save only (the `if not ...` guards ensure a later
`save()` regenerates nothing):

- **`token`** — `secrets.token_urlsafe(32)` produces 32 bytes of cryptographically secure
  randomness, base64url-encoded → **43 characters**, ~256 bits of entropy. Using
  `secrets` (rather than `random`) is the right call: it draws from the system CSPRNG,
  making the token unpredictable even to someone who knows previous ones. `unique=True`
  adds an index that both guarantees no collision and makes token lookup instant.
- **`expires_at`** — a fixed **30-minute** window hardcoded here. Worth moving to a
  setting (`settings.QRCODE_TTL_MINUTES`) so it can change without a migration.

> `editable=False` on `token` and `expires_at` excludes them from `ModelForm`s and the
> admin: only code can set them.

### Method `is_expired()`

```python
def is_expired(self):
    return timezone.now() > self.expires_at
```

Computed in Python, so it cannot be used in a `filter()`. To query expired QR codes in
the database:

```python
QRCode.objects.filter(expires_at__lt=timezone.now())
```

### QR code validity

A QR is redeemable if and only if:

```python
qr.is_used is False  and  not qr.is_expired()
```

No database constraint enforces this: the validation code must check it, under a lock.

### Representation

```python
def __str__(self):
    return f"QR {self.token[:8]}... ({self.amount}€)"
```

The token is truncated — good practice, it must not leak into logs or the admin.

---

## Model `Transaction`

The **permanent** record of a completed payment.

```python
class Transaction(models.Model):
    qr_code             = models.OneToOneField(QRCode, on_delete=models.PROTECT)
    employee            = models.ForeignKey('wallet.Employee', on_delete=models.PROTECT)
    partner             = models.ForeignKey('partners.Partner', on_delete=models.PROTECT)
    amount              = models.DecimalField(max_digits=10, decimal_places=2)
    validated_at        = models.DateTimeField(auto_now_add=True)
    is_cancelled        = models.BooleanField(default=False)
    cancelled_at        = models.DateTimeField(null=True, blank=True)
    cancelled_by        = models.ForeignKey('accounts.User', on_delete=models.SET_NULL,
                                            null=True, blank=True,
                                            related_name='cancelled_transactions')
    cancellation_reason = models.TextField(blank=True)
```

### Table: `transactions_transaction`

| Field | SQL type | Constraints | Description |
|---|---|---|---|
| `id` | `BIGINT` | PK, auto | Technical identifier |
| `qr_code_id` | `BIGINT` | FK → `transactions_qrcode.id`, **UNIQUE**, NOT NULL | Redeemed QR |
| `employee_id` | `BIGINT` | FK → `wallet_employee.id`, NOT NULL | Paying employee |
| `partner_id` | `BIGINT` | FK → `partners_partner.id`, NOT NULL | Collecting merchant |
| `amount` | `DECIMAL(10,2)` | NOT NULL | Amount actually debited |
| `validated_at` | `DATETIME` | NOT NULL, `auto_now_add` | Collection timestamp |
| `is_cancelled` | `BOOL` | NOT NULL, default `False` | Transaction cancelled |
| `cancelled_at` | `DATETIME` | NULL | Cancellation timestamp |
| `cancelled_by_id` | `BIGINT` | FK → `accounts_user.id`, NULL | Who cancelled |
| `cancellation_reason` | `TEXT` | NOT NULL, `blank=True` | Cancellation reason |

### `qr_code` as a `OneToOneField` — the double-spend guard

This is the app's most important design point.

`OneToOneField` puts a `UNIQUE` constraint on `qr_code_id`: **the database itself refuses
to let one QR code produce two transactions**. If two requests try to redeem the same
token in parallel, the second raises an `IntegrityError` instead of debiting the employee
twice.

That guarantee is far stronger than the `is_used` boolean alone, which is vulnerable to a
race between the read and the write. The two complement each other: `is_used` serves the
happy path (a clean error message), the `UNIQUE` constraint is the safety net under
concurrency.

### `PROTECT` everywhere — accounting integrity

`qr_code`, `employee` and `partner` all use `on_delete=PROTECT`. Any attempt to delete an
employee, a partner or a used QR code raises a `ProtectedError`.

**Practical consequence**: entities involved in a transaction are permanently
undeletable. Removing an actor is done by deactivation (`User.is_active = False`,
`Partner.status = 'closed'`), never by deletion. This is intentional — an orphaned
transaction would be a hole in the books.

### `amount` duplicated from `QRCode`

`Transaction.amount` copies `QRCode.amount`. This denormalisation is **deliberate**: it
freezes the amount at collection time. Even if the QR code were altered afterwards, the
transaction keeps the value actually debited. That is the immutability principle of
accounting entries.

### The cancellation block

Four fields form a coherent set:

| Field | Role |
|---|---|
| `is_cancelled` | Flag, filterable and indexable |
| `cancelled_at` | When |
| `cancelled_by` | Who (`SET_NULL`: the trace outlives the admin's deletion) |
| `cancellation_reason` | Why |

**A cancelled transaction is never deleted**: the row stays, flagged. It is the
equivalent of a reversing entry in accounting — you do not erase, you offset.

These four fields must stay consistent with each other (the last three set if and only if
`is_cancelled` is true). Nothing guarantees that today — see *Things to watch*.

### `related_name='cancelled_transactions'`

Not strictly required — `Transaction` has no other FK to `User` — but the explicit name
makes the intent readable from the `User` side:

```python
admin_user.cancelled_transactions.all()
```

### Representation

```python
def __str__(self):
    return f"{self.amount}€ - {self.employee.user.username} → {self.partner.business_name}"
```

Traverses `employee → user` and `partner`: **three queries** per display. Always use
`select_related('employee__user', 'partner')` on a list.

---

## Relations

### Outgoing

| Field | To | Type | `on_delete` |
|---|---|---|---|
| `QRCode.employee` | `wallet.Employee` | ForeignKey | `CASCADE` |
| `Transaction.qr_code` | `transactions.QRCode` | OneToOne | `PROTECT` |
| `Transaction.employee` | `wallet.Employee` | ForeignKey | `PROTECT` |
| `Transaction.partner` | `partners.Partner` | ForeignKey | `PROTECT` |
| `Transaction.cancelled_by` | `accounts.User` | ForeignKey | `SET_NULL` |

No incoming relations: `transactions` is the graph's endpoint.

> **A contradiction worth noting**: `QRCode.employee` uses `CASCADE` while
> `Transaction.qr_code` uses `PROTECT`. Deleting an `Employee` would try to cascade-delete
> their QR codes, which `Transaction`'s `PROTECT` will block as soon as one QR has been
> redeemed. The outcome is correct (the deletion fails) but the intent would be clearer
> with `PROTECT` on `QRCode.employee` too.

---

## Full collection flow

```
┌─ EMPLOYEE ────────────────────────────────────────────────────────┐
│ 1. Requests a 12€ QR                                              │
│    check: employee.balance >= 12                                  │
│    QRCode.objects.create(employee=..., amount=12)                 │
│      → token   = secrets.token_urlsafe(32)                        │
│      → expires_at = now + 30 min                                  │
│      → is_used = False                                            │
│ 2. The token is encoded as a QR image (`qrcode` lib) and shown    │
└───────────────────────────────────────────────────────────────────┘
                              │  scan
                              ▼
┌─ PARTNER ─────────────────────────────────────────────────────────┐
│ 3. POSTs the token                                                │
│ 4. Checks, inside an atomic transaction with a lock:              │
│      qr.is_used is False                                          │
│      qr.is_expired() is False                                     │
│      partner.status == 'active'                                   │
│      employee.balance >= qr.amount                                │
│ 5. Writes:                                                        │
│      Transaction.objects.create(qr_code=qr, employee=...,         │
│                                 partner=..., amount=qr.amount)    │
│      qr.is_used = True                    ; qr.save()             │
│      employee.balance -= qr.amount        ; employee.save()       │
└───────────────────────────────────────────────────────────────────┘
```

### Reference implementation

```python
from django.db import transaction, IntegrityError
from django.utils import timezone

def redeem(token: str, partner):
    with transaction.atomic():
        qr = (QRCode.objects
              .select_for_update()
              .select_related('employee')
              .get(token=token))

        if qr.is_used:
            raise ValueError("QR code already used")
        if qr.is_expired():
            raise ValueError("QR code expired")
        if partner.status != 'active':
            raise ValueError("Partner not active")

        employee = Employee.objects.select_for_update().get(pk=qr.employee_id)
        if employee.balance < qr.amount:
            raise ValueError("Insufficient balance")

        try:
            tx = Transaction.objects.create(
                qr_code=qr, employee=employee, partner=partner, amount=qr.amount,
            )
        except IntegrityError:          # double-spend safety net
            raise ValueError("QR code already redeemed")

        qr.is_used = True
        qr.save(update_fields=['is_used'])

        employee.balance -= qr.amount
        employee.save(update_fields=['balance'])

        return tx
```

Both `select_for_update()` calls are essential: they serialise concurrent scans of the
same QR code and concurrent debits of the same balance.

> `select_for_update()` is a **no-op on SQLite** (no row locking). One more reason to move
> to PostgreSQL before production; until then, the `UNIQUE` constraint on `qr_code` is the
> real protection.

---

## Cancellation flow

```python
with transaction.atomic():
    tx = Transaction.objects.select_for_update().get(pk=pk)
    if tx.is_cancelled:
        raise ValueError("Transaction already cancelled")

    tx.is_cancelled        = True
    tx.cancelled_at        = timezone.now()
    tx.cancelled_by        = request.user
    tx.cancellation_reason = reason
    tx.save(update_fields=['is_cancelled', 'cancelled_at',
                           'cancelled_by', 'cancellation_reason'])

    employee = Employee.objects.select_for_update().get(pk=tx.employee_id)
    employee.balance += tx.amount
    employee.save(update_fields=['balance'])
```

The QR code stays `is_used = True`: it is not reusable after a cancellation. The employee
must generate a new one.

---

## Typical queries

```python
from transactions.models import QRCode, Transaction
from django.db.models import Sum, Count
from django.utils import timezone

# An employee's currently valid QR codes
QRCode.objects.filter(employee=employee, is_used=False,
                      expires_at__gt=timezone.now())

# Cleaning up expired, never-used QR codes
QRCode.objects.filter(is_used=False, expires_at__lt=timezone.now()).delete()

# An employee's history, without N+1 queries
(Transaction.objects
    .filter(employee=employee, is_cancelled=False)
    .select_related('partner')
    .order_by('-validated_at'))

# A partner's revenue
(Transaction.objects
    .filter(partner=partner, is_cancelled=False)
    .aggregate(total=Sum('amount'), count=Count('id')))

# Cancelled transactions with their author
(Transaction.objects
    .filter(is_cancelled=True)
    .select_related('cancelled_by', 'employee__user', 'partner'))

# Today's volume
(Transaction.objects
    .filter(validated_at__date=timezone.now().date(), is_cancelled=False)
    .aggregate(total=Sum('amount')))
```

---

## Things to watch

| Topic | Observation | Recommendation |
|---|---|---|
| No business index | `is_used`, `expires_at`, `validated_at`, `is_cancelled` are unindexed | Add `db_index` / `Meta.indexes` |
| Hardcoded TTL | 30 min inside `save()` | `settings.QRCODE_TTL_MINUTES` |
| Unconstrained amounts | `amount` can be ≤ 0 | `CheckConstraint(amount__gt=0)` |
| Cancellation consistency | `is_cancelled=False` with `cancelled_at` set is possible | Combined `CheckConstraint` |
| Debit is not automatic | No signal touches `balance` | Wrap it in a service, as shown above |
| `CASCADE` vs `PROTECT` | Inconsistent between `QRCode.employee` and `Transaction` | Standardise on `PROTECT` |
| No purge | Expired QR codes pile up | Scheduled cleanup task |
| `select_for_update` on SQLite | No effect | Move to PostgreSQL |
| No `ordering` | Histories unsorted by default | `Meta.ordering = ['-validated_at']` |
| Empty admin | Models missing from `/admin/` | Register both models read-only |

### Recommended constraints and indexes

```python
class QRCode(models.Model):
    ...
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_used', 'expires_at']),
            models.Index(fields=['employee', '-created_at']),
        ]
        constraints = [
            models.CheckConstraint(check=models.Q(amount__gt=0), name='qrcode_amount_positive'),
        ]

class Transaction(models.Model):
    ...
    class Meta:
        ordering = ['-validated_at']
        indexes = [
            models.Index(fields=['partner', '-validated_at']),
            models.Index(fields=['employee', '-validated_at']),
        ]
        constraints = [
            models.CheckConstraint(check=models.Q(amount__gt=0),
                                   name='transaction_amount_positive'),
            models.CheckConstraint(
                check=(models.Q(is_cancelled=False, cancelled_at__isnull=True)
                       | models.Q(is_cancelled=True,  cancelled_at__isnull=False)),
                name='transaction_cancellation_coherent',
            ),
        ]
```
