# App `accounts`

> 🇫🇷 Version française : [../fr/accounts.md](../fr/accounts.md)

## Purpose

`accounts` is the project's **authentication foundation**. It provides the custom user
model that replaces `django.contrib.auth.models.User` across the whole application.

Declared in `backend/config/settings.py`:

```python
AUTH_USER_MODEL = 'accounts.User'
```

Every other app references this model through the string `'accounts.User'` (never a
direct import), which avoids circular imports.

Source file: [backend/accounts/models.py](../../backend/accounts/models.py)

---

## Model `User`

Inherits from `AbstractUser`, so it **keeps all of Django's standard fields** and adds a
single business field: `role`.

```python
class User(AbstractUser):
    ROLE_CHOICES = [
        ('employee', 'Salarié'),
        ('partner',  'Partenaire'),
        ('admin',    'Admin'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
```

### Table: `accounts_user`

#### Fields inherited from `AbstractUser`

| Field | SQL type | Constraints | Description |
|---|---|---|---|
| `id` | `BIGINT` | PK, auto-increment | Technical identifier |
| `password` | `VARCHAR(128)` | NOT NULL | **Hashed** password (PBKDF2 by default) |
| `last_login` | `DATETIME` | NULL | Last successful login |
| `is_superuser` | `BOOL` | NOT NULL, default `False` | Grants every permission |
| `username` | `VARCHAR(150)` | **UNIQUE**, NOT NULL | Login identifier |
| `first_name` | `VARCHAR(150)` | blank allowed | First name |
| `last_name` | `VARCHAR(150)` | blank allowed | Last name |
| `email` | `VARCHAR(254)` | blank allowed, **not unique** | Email address |
| `is_staff` | `BOOL` | NOT NULL, default `False` | Access to `/admin/` |
| `is_active` | `BOOL` | NOT NULL, default `True` | Account disabled if `False` (prefer this over deletion) |
| `date_joined` | `DATETIME` | NOT NULL, default `now` | Sign-up date |

#### Project-specific field

| Field | SQL type | Constraints | Description |
|---|---|---|---|
| `role` | `VARCHAR(20)` | NOT NULL, `choices` | Business role: `employee`, `partner` or `admin` |

#### Permission tables (created automatically by Django)

| Table | Description |
|---|---|
| `accounts_user_groups` | M2M join table `User` ↔ `auth_group` |
| `accounts_user_user_permissions` | M2M join table `User` ↔ `auth_permission` |

---

## The roles

| Stored value | Displayed label | Related profile | What the role allows |
|---|---|---|---|
| `employee` | Salarié | `wallet.Employee` (OneToOne) | View their balance, generate QR codes |
| `partner` | Partenaire | `partners.Partner` (OneToOne) | Scan a QR code, collect payment |
| `admin` | Admin | *(none)* | Credit employees, approve partners, cancel transactions |

> **Important — two distinct notions of rights:**
> `role` is a **business** field, entirely unrelated to `is_staff` / `is_superuser`,
> which govern access to the Django admin interface. A user may have `role='admin'`
> without being `is_staff`, and vice versa.

### The role as a switch

The role determines which profile the user owns:

```
User(role='employee')  ──1—1──►  wallet.Employee   (employer, balance)
User(role='partner')   ──1—1──►  partners.Partner  (business_name, siren, ...)
User(role='admin')     ──────►   no profile, appears as agent/created_by/cancelled_by
```

This consistency is **not enforced by the database**: nothing currently prevents creating
an `Employee` attached to a `User` whose role is `partner`. The check must happen at the
application level (serializer, `clean()` or signal).

---

## Incoming relations

No relation starts from `User`: it is a "leaf" model that other apps point to.

| App | Model | Field | Type | `on_delete` | Meaning |
|---|---|---|---|---|---|
| wallet | `Employee` | `user` | OneToOne | `CASCADE` | Employee profile |
| wallet | `TopUp` | `created_by` | ForeignKey | `SET_NULL` | Admin who credited |
| partners | `Partner` | `user` | OneToOne | `CASCADE` | Merchant profile |
| partners | `PartnerDecision` | `agent` | ForeignKey | `SET_NULL` | Agent who ruled |
| transactions | `Transaction` | `cancelled_by` | ForeignKey | `SET_NULL`, `related_name='cancelled_transactions'` | Admin who cancelled |

### Consequences of deleting a `User`

```
DELETE User
 ├─ CASCADE  → wallet.Employee deleted
 │              └─ CASCADE → transactions.QRCode deleted
 │              └─ PROTECT → transactions.Transaction  ❌ BLOCKS the deletion
 ├─ CASCADE  → partners.Partner deleted
 │              └─ CASCADE → partners.PartnerDecision deleted
 │              └─ PROTECT → transactions.Transaction  ❌ BLOCKS the deletion
 ├─ SET_NULL → wallet.TopUp.created_by = NULL
 ├─ SET_NULL → partners.PartnerDecision.agent = NULL
 └─ SET_NULL → transactions.Transaction.cancelled_by = NULL
```

**In practice**: as soon as a user has taken part in a transaction, deleting them raises
a `ProtectedError`. That is intentional — the correct move is setting
`is_active = False` instead of deleting.

---

## Representation

```python
def __str__(self):
    return self.username
```

---

## Migrations

| File | Content |
|---|---|
| `0001_initial.py` | Creates `accounts_user` with every `AbstractUser` field + `role` |
| `0002_alter_user_role.py` | Translates the `ROLE_CHOICES` labels into French |

> Changing `choices` does **not** alter the SQL schema (Django creates no `CHECK`
> constraint): migration `0002` is purely declarative. Value validation only happens in
> `full_clean()` and in forms/serializers.

---

## Usage examples

```python
from django.contrib.auth import get_user_model

User = get_user_model()   # ✅ always go through get_user_model()

# Creating an employee
user = User.objects.create_user(
    username='jdupont',
    email='j.dupont@example.com',
    password='password',
    role='employee',
)

# Filter by role
User.objects.filter(role='partner')

# Human-readable role label
user.get_role_display()   # → "Salarié"

# Access the profile (raises RelatedObjectDoesNotExist if missing)
user.employee.balance
user.partner.business_name

# Existence check without an exception
if hasattr(user, 'employee'):
    ...
```

---

## Things to watch

| Topic | Observation | Recommendation |
|---|---|---|
| Role without a default | `role` has neither `default` nor `null=True`. `createsuperuser` does not ask for it → empty string in the database | Add `default='employee'` or include it in `REQUIRED_FIELDS` |
| Email not unique | Inherited from `AbstractUser` | Add `unique=True` if login is meant to use email |
| Role ↔ profile consistency | Not enforced by the database | Validate in `Employee.clean()` / `Partner.clean()` |
| No custom `Manager` | No `User.objects.employees()` shortcut | Optional, but convenient |
| Empty admin | `accounts/admin.py` registers nothing | Add a `UserAdmin` that displays `role` |

### Admin registration (to be added)

```python
# backend/accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'role', 'is_active', 'is_staff')
    list_filter  = ('role', 'is_active', 'is_staff')
    fieldsets = BaseUserAdmin.fieldsets + (('Business role', {'fields': ('role',)}),)
```
