# App `partners`

> 🇬🇧 English version: [../en/partners.md](../en/partners.md)

## Rôle

`partners` gère les **commerçants partenaires** : leur fiche d'entreprise, leur
géolocalisation, leur statut d'agrément, et le **journal des décisions** prises par les
agents administratifs sur leur dossier.

Un partenaire est l'entité qui encaisse : c'est lui qui scanne les QR codes des salariés
(voir [`transactions`](transactions.md)).

Fichier source : [backend/partners/models.py](../../backend/partners/models.py)

---

## Modèle `Partner`

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

### Table : `partners_partner`

| Champ | Type SQL | Contraintes | Description |
|---|---|---|---|
| `id` | `BIGINT` | PK, auto | Identifiant technique |
| `status` | `VARCHAR(20)` | NOT NULL, `choices` | État du dossier (voir ci-dessous) |
| `user_id` | `BIGINT` | FK → `accounts_user.id`, **UNIQUE**, NOT NULL | Compte de connexion du commerçant |
| `business_name` | `VARCHAR(200)` | NOT NULL | Raison sociale / enseigne |
| `siren` | `VARCHAR(9)` | NOT NULL, validateur `^\d{9}$` | Numéro SIREN de l'entreprise |
| `business_purpose` | `TEXT` | NOT NULL | Objet social / description de l'activité |
| `address` | `VARCHAR(300)` | NOT NULL | Adresse postale complète |
| `latitude` | `DECIMAL(9,6)` | NULL | Latitude WGS84 |
| `longitude` | `DECIMAL(9,6)` | NULL | Longitude WGS84 |
| `is_featured` | `BOOL` | NOT NULL, défaut `False` | Mise en avant dans l'application |
| `registered_at` | `DATETIME` | NOT NULL, `auto_now_add` | Date de dépôt du dossier |

### Le champ `siren`

Le SIREN identifie une entreprise française sur 9 chiffres. Il est stocké en
`CharField(max_length=9)` et **non** en entier : un SIREN peut commencer par un zéro,
qu'un `IntegerField` perdrait.

```python
validators=[RegexValidator(r'^\d{9}$', 'Le SIREN doit contenir exactement 9 chiffres.')]
```

> ⚠️ Un `validator` Django n'est **pas** une contrainte SQL. Il ne s'applique que lors
> d'un `full_clean()` — donc via un `ModelForm`, l'admin ou un serializer DRF. Un
> `Partner.objects.create(siren='abc')` en shell passe sans erreur.
>
> ⚠️ `siren` n'est pas `unique=True` : deux partenaires peuvent aujourd'hui déclarer la
> même entreprise. À corriger si un SIREN doit correspondre à un seul compte.
>
> Le validateur ne vérifie pas non plus la **clé de Luhn**, qui permettrait de rejeter un
> numéro syntaxiquement correct mais inexistant.

### Géolocalisation

`latitude` / `longitude` sont en `DECIMAL(9,6)` :

- 6 décimales ≈ **11 cm de précision**, largement suffisant pour situer un commerce ;
- 9 chiffres au total → 3 chiffres avant la virgule, ce qui couvre `-180.000000` à
  `180.000000` (longitude) et `-90` à `90` (latitude) ;
- `null=True, blank=True` : les coordonnées sont facultatives (dossier déposé sans
  géocodage). `null` = valeur absente en base, `blank` = champ non requis dans les
  formulaires — les deux sont nécessaires.

Ces champs servent à la recherche « partenaires autour de moi ». Avec SQLite/PostgreSQL
sans PostGIS, le calcul de distance doit se faire côté application (formule de
haversine) ou via un `SELECT` avec calcul trigonométrique. Le passage à PostGIS +
`django.contrib.gis` (`PointField`) est la solution propre si cette fonctionnalité
devient centrale.

### Les statuts

| Valeur | Libellé | Signification | Le partenaire peut-il encaisser ? |
|---|---|---|---|
| `pending` | En attente | Dossier déposé, pas encore examiné | ❌ |
| `active` | Actif | Dossier accepté, partenaire opérationnel | ✅ |
| `suspended` | Suspendu | Suspension temporaire (litige, contrôle) | ❌ |
| `closed` | Clôturé | Fin de partenariat, définitif | ❌ |

Transitions attendues :

```
   pending ──accepted──► active ◄──────► suspended
      │                    │                  │
      └──rejected──────────┴──────────────────┴──► closed
```

> Ces transitions ne sont **pas** contraintes par le modèle : `status` est un simple
> `CharField`. La logique de transition doit être implémentée dans la couche métier.
> `status` n'a pas non plus de `default` — il faudrait ajouter `default='pending'`, un
> nouveau dossier étant nécessairement en attente.

### `is_featured`

Booléen de mise en avant (carrousel, tête de liste). Purement éditorial, sans effet sur
les droits. Un partenaire `is_featured=True` mais `status != 'active'` ne devrait jamais
être affiché : le filtrage doit combiner les deux conditions.

### Représentation

```python
def __str__(self):
    return self.business_name
```

---

## Modèle `PartnerDecision`

Journal d'audit des décisions d'agrément. **Une ligne par décision**, jamais modifiée ni
supprimée : c'est l'historique complet du traitement du dossier.

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

### Table : `partners_partnerdecision`

| Champ | Type SQL | Contraintes | Description |
|---|---|---|---|
| `id` | `BIGINT` | PK, auto | Identifiant technique |
| `partner_id` | `BIGINT` | FK → `partners_partner.id`, NOT NULL | Dossier concerné |
| `decision` | `VARCHAR(20)` | NOT NULL, `choices` | `accepted` ou `rejected` |
| `reason` | `TEXT` | NOT NULL, `blank=True` | Motivation (obligatoire en cas de refus, par convention) |
| `agent_id` | `BIGINT` | FK → `accounts_user.id`, NULL | Agent ayant statué |
| `created_at` | `DATETIME` | NOT NULL, `auto_now_add` | Horodatage de la décision |

### Détails

- **`related_name='decisions'`** : l'accès inverse est `partner.decisions.all()` et non
  `partner.partnerdecision_set.all()`.
- **`on_delete=CASCADE` sur `partner`** : les décisions n'ont aucun sens sans le dossier,
  elles disparaissent avec lui.
- **`on_delete=SET_NULL` sur `agent`** : la décision reste tracée même si l'agent quitte
  l'entreprise. C'est la règle d'or d'un journal d'audit : ne jamais perdre l'événement.
- **`reason` avec `blank=True`** : facultatif au niveau formulaire. En base la colonne est
  `NOT NULL` et contiendra une chaîne vide — Django n'utilise jamais `NULL` pour les
  champs texte (`null=True` sur un `TextField` créerait deux façons de dire « vide »).

### Relation avec `Partner.status`

`PartnerDecision` est **l'historique**, `Partner.status` est **l'état courant**. Les deux
sont dénormalisés l'un par rapport à l'autre : rien ne les synchronise automatiquement.

```python
from django.db import transaction

with transaction.atomic():
    PartnerDecision.objects.create(
        partner=partner, decision='accepted', reason='Dossier conforme', agent=request.user,
    )
    partner.status = 'active'
    partner.save(update_fields=['status'])
```

Le statut courant peut toujours être recalculé depuis la dernière décision :

```python
last = partner.decisions.order_by('-created_at').first()
```

### Représentation

```python
def __str__(self):
    return f"{self.partner.business_name} - {self.decision} ({self.created_at:%d/%m/%Y})"
```

Traverse `partner` → requête supplémentaire. Utiliser
`PartnerDecision.objects.select_related('partner', 'agent')` dans les listes.

---

## Relations

### Sortantes

| Champ | Vers | Type | `on_delete` |
|---|---|---|---|
| `Partner.user` | `accounts.User` | OneToOne | `CASCADE` |
| `PartnerDecision.partner` | `partners.Partner` | ForeignKey (`related_name='decisions'`) | `CASCADE` |
| `PartnerDecision.agent` | `accounts.User` | ForeignKey | `SET_NULL` |

### Entrantes

| App | Modèle | Champ | Type | `on_delete` |
|---|---|---|---|---|
| partners | `PartnerDecision` | `partner` | ForeignKey | `CASCADE` |
| transactions | `Transaction` | `partner` | ForeignKey | `PROTECT` |

Le `PROTECT` de `Transaction` signifie qu'**un partenaire ayant encaissé au moins une
fois ne peut plus être supprimé** : il faut le passer en `status='closed'`.

---

## Cycle de vie d'un dossier

```
1. Le commerçant s'inscrit
   User(role='partner')  +  Partner(status='pending')

2. Un agent examine le dossier
   PartnerDecision(decision='accepted'|'rejected', reason, agent)

3. Mise à jour de l'état courant
   accepted  →  Partner.status = 'active'    → peut encaisser
   rejected  →  Partner.status = 'closed'    → ne peut pas encaisser

4. Vie du partenariat
   suspension temporaire →  status = 'suspended'  (+ nouvelle PartnerDecision)
   reprise               →  status = 'active'
   fin                   →  status = 'closed'
```

---

## Requêtes types

```python
from partners.models import Partner, PartnerDecision

# Partenaires visibles dans l'application
Partner.objects.filter(status='active')

# Mise en avant (le filtre sur status reste indispensable)
Partner.objects.filter(status='active', is_featured=True)

# Dossiers à traiter, du plus ancien au plus récent
Partner.objects.filter(status='pending').order_by('registered_at')

# Partenaires géolocalisés uniquement
Partner.objects.filter(status='active', latitude__isnull=False, longitude__isnull=False)

# Historique complet d'un dossier
partner.decisions.select_related('agent').order_by('-created_at')

# Activité d'un agent
PartnerDecision.objects.filter(agent=user).select_related('partner')

# Dernière décision par dossier
Partner.objects.prefetch_related('decisions')
```

---

## Points d'attention

| Sujet | Constat | Recommandation |
|---|---|---|
| `siren` non unique | Doublons d'entreprises possibles | `unique=True` |
| `siren` non validé en base | Le `RegexValidator` est ignoré hors `full_clean()` | Valider dans le serializer, ou ajouter un `CheckConstraint` |
| Clé de Luhn | Non vérifiée | Ajouter un validateur métier |
| `status` sans défaut | Chaîne vide possible à la création | `default='pending'` |
| Transitions libres | On peut passer de `closed` à `active` sans décision | Machine à états applicative |
| Pas d'index sur `status` | Le filtre le plus fréquent fait un scan complet | `db_index=True` |
| `decision` sans `pending` | Les `DECISION_CHOICES` n'ont que 2 valeurs terminales | Cohérent : l'absence de décision = absence de ligne |
| Pas d'`ordering` | Historique non trié | `Meta.ordering = ['-created_at']` |
| `Partner.status` désynchronisable | Aucun lien automatique avec les décisions | Encapsuler dans une méthode `partner.apply_decision(...)` |
| Admin vide | Modèles absents de `/admin/` | Enregistrer les deux modèles |

### Améliorations recommandées

```python
class Partner(models.Model):
    status = models.CharField(choices=STATUS_CHOICE, max_length=20,
                              default='pending', db_index=True)
    siren  = models.CharField(max_length=9, unique=True, validators=[...])
    ...
    class Meta:
        ordering = ['business_name']
        verbose_name = 'partenaire'

class PartnerDecision(models.Model):
    ...
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'décision partenaire'
```
