# App `wallet`

> 🇬🇧 English version: [../en/wallet.md](../en/wallet.md)

## Rôle

`wallet` gère le **porte-monnaie des salariés** : le profil salarié qui porte le solde,
et l'historique des créditations effectuées par l'employeur ou un administrateur.

C'est le point d'entrée de l'argent dans le système. L'argent en sort via
[`transactions`](transactions.md).

Fichier source : [backend/wallet/models.py](../../backend/wallet/models.py)

---

## Modèle `Employee`

Profil métier d'un utilisateur de rôle `employee`. Il porte le **solde disponible**.

```python
class Employee(models.Model):
    user     = models.OneToOneField('accounts.User', on_delete=models.CASCADE)
    employer = models.CharField(max_length=200)
    balance  = models.DecimalField(max_digits=10, decimal_places=2, default=0)
```

### Table : `wallet_employee`

| Champ | Type SQL | Contraintes | Description |
|---|---|---|---|
| `id` | `BIGINT` | PK, auto | Identifiant technique |
| `user_id` | `BIGINT` | FK → `accounts_user.id`, **UNIQUE**, NOT NULL | Compte de connexion associé |
| `employer` | `VARCHAR(200)` | NOT NULL | Nom de l'entreprise employeuse (texte libre) |
| `balance` | `DECIMAL(10,2)` | NOT NULL, défaut `0.00` | Solde disponible en euros |

### Détails

- **`user` en `OneToOneField`** : un utilisateur a au plus un profil salarié. La
  contrainte `UNIQUE` est posée en base. L'accès inverse se fait par `user.employee`.
- **`on_delete=CASCADE`** : supprimer le compte supprime le profil. En pratique la
  suppression sera souvent bloquée par les `Transaction` en `PROTECT`.
- **`employer` est une chaîne libre**, pas une clé étrangère. C'est suffisant tant qu'il
  n'y a pas de fonctionnalité côté entreprise ; le jour où il faut regrouper les salariés
  par employeur, facturer une société ou gérer un budget d'entreprise, il faudra un
  modèle `Company` dédié — sinon les fautes de frappe (« ACME » / « Acme SA ») rendront
  tout regroupement impossible.
- **`balance` en `Decimal`** : jamais un `float`. Plage : `-99 999 999,99` à
  `99 999 999,99`. Rien n'interdit aujourd'hui un solde négatif — voir *Points d'attention*.

### Représentation

```python
def __str__(self):
    return f"{self.user.username}: ({self.balance}€)"
```

⚠️ Cette implémentation déclenche une requête SQL supplémentaire sur `accounts_user` à
chaque affichage. Dans les listes, utiliser `Employee.objects.select_related('user')`.

---

## Modèle `TopUp`

Ligne d'historique : « le salarié X a été crédité de Y € par Z le … ».

```python
class TopUp(models.Model):
    user       = models.OneToOneField(Employee, on_delete=models.CASCADE)
    amount     = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
```

### Table : `wallet_topup`

| Champ | Type SQL | Contraintes | Description |
|---|---|---|---|
| `id` | `BIGINT` | PK, auto | Identifiant technique |
| `user_id` | `BIGINT` | FK → `wallet_employee.id`, **UNIQUE**, NOT NULL | Salarié crédité |
| `amount` | `DECIMAL(10,2)` | NOT NULL | Montant crédité en euros |
| `created_at` | `DATETIME` | NOT NULL, `auto_now_add` | Horodatage de la créditation |
| `created_by_id` | `BIGINT` | FK → `accounts_user.id`, NULL | Admin auteur de l'opération |

### Détails

- **`created_at = auto_now_add=True`** : renseigné automatiquement à l'insertion, non
  modifiable ensuite (le champ est `editable=False`, il n'apparaît pas dans les
  formulaires).
- **`created_by` en `SET_NULL`** : si l'administrateur est supprimé, la ligne
  d'historique **reste** avec `created_by = NULL`. C'est le comportement voulu pour un
  journal d'audit — on ne perd jamais la trace d'un mouvement d'argent.
- **Le `TopUp` ne met pas à jour `Employee.balance` automatiquement.** Il n'y a ni
  surcharge de `save()`, ni signal `post_save`. Le crédit du solde doit être fait
  explicitement par le code appelant, dans la même transaction atomique :

```python
from django.db import transaction

with transaction.atomic():
    employee = Employee.objects.select_for_update().get(pk=pk)
    TopUp.objects.create(user=employee, amount=amount, created_by=request.user)
    employee.balance += amount
    employee.save(update_fields=['balance'])
```

---

## ⚠️ Deux bugs à corriger dans `TopUp`

### 1. `user` doit être un `ForeignKey`, pas un `OneToOneField`

```python
user = models.OneToOneField(Employee, on_delete=models.CASCADE)   # ❌
```

`OneToOneField` pose une contrainte `UNIQUE` sur `user_id` : **un salarié ne peut être
crédité qu'une seule fois dans toute la vie de la base**. La deuxième créditation lève une
`IntegrityError: UNIQUE constraint failed`.

Or `TopUp` est par nature un historique : un salarié est rechargé tous les mois.

```python
employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='topups')  # ✅
```

Le renommage `user` → `employee` est également souhaitable : le champ pointe un
`Employee`, pas un `User`, et l'appeler `user` prête à confusion avec `created_by` qui
lui est bien un `User`.

### 2. `__str__` référence un champ inexistant

```python
def __str__(self):
    return f"+{self.amount}€ for {self.employee.user.username}"   # ❌ self.employee n'existe pas
```

Le champ s'appelle `user`, pas `employee` → `AttributeError` dès qu'on affiche un
`TopUp` (dans un shell, dans l'admin, dans un log). Après le renommage proposé ci-dessus,
ce `__str__` devient correct tel quel.

Ces deux corrections nécessitent une nouvelle migration :

```bash
python manage.py makemigrations wallet
python manage.py migrate
```

---

## Relations

### Sortantes

| Champ | Vers | Type | `on_delete` |
|---|---|---|---|
| `Employee.user` | `accounts.User` | OneToOne | `CASCADE` |
| `TopUp.user` | `wallet.Employee` | OneToOne ⚠️ | `CASCADE` |
| `TopUp.created_by` | `accounts.User` | ForeignKey | `SET_NULL` |

### Entrantes vers `Employee`

| App | Modèle | Champ | Type | `on_delete` | Accès inverse |
|---|---|---|---|---|---|
| wallet | `TopUp` | `user` | OneToOne | `CASCADE` | `employee.topup` |
| transactions | `QRCode` | `employee` | ForeignKey | `CASCADE` | `employee.qrcode_set` |
| transactions | `Transaction` | `employee` | ForeignKey | `PROTECT` | `employee.transaction_set` |

---

## Place dans le flux métier

```
        ADMIN                    SALARIÉ                  PARTENAIRE
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

`wallet` est donc **la seule source d'entrée d'argent** et le détenteur unique du solde.
Toute opération financière doit passer par une lecture/écriture de `Employee.balance`.

---

## Requêtes types

```python
from wallet.models import Employee, TopUp
from django.db.models import Sum

# Solde d'un salarié
Employee.objects.get(user__username='jdupont').balance

# Salariés d'un employeur donné, sans requête N+1 sur user
Employee.objects.filter(employer='ACME').select_related('user')

# Total crédité sur la plateforme
TopUp.objects.aggregate(total=Sum('amount'))['total']

# Historique d'un salarié (après passage en ForeignKey + related_name='topups')
employee.topups.order_by('-created_at')

# Salariés à découvert (anomalie à surveiller)
Employee.objects.filter(balance__lt=0)
```

---

## Points d'attention

| Sujet | Constat | Recommandation |
|---|---|---|
| `TopUp.user` OneToOne | Un seul crédit possible par salarié | Passer en `ForeignKey` (voir plus haut) |
| `TopUp.__str__` | `AttributeError` | Corriger le nom du champ |
| Solde négatif | Aucune contrainte | `CheckConstraint(check=Q(balance__gte=0))` |
| Montant négatif ou nul | Aucune contrainte | `CheckConstraint(check=Q(amount__gt=0))` |
| Solde non recalculable | `balance` est dénormalisé, sans vérification | Ajouter une commande de réconciliation `Σ TopUp − Σ Transaction` |
| Concurrence | Deux crédits simultanés peuvent s'écraser | `select_for_update()` systématique |
| Pas d'`ordering` | Historique non trié par défaut | `class Meta: ordering = ['-created_at']` sur `TopUp` |
| Admin vide | Modèles absents de `/admin/` | Enregistrer `Employee` et `TopUp` |

### Contraintes recommandées

```python
class Employee(models.Model):
    ...
    class Meta:
        verbose_name = 'salarié'
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
