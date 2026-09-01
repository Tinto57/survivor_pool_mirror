# App `wallet`

> 🇫🇷 Version française : [../fr/wallet.md](../fr/wallet.md)

## Purpose

`wallet` manages the **employees' wallet**: the employee profile that carries the
balance, and the history of credits issued by the employer or an administrator.

This is where money enters the system. It leaves through
[`transactions`](transactions.md).

Source file: [backend/wallet/models.py](../../backend/wallet/models.py)

---

## Model `Employee`

Business profile of a user whose role is `employee`. It carries the **available balance**.

```python
class Employee(models.Model):
    user     = models.OneToOneField('accounts.User', on_delete=models.CASCADE)
    employer = models.CharField(max_length=200)
    balance  = models.DecimalField(max_digits=10, decimal_places=2, default=0)
```

### Table: `wallet_employee`

| Field | SQL type | Constraints | Description |
|---|---|---|---|
| `id` | `BIGINT` | PK, auto | Technical identifier |
| `user_id` | `BIGINT` | FK → `accounts_user.id`, **UNIQUE**, NOT NULL | Associated login account |
| `employer` | `VARCHAR(200)` | NOT NULL | Employing company name (free text) |
| `balance` | `DECIMAL(10,2)` | NOT NULL, default `0.00` | Available balance in euros |

### Details

- **`user` as a `OneToOneField`**: a user has at most one employee profile. The `UNIQUE`
  constraint is enforced in the database. Reverse access is `user.employee`.
- **`on_delete=CASCADE`**: deleting the account deletes the profile. In practice the
  deletion will often be blocked by `PROTECT`ed `Transaction` rows.
- **`employer` is a free-text string**, not a foreign key. That is fine as long as there
  is no company-side feature; the day you need to group employees by employer, invoice a
  company or manage a company budget, a dedicated `Company` model becomes necessary —
  otherwise typos ("ACME" / "Acme Ltd") make any grouping impossible.
- **`balance` as a `Decimal`**: never a `float`. Range: `-99,999,999.99` to
  `99,999,999.99`. Nothing currently forbids a negative balance — see *Things to watch*.

### Representation

```python
def __str__(self):
    return f"{self.user.username}: ({self.balance}€)"
```

⚠️ This triggers an extra SQL query on `accounts_user` on every display. In list views,
use `Employee.objects.select_related('user')`.

---

## Model `TopUp`

A history row: "employee X was credited Y € by Z on …".

```python
class TopUp(models.Model):
    user       = models.OneToOneField(Employee, on_delete=models.CASCADE)
    amount     = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
```

### Table: `wallet_topup`

| Field | SQL type | Constraints | Description |
|---|---|---|---|
| `id` | `BIGINT` | PK, auto | Technical identifier |
| `user_id` | `BIGINT` | FK → `wallet_employee.id`, **UNIQUE**, NOT NULL | Credited employee |
| `amount` | `DECIMAL(10,2)` | NOT NULL | Credited amount in euros |
| `created_at` | `DATETIME` | NOT NULL, `auto_now_add` | Credit timestamp |
| `created_by_id` | `BIGINT` | FK → `accounts_user.id`, NULL | Admin who performed the operation |

### Details

- **`created_at = auto_now_add=True`**: set automatically on insert, immutable afterwards
  (the field is `editable=False`, so it does not appear in forms).
- **`created_by` with `SET_NULL`**: if the administrator is deleted, the history row
  **stays** with `created_by = NULL`. That is the intended behaviour for an audit log —
  a money movement must never lose its trace.
- **A `TopUp` does not update `Employee.balance` automatically.** There is no `save()`
  override and no `post_save` signal. Crediting the balance must be done explicitly by
  the calling code, inside the same atomic transaction:

```python
from django.db import transaction

with transaction.atomic():
    employee = Employee.objects.select_for_update().get(pk=pk)
    TopUp.objects.create(user=employee, amount=amount, created_by=request.user)
    employee.balance += amount
    employee.save(update_fields=['balance'])
```

---

## ⚠️ Two bugs to fix in `TopUp`

### 1. `user` should be a `ForeignKey`, not a `OneToOneField`

```python
user = models.OneToOneField(Employee, on_delete=models.CASCADE)   # ❌
```

`OneToOneField` puts a `UNIQUE` constraint on `user_id`: **an employee can only ever be
credited once for the entire lifetime of the database**. The second credit raises
`IntegrityError: UNIQUE constraint failed`.

Yet `TopUp` is a history by nature: an employee is topped up every month.

```python
employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='topups')  # ✅
```

Renaming `user` → `employee` is also desirable: the field points to an `Employee`, not a
`User`, and calling it `user` is confusing next to `created_by`, which really is a `User`.

### 2. `__str__` references a non-existent field

```python
def __str__(self):
    return f"+{self.amount}€ for {self.employee.user.username}"   # ❌ self.employee does not exist
```

The field is called `user`, not `employee` → `AttributeError` as soon as a `TopUp` is
displayed (in a shell, in the admin, in a log). After the rename proposed above, this
`__str__` becomes correct as-is.

Both fixes require a new migration:

```bash
python manage.py makemigrations wallet
python manage.py migrate
```

---

## Relations

### Outgoing

| Field | To | Type | `on_delete` |
|---|---|---|---|
| `Employee.user` | `accounts.User` | OneToOne | `CASCADE` |
| `TopUp.user` | `wallet.Employee` | OneToOne ⚠️ | `CASCADE` |
| `TopUp.created_by` | `accounts.User` | ForeignKey | `SET_NULL` |

### Incoming to `Employee`

| App | Model | Field | Type | `on_delete` | Reverse access |
|---|---|---|---|---|---|
| wallet | `TopUp` | `user` | OneToOne | `CASCADE` | `employee.topup` |
| transactions | `QRCode` | `employee` | ForeignKey | `CASCADE` | `employee.qrcode_set` |
| transactions | `Transaction` | `employee` | ForeignKey | `PROTECT` | `employee.transaction_set` |

---

## Place in the business flow

```
        ADMIN                    EMPLOYEE                  PARTNER
          │                         │                         │
          │  TopUp(+50€)            │                         │
          ├────────────────────────►│                         │
          │   balance += 50         │                         │
          │                         │  QRCode(12€)            │
          │                         ├────────────────────────►│
          │                         │            Transaction  │
          │                         │◄────────────────────────┤
          │                         │   balance -= 12         │
```

`wallet` is therefore **the only entry point for money** and the single owner of the
balance. Every financial operation must read/write `Employee.balance`.

---

## Typical queries

```python
from wallet.models import Employee, TopUp
from django.db.models import Sum

# One employee's balance
Employee.objects.get(user__username='jdupont').balance

# Employees of a given employer, without an N+1 query on user
Employee.objects.filter(employer='ACME').select_related('user')

# Total credited across the platform
TopUp.objects.aggregate(total=Sum('amount'))['total']

# One employee's history (after switching to ForeignKey + related_name='topups')
employee.topups.order_by('-created_at')

# Employees in the red (an anomaly worth monitoring)
Employee.objects.filter(balance__lt=0)
```

---

## Things to watch

| Topic | Observation | Recommendation |
|---|---|---|
| `TopUp.user` OneToOne | Only one credit per employee is possible | Switch to `ForeignKey` (see above) |
| `TopUp.__str__` | `AttributeError` | Fix the field name |
| Negative balance | No constraint | `CheckConstraint(check=Q(balance__gte=0))` |
| Negative or zero amount | No constraint | `CheckConstraint(check=Q(amount__gt=0))` |
| Balance not recomputable | `balance` is denormalised, with no verification | Add a reconciliation command `Σ TopUp − Σ Transaction` |
| Concurrency | Two simultaneous credits can overwrite each other | Always use `select_for_update()` |
| No `ordering` | History is unsorted by default | `class Meta: ordering = ['-created_at']` on `TopUp` |
| Empty admin | Models missing from `/admin/` | Register `Employee` and `TopUp` |

### Recommended constraints

```python
class Employee(models.Model):
    ...
    class Meta:
        verbose_name = 'employee'
        constraints = [
            models.CheckConstraint(check=models.Q(balance__gte=0), name='employee_balance_positive'),
        ]

class TopUp(models.Model):
    ...
    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(check=models.Q(amount__gt=0), name='topup_amount_positive'),
        ]
```
