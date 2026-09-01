# App `api`

> 🇫🇷 Version française : [../fr/api.md](../fr/api.md)

## Purpose

`api` is the app meant to **expose data over HTTP** (Django REST Framework). It contains
**no model** and creates **no table**: it is not a data source but a presentation layer on
top of `accounts`, `wallet`, `partners` and `transactions`.

Source file: [backend/api/models.py](../../backend/api/models.py) (empty)

---

## Current state

| File | Content |
|---|---|
| `models.py` | Empty (generated comment) |
| `views.py` | Empty |
| `admin.py` | Empty |
| `apps.py` | `ApiConfig` |
| `migrations/` | Only `__init__.py` — no migration, no table |
| `urls.py` | **Missing** |
| `serializers.py` | **Missing** |

`config/urls.py` currently routes `/admin/` only:

```python
urlpatterns = [
    path('admin/', admin.site.urls),
]
```

So no API endpoint is exposed today.

---

## Why an app with no models?

This is a deliberate and common architectural choice:

- the business apps (`accounts`, `wallet`, `partners`, `transactions`) stay **focused on
  data** — models, constraints, invariants;
- `api` concentrates **exposure** — serializers, views, permissions, routing,
  versioning;
- the API can evolve (v1 → v2, format change) without touching the database schema.

The alternative — a `serializers.py` and a `views.py` inside each app — is equally valid.
What matters is not mixing the two approaches.

---

## Target structure

```
backend/api/
├── __init__.py
├── apps.py
├── serializers.py     # model ⇄ JSON translation
├── views.py           # DRF ViewSets
├── permissions.py     # per-role access rules
├── urls.py            # router
└── services.py        # transactional business logic (redeem, top-up, cancel)
```

Wired into `config/urls.py`:

```python
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('api.urls')),
]
```

---

## Model → endpoint mapping (planned)

| Resource | Source model | Endpoints | Access |
|---|---|---|---|
| Authentication | `accounts.User` | `POST /auth/login/`, `POST /auth/register/`, `GET /auth/me/` | public / authenticated |
| Balance | `wallet.Employee` | `GET /me/wallet/` | `role='employee'` |
| Top-up | `wallet.TopUp` | `POST /employees/{id}/topup/`, `GET /me/topups/` | admin / employee |
| QR code | `transactions.QRCode` | `POST /qrcodes/`, `GET /me/qrcodes/` | `role='employee'` |
| Redemption | `transactions.Transaction` | `POST /transactions/redeem/` | `role='partner'`, `status='active'` |
| Cancellation | `transactions.Transaction` | `POST /transactions/{id}/cancel/` | `role='admin'` |
| History | `transactions.Transaction` | `GET /me/transactions/` | employee or partner |
| Directory | `partners.Partner` | `GET /partners/`, `GET /partners/{id}/` | authenticated |
| Application | `partners.Partner` | `POST /partners/` | public |
| Approval | `partners.PartnerDecision` | `POST /partners/{id}/decision/` | `role='admin'` |

---

## Rules the API layer must enforce

The database schema does not constrain these rules: that is the job of permissions and
serializers.

| Rule | Where to enforce it |
|---|---|
| An employee only sees their own balance and history | Queryset filtering on `request.user` |
| A partner only sees their own collections | Same |
| Only a partner with `status='active'` can collect | Dedicated permission |
| `Employee.balance` is **never** directly writable through the API | `read_only_fields` on the serializer |
| `QRCode.token` and `expires_at` are never client-supplied | `editable=False` + `read_only_fields` |
| A user cannot change their own role | `read_only_fields` outside admin |
| A QR amount cannot exceed the available balance | Serializer validation |
| Debit and transaction inside the same atomic block | A service function, not the view |

---

## Example serializers

```python
# backend/api/serializers.py
from rest_framework import serializers
from wallet.models import Employee
from transactions.models import QRCode, Transaction


class EmployeeSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model  = Employee
        fields = ['id', 'username', 'employer', 'balance']
        read_only_fields = ['balance']       # never writable through the API


class QRCodeSerializer(serializers.ModelSerializer):
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model  = QRCode
        fields = ['id', 'token', 'amount', 'created_at', 'expires_at',
                  'is_used', 'is_expired']
        read_only_fields = ['token', 'created_at', 'expires_at', 'is_used']

    def validate_amount(self, value):
        employee = self.context['request'].user.employee
        if value <= 0:
            raise serializers.ValidationError("Amount must be positive.")
        if value > employee.balance:
            raise serializers.ValidationError("Insufficient balance.")
        return value


class TransactionSerializer(serializers.ModelSerializer):
    partner_name = serializers.CharField(source='partner.business_name', read_only=True)

    class Meta:
        model  = Transaction
        fields = ['id', 'partner_name', 'amount', 'validated_at', 'is_cancelled']
        read_only_fields = fields
```

---

## DRF configuration

`rest_framework` is already in `INSTALLED_APPS`, but **no `REST_FRAMEWORK` block** is
defined in `settings.py`. The defaults therefore apply: `SessionAuthentication` only, no
global permission, no pagination.

Minimal configuration to add:

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        # 'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}
```

---

## Per-role permissions

`accounts.User.role` is the pivot of API authorisation:

```python
# backend/api/permissions.py
from rest_framework.permissions import BasePermission


class IsEmployee(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'employee'


class IsActivePartner(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return (user.is_authenticated
                and user.role == 'partner'
                and hasattr(user, 'partner')
                and user.partner.status == 'active')


class IsAdminRole(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'
```

---

## CORS

`corsheaders` is installed and its middleware sits **first**, which is correct.

```python
# NOTE: Set to False when in production !!!!
CORS_ALLOW_ALL_ORIGINS = True
```

⚠️ This setting allows any origin. It must be replaced before production:

```python
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = ['https://app.survivor-pool.example']
CORS_ALLOW_CREDENTIALS = True
```

---

## Things to watch

| Topic | Observation | Recommendation |
|---|---|---|
| No API route | `config/urls.py` only exposes `/admin/` | Create `api/urls.py` and include it |
| No `REST_FRAMEWORK` block | DRF defaults (no global permission) | Add the configuration block |
| No token authentication | Session only, poorly suited to a mobile client | `djangorestframework-simplejwt` |
| `CORS_ALLOW_ALL_ORIGINS = True` | Open to everyone | Restrict in production |
| No `serializers.py` | — | To be created |
| No migrations in `api` | Normal, the app has no model | Nothing to do |
| Business logic | Must not live in views | `api/services.py` with `transaction.atomic()` |
| No API documentation | — | `drf-spectacular` (OpenAPI) |
