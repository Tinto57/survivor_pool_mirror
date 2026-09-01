# App `partners`

> 🇫🇷 Version française : [../fr/partners.md](../fr/partners.md)

## Purpose

`partners` manages the **merchant partners**: their company record, their geolocation,
their approval status, and the **decision log** produced by administrative agents
reviewing their application.

A partner is the entity that collects payment: they scan employees' QR codes (see
[`transactions`](transactions.md)).

Source file: [backend/partners/models.py](../../backend/partners/models.py)

---

## Model `Partner`

```python
class Partner(models.Model):
    STATUS_CHOICE = [
        ('pending',   "En attente"),
        ('active',    "Actif"),
        ('suspended', "Suspendu"),
        ('closed',    'Cloturé'),
    ]
    status           = models.CharField(choices=STATUS_CHOICE, max_length=20)
    user             = models.OneToOneField('accounts.User', on_delete=models.CASCADE)
    business_name    = models.CharField(max_length=200)
    siren            = models.CharField(max_length=9, validators=[RegexValidator(r'^\d{9}$', ...)])
    business_purpose = models.TextField()
    address          = models.CharField(max_length=300)
    latitude         = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude        = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_featured      = models.BooleanField(default=False)
    registered_at    = models.DateTimeField(auto_now_add=True)
```

### Table: `partners_partner`

| Field | SQL type | Constraints | Description |
|---|---|---|---|
| `id` | `BIGINT` | PK, auto | Technical identifier |
| `status` | `VARCHAR(20)` | NOT NULL, `choices` | Application state (see below) |
| `user_id` | `BIGINT` | FK → `accounts_user.id`, **UNIQUE**, NOT NULL | Merchant's login account |
| `business_name` | `VARCHAR(200)` | NOT NULL | Legal or trading name |
| `siren` | `VARCHAR(9)` | NOT NULL, `^\d{9}$` validator | French company registration number |
| `business_purpose` | `TEXT` | NOT NULL | Corporate purpose / activity description |
| `address` | `VARCHAR(300)` | NOT NULL | Full postal address |
| `latitude` | `DECIMAL(9,6)` | NULL | WGS84 latitude |
| `longitude` | `DECIMAL(9,6)` | NULL | WGS84 longitude |
| `is_featured` | `BOOL` | NOT NULL, default `False` | Highlighted in the application |
| `registered_at` | `DATETIME` | NOT NULL, `auto_now_add` | Application submission date |

### The `siren` field

The SIREN identifies a French company with 9 digits. It is stored as
`CharField(max_length=9)` and **not** as an integer: a SIREN may start with a zero, which
an `IntegerField` would lose.

```python
validators=[RegexValidator(r'^\d{9}$', 'Le SIREN doit contenir exactement 9 chiffres.')]
```

> ⚠️ A Django `validator` is **not** an SQL constraint. It only runs on `full_clean()` —
> that is, through a `ModelForm`, the admin, or a DRF serializer. A
> `Partner.objects.create(siren='abc')` in a shell goes through without error.
>
> ⚠️ `siren` is not `unique=True`: two partners can currently declare the same company.
> Worth fixing if one SIREN must map to a single account.
>
> The validator also does not check the **Luhn checksum**, which would reject a
> syntactically valid but non-existent number.

### Geolocation

`latitude` / `longitude` are `DECIMAL(9,6)`:

- 6 decimal places ≈ **11 cm of precision**, far more than enough to locate a shop;
- 9 digits total → 3 digits before the decimal point, covering `-180.000000` to
  `180.000000` (longitude) and `-90` to `90` (latitude);
- `null=True, blank=True`: coordinates are optional (application submitted without
  geocoding). `null` = value absent in the database, `blank` = field not required in
  forms — both are needed.

These fields power the "partners near me" search. With SQLite/PostgreSQL and no PostGIS,
distance must be computed application-side (haversine formula) or via a `SELECT` with
trigonometric arithmetic. Moving to PostGIS + `django.contrib.gis` (`PointField`) is the
clean solution if this feature becomes central.

### The statuses

| Value | Label | Meaning | Can the partner collect payments? |
|---|---|---|---|
| `pending` | En attente | Application submitted, not yet reviewed | ❌ |
| `active` | Actif | Application accepted, partner operational | ✅ |
| `suspended` | Suspendu | Temporary suspension (dispute, audit) | ❌ |
| `closed` | Cloturé | Partnership terminated, final | ❌ |

Expected transitions:

```
   pending ──accepted──► active ◄──────► suspended
      │                    │                  │
      └──rejected──────────┴──────────────────┴──► closed
```

> These transitions are **not** enforced by the model: `status` is a plain `CharField`.
> Transition logic must live in the business layer. `status` also has no `default` —
> `default='pending'` should be added, since a new application is necessarily pending.

### `is_featured`

Highlight flag (carousel, top of list). Purely editorial, with no effect on permissions.
A partner with `is_featured=True` but `status != 'active'` should never be shown:
filtering must combine both conditions.

### Representation

```python
def __str__(self):
    return self.business_name
```

---

## Model `PartnerDecision`

Audit log of approval decisions. **One row per decision**, never modified nor deleted: it
is the complete history of how the application was handled.

```python
class PartnerDecision(models.Model):
    DECISION_CHOICES = [
        ('accepted', 'Acceptée'),
        ('rejected', 'Refusée'),
    ]
    partner    = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name='decisions')
    decision   = models.CharField(max_length=20, choices=DECISION_CHOICES)
    reason     = models.TextField(blank=True)
    agent      = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

### Table: `partners_partnerdecision`

| Field | SQL type | Constraints | Description |
|---|---|---|---|
| `id` | `BIGINT` | PK, auto | Technical identifier |
| `partner_id` | `BIGINT` | FK → `partners_partner.id`, NOT NULL | Application concerned |
| `decision` | `VARCHAR(20)` | NOT NULL, `choices` | `accepted` or `rejected` |
| `reason` | `TEXT` | NOT NULL, `blank=True` | Rationale (required on rejection, by convention) |
| `agent_id` | `BIGINT` | FK → `accounts_user.id`, NULL | Agent who ruled |
| `created_at` | `DATETIME` | NOT NULL, `auto_now_add` | Decision timestamp |

### Details

- **`related_name='decisions'`**: reverse access is `partner.decisions.all()`, not
  `partner.partnerdecision_set.all()`.
- **`on_delete=CASCADE` on `partner`**: decisions are meaningless without the
  application, so they disappear with it.
- **`on_delete=SET_NULL` on `agent`**: the decision stays on record even if the agent
  leaves the company. That is the golden rule of an audit log: never lose the event.
- **`reason` with `blank=True`**: optional at form level. In the database the column is
  `NOT NULL` and will hold an empty string — Django never uses `NULL` for text fields
  (`null=True` on a `TextField` would create two ways of saying "empty").

### Relationship with `Partner.status`

`PartnerDecision` is **the history**, `Partner.status` is **the current state**. The two
are denormalised with respect to each other: nothing synchronises them automatically.

```python
from django.db import transaction

with transaction.atomic():
    PartnerDecision.objects.create(
        partner=partner, decision='accepted', reason='Application compliant', agent=request.user,
    )
    partner.status = 'active'
    partner.save(update_fields=['status'])
```

The current status can always be recomputed from the latest decision:

```python
last = partner.decisions.order_by('-created_at').first()
```

### Representation

```python
def __str__(self):
    return f"{self.partner.business_name} - {self.decision} ({self.created_at:%d/%m/%Y})"
```

Traverses `partner` → an extra query. Use
`PartnerDecision.objects.select_related('partner', 'agent')` in list views.

---

## Relations

### Outgoing

| Field | To | Type | `on_delete` |
|---|---|---|---|
| `Partner.user` | `accounts.User` | OneToOne | `CASCADE` |
| `PartnerDecision.partner` | `partners.Partner` | ForeignKey (`related_name='decisions'`) | `CASCADE` |
| `PartnerDecision.agent` | `accounts.User` | ForeignKey | `SET_NULL` |

### Incoming

| App | Model | Field | Type | `on_delete` |
|---|---|---|---|---|
| partners | `PartnerDecision` | `partner` | ForeignKey | `CASCADE` |
| transactions | `Transaction` | `partner` | ForeignKey | `PROTECT` |

`Transaction`'s `PROTECT` means that **a partner who has collected at least one payment
can no longer be deleted**: they must be moved to `status='closed'`.

---

## Application lifecycle

```
1. The merchant signs up
   User(role='partner')  +  Partner(status='pending')

2. An agent reviews the application
   PartnerDecision(decision='accepted'|'rejected', reason, agent)

3. Current state is updated
   accepted  →  Partner.status = 'active'    → can collect payments
   rejected  →  Partner.status = 'closed'    → cannot collect payments

4. Life of the partnership
   temporary suspension →  status = 'suspended'  (+ a new PartnerDecision)
   resumption           →  status = 'active'
   termination          →  status = 'closed'
```

---

## Typical queries

```python
from partners.models import Partner, PartnerDecision

# Partners visible in the application
Partner.objects.filter(status='active')

# Highlighted partners (the status filter remains essential)
Partner.objects.filter(status='active', is_featured=True)

# Applications awaiting review, oldest first
Partner.objects.filter(status='pending').order_by('registered_at')

# Geolocated partners only
Partner.objects.filter(status='active', latitude__isnull=False, longitude__isnull=False)

# Full history of an application
partner.decisions.select_related('agent').order_by('-created_at')

# One agent's activity
PartnerDecision.objects.filter(agent=user).select_related('partner')

# Latest decision per application
Partner.objects.prefetch_related('decisions')
```

---

## Things to watch

| Topic | Observation | Recommendation |
|---|---|---|
| `siren` not unique | Duplicate companies possible | `unique=True` |
| `siren` not validated in the database | The `RegexValidator` is ignored outside `full_clean()` | Validate in the serializer, or add a `CheckConstraint` |
| Luhn checksum | Not verified | Add a business validator |
| `status` without a default | Empty string possible on creation | `default='pending'` |
| Free transitions | You can go from `closed` to `active` with no decision | Application-level state machine |
| No index on `status` | The most frequent filter does a full scan | `db_index=True` |
| `decision` has no `pending` | `DECISION_CHOICES` only holds 2 terminal values | Consistent: no decision = no row |
| No `ordering` | History is unsorted | `Meta.ordering = ['-created_at']` |
| `Partner.status` can drift | No automatic link with decisions | Wrap it in a `partner.apply_decision(...)` method |
| Empty admin | Models missing from `/admin/` | Register both models |

### Recommended improvements

```python
class Partner(models.Model):
    status = models.CharField(choices=STATUS_CHOICE, max_length=20,
                              default='pending', db_index=True)
    siren  = models.CharField(max_length=9, unique=True, validators=[...])
    ...
    class Meta:
        ordering = ['business_name']
        verbose_name = 'partner'

class PartnerDecision(models.Model):
    ...
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'partner decision'
```
