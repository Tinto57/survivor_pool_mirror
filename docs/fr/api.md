# App `api`

> 🇬🇧 English version: [../en/api.md](../en/api.md)

## Rôle

`api` est l'app destinée à **exposer les données via HTTP** (Django REST Framework).
Elle ne contient **aucun modèle** et ne crée **aucune table** : elle n'est pas une source
de données mais une couche de présentation au-dessus de `accounts`, `wallet`, `partners`
et `transactions`.

Fichier source : [backend/api/models.py](../../backend/api/models.py) (vide)

---

## État actuel

| Fichier | Contenu |
|---|---|
| `models.py` | Vide (commentaire généré) |
| `views.py` | Vide |
| `admin.py` | Vide |
| `apps.py` | `ApiConfig` |
| `migrations/` | Contient seulement `__init__.py` — aucune migration, aucune table |
| `urls.py` | **Absent** |
| `serializers.py` | **Absent** |

`config/urls.py` ne route pour l'instant que `/admin/` :

```python
urlpatterns = [
    path('admin/', admin.site.urls),
]
```

Aucun endpoint API n'est donc exposé à ce jour.

---

## Pourquoi une app sans modèle ?

C'est un choix d'architecture volontaire et courant :

- les apps métier (`accounts`, `wallet`, `partners`, `transactions`) restent
  **concentrées sur les données** — modèles, contraintes, invariants ;
- `api` concentre **l'exposition** — serializers, vues, permissions, routage,
  versionnement ;
- l'API peut évoluer (v1 → v2, changement de format) sans toucher au schéma de la base.

L'alternative — un `serializers.py` et un `views.py` dans chaque app — est tout aussi
valable. L'important est de ne pas mélanger les deux approches.

---

## Structure cible

```
backend/api/
├── __init__.py
├── apps.py
├── serializers.py     # traduction modèle ⇄ JSON
├── views.py           # ViewSets DRF
├── permissions.py     # règles d'accès par rôle
├── urls.py            # routeur
└── services.py        # logique métier transactionnelle (redeem, top-up, cancel)
```

À brancher dans `config/urls.py` :

```python
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('api.urls')),
]
```

---

## Correspondance modèles → endpoints envisagés

| Ressource | Modèle source | Endpoints | Accès |
|---|---|---|---|
| Authentification | `accounts.User` | `POST /auth/login/`, `POST /auth/register/`, `GET /auth/me/` | public / authentifié |
| Solde | `wallet.Employee` | `GET /me/wallet/` | `role='employee'` |
| Créditation | `wallet.TopUp` | `POST /employees/{id}/topup/`, `GET /me/topups/` | admin / salarié |
| QR code | `transactions.QRCode` | `POST /qrcodes/`, `GET /me/qrcodes/` | `role='employee'` |
| Encaissement | `transactions.Transaction` | `POST /transactions/redeem/` | `role='partner'`, `status='active'` |
| Annulation | `transactions.Transaction` | `POST /transactions/{id}/cancel/` | `role='admin'` |
| Historique | `transactions.Transaction` | `GET /me/transactions/` | salarié ou partenaire |
| Annuaire | `partners.Partner` | `GET /partners/`, `GET /partners/{id}/` | authentifié |
| Candidature | `partners.Partner` | `POST /partners/` | public |
| Agrément | `partners.PartnerDecision` | `POST /partners/{id}/decision/` | `role='admin'` |

---

## Règles à faire respecter par la couche API

Le schéma de base ne contraint pas ces règles : c'est le rôle des permissions et des
serializers.

| Règle | Où la vérifier |
|---|---|
| Un salarié ne voit que son propre solde et son propre historique | Filtrage du queryset sur `request.user` |
| Un partenaire ne voit que ses propres encaissements | Idem |
| Seul un partenaire `status='active'` peut encaisser | Permission dédiée |
| `Employee.balance` n'est **jamais** modifiable directement par l'API | `read_only_fields` sur le serializer |
| `QRCode.token` et `expires_at` ne sont jamais fournis par le client | `editable=False` + `read_only_fields` |
| Le rôle d'un utilisateur n'est pas modifiable par lui-même | `read_only_fields` hors admin |
| Un montant de QR ne peut dépasser le solde disponible | Validation dans le serializer |
| Débit et transaction dans la même atomique | Fonction de service, pas la vue |

---

## Exemple de serializers

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
        read_only_fields = ['balance']       # jamais modifiable via l'API


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
            raise serializers.ValidationError("Le montant doit être positif.")
        if value > employee.balance:
            raise serializers.ValidationError("Solde insuffisant.")
        return value


class TransactionSerializer(serializers.ModelSerializer):
    partner_name = serializers.CharField(source='partner.business_name', read_only=True)

    class Meta:
        model  = Transaction
        fields = ['id', 'partner_name', 'amount', 'validated_at', 'is_cancelled']
        read_only_fields = fields
```

---

## Configuration DRF

`rest_framework` est déjà dans `INSTALLED_APPS`, mais **aucun bloc `REST_FRAMEWORK`**
n'est défini dans `settings.py`. Les valeurs par défaut s'appliquent donc :
`SessionAuthentication` seule, aucune permission globale, aucune pagination.

Configuration minimale à ajouter :

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

## Permissions par rôle

`accounts.User.role` est le pivot des autorisations côté API :

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

`corsheaders` est installé et son middleware est placé **en premier**, ce qui est correct.

```python
# NOTE: Set to False when in production !!!!
CORS_ALLOW_ALL_ORIGINS = True
```

⚠️ Ce réglage autorise n'importe quelle origine. À remplacer avant mise en production :

```python
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = ['https://app.survivor-pool.example']
CORS_ALLOW_CREDENTIALS = True
```

---

## Points d'attention

| Sujet | Constat | Recommandation |
|---|---|---|
| Aucune route API | `config/urls.py` n'expose que `/admin/` | Créer `api/urls.py` et l'inclure |
| Pas de `REST_FRAMEWORK` | Défauts DRF (pas de permission globale) | Ajouter le bloc de configuration |
| Pas d'authentification par token | Session uniquement, peu adapté à un client mobile | `djangorestframework-simplejwt` |
| `CORS_ALLOW_ALL_ORIGINS = True` | Ouvert à tous | Restreindre en production |
| Pas de `serializers.py` | — | À créer |
| Pas de migrations dans `api` | Normal, l'app n'a pas de modèle | Rien à faire |
| Logique métier | Ne doit pas vivre dans les vues | `api/services.py` avec `transaction.atomic()` |
| Pas de documentation d'API | — | `drf-spectacular` (OpenAPI) |
