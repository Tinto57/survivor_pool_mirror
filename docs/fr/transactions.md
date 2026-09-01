# App `transactions`

> 🇬🇧 English version: [../en/transactions.md](../en/transactions.md)

## Rôle

`transactions` implémente le **mécanisme de paiement** : un salarié génère un QR code
d'un montant donné, un partenaire le scanne, une transaction est enregistrée.

C'est l'app la plus sensible du projet : elle touche à l'argent, à la concurrence et à
l'auditabilité.

Fichier source : [backend/transactions/models.py](../../backend/transactions/models.py)

---

## Modèle `QRCode`

Jeton de paiement **à usage unique et à durée de vie limitée**.

```python
class QRCode(models.Model):
    employee   = models.ForeignKey('wallet.Employee', on_delete=models.CASCADE)
    token      = models.CharField(max_length=100, unique=True, editable=False)
    amount     = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(editable=False)
    is_used    = models.BooleanField(default=False)
```

### Table : `transactions_qrcode`

| Champ | Type SQL | Contraintes | Description |
|---|---|---|---|
| `id` | `BIGINT` | PK, auto | Identifiant technique |
| `employee_id` | `BIGINT` | FK → `wallet_employee.id`, NOT NULL | Salarié émetteur |
| `token` | `VARCHAR(100)` | **UNIQUE**, NOT NULL, `editable=False` | Secret encodé dans le QR |
| `amount` | `DECIMAL(10,2)` | NOT NULL | Montant du paiement en euros |
| `created_at` | `DATETIME` | NOT NULL, `auto_now_add` | Date de génération |
| `expires_at` | `DATETIME` | NOT NULL, `editable=False` | Date d'expiration (création + 30 min) |
| `is_used` | `BOOL` | NOT NULL, défaut `False` | Passe à `True` une fois scanné |

### Génération automatique — surcharge de `save()`

```python
def save(self, *args, **kwargs):
    if not self.token:
        self.token = secrets.token_urlsafe(32)
    if not self.expires_at:
        self.expires_at = timezone.now() + timedelta(minutes=30)
    super().save(*args, **kwargs)
```

Deux valeurs sont calculées à la première sauvegarde uniquement (les tests `if not ...`
garantissent qu'un `save()` ultérieur ne régénère rien) :

- **`token`** — `secrets.token_urlsafe(32)` produit 32 octets d'aléa
  cryptographiquement sûr, encodés en base64 URL-safe → **43 caractères**, ~256 bits
  d'entropie. Le module `secrets` (et non `random`) est le bon choix : il s'appuie sur le
  CSPRNG du système, ce qui rend le token imprévisible même en connaissant les
  précédents. `unique=True` pose un index qui garantit l'absence de collision et rend la
  recherche par token instantanée.
- **`expires_at`** — fenêtre fixe de **30 minutes** codée en dur. À externaliser en
  réglage (`settings.QRCODE_TTL_MINUTES`) pour pouvoir l'ajuster sans migration.

> `editable=False` sur `token` et `expires_at` les exclut des `ModelForm` et de l'admin :
> ils ne peuvent être renseignés que par le code.

### Méthode `is_expired()`

```python
def is_expired(self):
    return timezone.now() > self.expires_at
```

Calculée en Python, elle ne peut pas être utilisée dans un `filter()`. Pour requêter les
QR codes expirés en base :

```python
QRCode.objects.filter(expires_at__lt=timezone.now())
```

### Validité d'un QR code

Un QR est encaissable si et seulement si :

```python
qr.is_used is False  and  not qr.is_expired()
```

Aucune contrainte de base ne l'impose : c'est au code de validation de le vérifier, sous
verrou.

### Représentation

```python
def __str__(self):
    return f"QR {self.token[:8]}... ({self.amount}€)"
```

Le token est tronqué — bonne pratique, il ne doit pas fuiter dans les logs ou l'admin.

---

## Modèle `Transaction`

Enregistrement **définitif** d'un paiement effectué.

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

### Table : `transactions_transaction`

| Champ | Type SQL | Contraintes | Description |
|---|---|---|---|
| `id` | `BIGINT` | PK, auto | Identifiant technique |
| `qr_code_id` | `BIGINT` | FK → `transactions_qrcode.id`, **UNIQUE**, NOT NULL | QR consommé |
| `employee_id` | `BIGINT` | FK → `wallet_employee.id`, NOT NULL | Salarié payeur |
| `partner_id` | `BIGINT` | FK → `partners_partner.id`, NOT NULL | Commerçant encaisseur |
| `amount` | `DECIMAL(10,2)` | NOT NULL | Montant effectivement débité |
| `validated_at` | `DATETIME` | NOT NULL, `auto_now_add` | Horodatage de l'encaissement |
| `is_cancelled` | `BOOL` | NOT NULL, défaut `False` | Transaction annulée |
| `cancelled_at` | `DATETIME` | NULL | Horodatage de l'annulation |
| `cancelled_by_id` | `BIGINT` | FK → `accounts_user.id`, NULL | Auteur de l'annulation |
| `cancellation_reason` | `TEXT` | NOT NULL, `blank=True` | Motif de l'annulation |

### `qr_code` en `OneToOneField` — la protection anti-double-dépense

C'est le point de conception le plus important de l'app.

`OneToOneField` pose une contrainte `UNIQUE` sur `qr_code_id` : **la base elle-même
refuse qu'un même QR code donne lieu à deux transactions**. Si deux requêtes tentent
d'encaisser le même token en parallèle, la seconde lève une `IntegrityError` au lieu de
débiter le salarié deux fois.

C'est une garantie bien plus solide que le seul booléen `is_used`, qui est vulnérable à
une condition de course entre la lecture et l'écriture. Les deux se complètent :
`is_used` sert au chemin nominal (message d'erreur propre), la contrainte `UNIQUE` sert
de filet de sécurité en cas de concurrence.

### `PROTECT` partout — l'intégrité comptable

`qr_code`, `employee` et `partner` sont tous en `on_delete=PROTECT`. Toute tentative de
supprimer un salarié, un partenaire ou un QR code ayant servi lève une `ProtectedError`.

**Conséquence pratique** : les entités impliquées dans une transaction sont
définitivement non supprimables. Le retrait d'un acteur se fait par désactivation
(`User.is_active = False`, `Partner.status = 'closed'`), jamais par suppression. C'est
volontaire — une transaction orpheline serait un trou dans la comptabilité.

### `amount` dupliqué depuis `QRCode`

`Transaction.amount` recopie `QRCode.amount`. Cette dénormalisation est **voulue** : elle
fige le montant au moment de l'encaissement. Même si le QR code était modifié après coup,
la transaction garde la valeur réellement débitée. C'est le principe de l'immuabilité des
écritures comptables.

### Le bloc d'annulation

Quatre champs forment un ensemble cohérent :

| Champ | Rôle |
|---|---|
| `is_cancelled` | Drapeau, filtrable et indexable |
| `cancelled_at` | Quand |
| `cancelled_by` | Qui (`SET_NULL` : la trace survit à la suppression de l'admin) |
| `cancellation_reason` | Pourquoi |

**Une transaction annulée n'est jamais supprimée** : la ligne reste, marquée. C'est
l'équivalent d'une écriture d'extourne en comptabilité — on n'efface pas, on contre-passe.

Ces quatre champs doivent rester cohérents entre eux (les trois derniers renseignés si et
seulement si `is_cancelled` est vrai). Rien ne le garantit aujourd'hui — voir *Points
d'attention*.

### `related_name='cancelled_transactions'`

Nécessaire pour éviter une collision : `Transaction` n'a pas d'autre FK vers `User`, mais
le nom explicite rend l'intention lisible côté `User` :

```python
admin_user.cancelled_transactions.all()
```

### Représentation

```python
def __str__(self):
    return f"{self.amount}€ - {self.employee.user.username} → {self.partner.business_name}"
```

Traverse `employee → user` et `partner` : **trois requêtes** par affichage. Toujours
utiliser `select_related('employee__user', 'partner')` sur une liste.

---

## Relations

### Sortantes

| Champ | Vers | Type | `on_delete` |
|---|---|---|---|
| `QRCode.employee` | `wallet.Employee` | ForeignKey | `CASCADE` |
| `Transaction.qr_code` | `transactions.QRCode` | OneToOne | `PROTECT` |
| `Transaction.employee` | `wallet.Employee` | ForeignKey | `PROTECT` |
| `Transaction.partner` | `partners.Partner` | ForeignKey | `PROTECT` |
| `Transaction.cancelled_by` | `accounts.User` | ForeignKey | `SET_NULL` |

Aucune relation entrante : `transactions` est le point terminal du graphe.

> **Contradiction à noter** : `QRCode.employee` est en `CASCADE` alors que
> `Transaction.qr_code` est en `PROTECT`. Supprimer un `Employee` tenterait de supprimer
> ses QR codes en cascade, ce que le `PROTECT` de `Transaction` bloquera dès qu'un QR a
> été consommé. Le résultat est correct (la suppression échoue) mais l'intention serait
> plus claire avec `PROTECT` sur `QRCode.employee` aussi.

---

## Flux d'encaissement complet

```
┌─ SALARIÉ ─────────────────────────────────────────────────────────┐
│ 1. Demande un QR de 12€                                           │
│    vérification : employee.balance >= 12                          │
│    QRCode.objects.create(employee=..., amount=12)                 │
│      → token   = secrets.token_urlsafe(32)                        │
│      → expires_at = now + 30 min                                  │
│      → is_used = False                                            │
│ 2. Le token est encodé en image QR (lib `qrcode`) et affiché      │
└───────────────────────────────────────────────────────────────────┘
                              │  scan
                              ▼
┌─ PARTENAIRE ──────────────────────────────────────────────────────┐
│ 3. POST du token                                                  │
│ 4. Vérifications, sous transaction atomique et verrou :           │
│      qr.is_used is False                                          │
│      qr.is_expired() is False                                     │
│      partner.status == 'active'                                   │
│      employee.balance >= qr.amount                                │
│ 5. Écritures :                                                    │
│      Transaction.objects.create(qr_code=qr, employee=...,         │
│                                 partner=..., amount=qr.amount)    │
│      qr.is_used = True                    ; qr.save()             │
│      employee.balance -= qr.amount        ; employee.save()       │
└───────────────────────────────────────────────────────────────────┘
```

### Implémentation de référence

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
            raise ValueError("QR code déjà utilisé")
        if qr.is_expired():
            raise ValueError("QR code expiré")
        if partner.status != 'active':
            raise ValueError("Partenaire non actif")

        employee = Employee.objects.select_for_update().get(pk=qr.employee_id)
        if employee.balance < qr.amount:
            raise ValueError("Solde insuffisant")

        try:
            tx = Transaction.objects.create(
                qr_code=qr, employee=employee, partner=partner, amount=qr.amount,
            )
        except IntegrityError:          # filet anti-double-dépense
            raise ValueError("QR code déjà encaissé")

        qr.is_used = True
        qr.save(update_fields=['is_used'])

        employee.balance -= qr.amount
        employee.save(update_fields=['balance'])

        return tx
```

Les deux `select_for_update()` sont indispensables : ils sérialisent les scans
concurrents du même QR code et les débits concurrents du même solde.

> `select_for_update()` est **sans effet sur SQLite** (pas de verrouillage de ligne).
> C'est une raison de plus de basculer sur PostgreSQL avant la mise en production ; d'ici
> là, la contrainte `UNIQUE` sur `qr_code` reste la vraie protection.

---

## Flux d'annulation

```python
with transaction.atomic():
    tx = Transaction.objects.select_for_update().get(pk=pk)
    if tx.is_cancelled:
        raise ValueError("Transaction déjà annulée")

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

Le QR code reste `is_used = True` : il n'est pas réutilisable après annulation. Le
salarié doit en générer un nouveau.

---

## Requêtes types

```python
from transactions.models import QRCode, Transaction
from django.db.models import Sum, Count
from django.utils import timezone

# QR codes actuellement valides d'un salarié
QRCode.objects.filter(employee=employee, is_used=False,
                      expires_at__gt=timezone.now())

# Nettoyage des QR périmés jamais utilisés
QRCode.objects.filter(is_used=False, expires_at__lt=timezone.now()).delete()

# Historique d'un salarié, sans requête N+1
(Transaction.objects
    .filter(employee=employee, is_cancelled=False)
    .select_related('partner')
    .order_by('-validated_at'))

# Chiffre d'affaires d'un partenaire
(Transaction.objects
    .filter(partner=partner, is_cancelled=False)
    .aggregate(total=Sum('amount'), nb=Count('id')))

# Transactions annulées avec leur auteur
(Transaction.objects
    .filter(is_cancelled=True)
    .select_related('cancelled_by', 'employee__user', 'partner'))

# Volume du jour
(Transaction.objects
    .filter(validated_at__date=timezone.now().date(), is_cancelled=False)
    .aggregate(total=Sum('amount')))
```

---

## Points d'attention

| Sujet | Constat | Recommandation |
|---|---|---|
| Aucun index métier | `is_used`, `expires_at`, `validated_at`, `is_cancelled` non indexés | Ajouter des `db_index` / `Meta.indexes` |
| TTL codé en dur | 30 min dans `save()` | `settings.QRCODE_TTL_MINUTES` |
| Montants non contraints | `amount` peut être ≤ 0 | `CheckConstraint(amount__gt=0)` |
| Cohérence de l'annulation | `is_cancelled=False` avec `cancelled_at` renseigné est possible | `CheckConstraint` combiné |
| Débit non automatique | Aucun signal ne touche `balance` | Encapsuler dans un service, comme ci-dessus |
| `CASCADE` vs `PROTECT` | Incohérent entre `QRCode.employee` et `Transaction` | Uniformiser en `PROTECT` |
| Pas de purge | Les QR expirés s'accumulent | Tâche planifiée de nettoyage |
| `select_for_update` sur SQLite | Sans effet | Passer à PostgreSQL |
| Pas d'`ordering` | Historiques non triés par défaut | `Meta.ordering = ['-validated_at']` |
| Admin vide | Modèles absents de `/admin/` | Enregistrer les deux modèles en lecture seule |

### Contraintes et index recommandés

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
