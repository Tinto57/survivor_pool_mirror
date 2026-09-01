# App `accounts`

> 🇬🇧 English version: [../en/accounts.md](../en/accounts.md)

## Rôle

`accounts` est le **socle d'authentification** du projet. Elle fournit le modèle
utilisateur personnalisé qui remplace `django.contrib.auth.models.User` pour toute
l'application.

Déclaration dans `backend/config/settings.py` :

```python
AUTH_USER_MODEL = 'accounts.User'
```

Toutes les autres apps référencent ce modèle par la chaîne `'accounts.User'` (jamais par
import direct), ce qui évite les imports circulaires.

Fichier source : [backend/accounts/models.py](../../backend/accounts/models.py)

---

## Modèle `User`

Hérite de `AbstractUser`, donc **conserve tous les champs standards de Django** et y
ajoute un seul champ métier : `role`.

```python
class User(AbstractUser):
    ROLE_CHOICES = [
        ('employee', 'Salarié'),
        ('partner',  'Partenaire'),
        ('admin',    'Admin'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
```

### Table : `accounts_user`

#### Champs hérités de `AbstractUser`

| Champ | Type SQL | Contraintes | Description |
|---|---|---|---|
| `id` | `BIGINT` | PK, auto-incrément | Identifiant technique |
| `password` | `VARCHAR(128)` | NOT NULL | Mot de passe **haché** (PBKDF2 par défaut) |
| `last_login` | `DATETIME` | NULL | Dernière connexion réussie |
| `is_superuser` | `BOOL` | NOT NULL, défaut `False` | Accorde toutes les permissions |
| `username` | `VARCHAR(150)` | **UNIQUE**, NOT NULL | Identifiant de connexion |
| `first_name` | `VARCHAR(150)` | blank autorisé | Prénom |
| `last_name` | `VARCHAR(150)` | blank autorisé | Nom |
| `email` | `VARCHAR(254)` | blank autorisé, **non unique** | Adresse e-mail |
| `is_staff` | `BOOL` | NOT NULL, défaut `False` | Accès à `/admin/` |
| `is_active` | `BOOL` | NOT NULL, défaut `True` | Compte désactivé si `False` (préférer à la suppression) |
| `date_joined` | `DATETIME` | NOT NULL, défaut `now` | Date d'inscription |

#### Champ propre au projet

| Champ | Type SQL | Contraintes | Description |
|---|---|---|---|
| `role` | `VARCHAR(20)` | NOT NULL, `choices` | Rôle métier : `employee`, `partner` ou `admin` |

#### Tables de permissions (créées automatiquement par Django)

| Table | Description |
|---|---|
| `accounts_user_groups` | Table de liaison M2M `User` ↔ `auth_group` |
| `accounts_user_user_permissions` | Table de liaison M2M `User` ↔ `auth_permission` |

---

## Les rôles

| Valeur stockée | Libellé affiché | Profil associé | Ce que le rôle autorise |
|---|---|---|---|
| `employee` | Salarié | `wallet.Employee` (OneToOne) | Consulter son solde, générer des QR codes |
| `partner` | Partenaire | `partners.Partner` (OneToOne) | Scanner un QR code, encaisser |
| `admin` | Admin | *(aucun)* | Créditer les salariés, valider les partenaires, annuler des transactions |

> **Important — deux notions de droits distinctes :**
> `role` est un champ **métier**, sans aucun lien avec `is_staff` / `is_superuser` qui
> gouvernent l'accès à l'interface d'administration Django. Un utilisateur peut avoir
> `role='admin'` sans être `is_staff`, et inversement.

### Le rôle comme aiguillage

Le rôle détermine quel profil l'utilisateur possède :

```
User(role='employee')  ──1—1──►  wallet.Employee   (employer, balance)
User(role='partner')   ──1—1──►  partners.Partner  (business_name, siren, ...)
User(role='admin')     ──────►   pas de profil, apparaît comme agent/created_by/cancelled_by
```

Cette cohérence n'est **pas garantie par la base** : rien n'empêche aujourd'hui de créer
un `Employee` rattaché à un `User` de rôle `partner`. La vérification doit être faite au
niveau applicatif (serializer, `clean()` ou signal).

---

## Relations entrantes

Aucune relation ne part de `User` : c'est un modèle « feuille » que les autres apps
pointent.

| App | Modèle | Champ | Type | `on_delete` | Signification |
|---|---|---|---|---|---|
| wallet | `Employee` | `user` | OneToOne | `CASCADE` | Profil salarié |
| wallet | `TopUp` | `created_by` | ForeignKey | `SET_NULL` | Admin ayant crédité |
| partners | `Partner` | `user` | OneToOne | `CASCADE` | Profil commerçant |
| partners | `PartnerDecision` | `agent` | ForeignKey | `SET_NULL` | Agent ayant statué |
| transactions | `Transaction` | `cancelled_by` | ForeignKey | `SET_NULL`, `related_name='cancelled_transactions'` | Admin ayant annulé |

### Conséquence de la suppression d'un `User`

```
DELETE User
 ├─ CASCADE  → wallet.Employee supprimé
 │              └─ CASCADE → transactions.QRCode supprimés
 │              └─ PROTECT → transactions.Transaction  ❌ BLOQUE la suppression
 ├─ CASCADE  → partners.Partner supprimé
 │              └─ CASCADE → partners.PartnerDecision supprimées
 │              └─ PROTECT → transactions.Transaction  ❌ BLOQUE la suppression
 ├─ SET_NULL → wallet.TopUp.created_by = NULL
 ├─ SET_NULL → partners.PartnerDecision.agent = NULL
 └─ SET_NULL → transactions.Transaction.cancelled_by = NULL
```

**En pratique** : dès qu'un utilisateur a participé à une transaction, sa suppression
lève une `ProtectedError`. C'est volontaire — la bonne pratique est de passer
`is_active = False` plutôt que de supprimer.

---

## Représentation

```python
def __str__(self):
    return self.username
```

---

## Migrations

| Fichier | Contenu |
|---|---|
| `0001_initial.py` | Création de `accounts_user` avec tous les champs d'`AbstractUser` + `role` |
| `0002_alter_user_role.py` | Traduction des libellés des `ROLE_CHOICES` en français |

> Un changement de `choices` ne modifie **pas** le schéma SQL (aucune contrainte `CHECK`
> n'est créée par Django) : la migration `0002` est purement déclarative. La validation
> des valeurs se fait uniquement dans `full_clean()` et dans les formulaires/serializers.

---

## Exemples d'utilisation

```python
from django.contrib.auth import get_user_model

User = get_user_model()   # ✅ toujours passer par get_user_model()

# Création d'un salarié
user = User.objects.create_user(
    username='jdupont',
    email='j.dupont@example.com',
    password='motdepasse',
    role='employee',
)

# Filtrer par rôle
User.objects.filter(role='partner')

# Libellé affichable du rôle
user.get_role_display()   # → "Salarié"

# Accès au profil (lève RelatedObjectDoesNotExist s'il n'existe pas)
user.employee.balance
user.partner.business_name

# Test d'existence sans exception
if hasattr(user, 'employee'):
    ...
```

---

## Points d'attention

| Sujet | Constat | Recommandation |
|---|---|---|
| Rôle sans défaut | `role` n'a ni `default` ni `null=True`. `createsuperuser` ne le demande pas → chaîne vide en base | Ajouter `default='employee'` ou l'inclure dans `REQUIRED_FIELDS` |
| E-mail non unique | Hérité d'`AbstractUser` | Ajouter `unique=True` si la connexion doit se faire par e-mail |
| Cohérence rôle ↔ profil | Non contrainte par la base | Valider dans `Employee.clean()` / `Partner.clean()` |
| Pas de `Manager` custom | Pas de raccourci `User.objects.employees()` | Optionnel, mais pratique |
| Admin vide | `accounts/admin.py` ne registre rien | Ajouter un `UserAdmin` affichant `role` |

### Enregistrement dans l'admin (à ajouter)

```python
# backend/accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'role', 'is_active', 'is_staff')
    list_filter  = ('role', 'is_active', 'is_staff')
    fieldsets = BaseUserAdmin.fieldsets + (('Rôle métier', {'fields': ('role',)}),)
```
