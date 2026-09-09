# Note — mécanisme d'intégrité du journal d'audit CartePro

## Ce que le journal couvre

Neuf types d'opérations sensibles : création et modification de compte, changement
de rôle, décision sur un partenaire (validation ou refus), abondement d'un solde,
transaction validée, transaction refusée, connexion échouée, action
d'administration. Une table dédiée (`audit_auditlog`), distincte des tables métier.

Le journal démarre à son déploiement, pas avant. Une première ligne explicite
(« genèse ») marque ce point de départ et précise noir sur blanc que rien
d'antérieur n'est couvert — les décisions de partenaires, abondements et migrations
de la semaine passée ne sont pas reconstruits rétroactivement, ce serait fabriquer
un historique. Détail dans `docs/fr/journal-audit-genese.md`.

## Pourquoi on ne peut pas juste faire confiance au code

Une règle applicative (« l'API interdit les modifications ») se contourne par
n'importe qui ayant un accès direct à la base — un shell Django, un client SQL, un
script d'urgence un dimanche soir. La garantie tient donc au niveau du serveur de
base de données lui-même : le rôle utilisé par l'application en fonctionnement
(distinct du rôle utilisé pour les migrations) n'a **techniquement pas le droit**
de modifier, supprimer, ni vider la table d'audit (`REVOKE UPDATE, DELETE,
TRUNCATE`). Un développeur pressé, ou un attaquant avec un accès applicatif, se
heurte à une erreur de permission PostgreSQL, pas à une vérification qu'il suffit de
contourner dans le code.

## Comment une altération malgré tout se détecterait

Chaque ligne porte le SHA-256 de la ligne qui la précède, calculé sur ses champs
dans un ordre documenté (`audit/hashing.py`). Modifier un champ après coup — même
avec un accès direct et privilégié à la base — rend le hash stocké de cette ligne
incohérent avec son contenu réel. Supprimer une ligne casse le maillon entre celle
qui la précédait et celle qui la suivait. Les deux anomalies sont détectables et se
distinguent l'une de l'autre.

## Comment le vérifier, sans faire confiance à la base

```bash
python manage.py export_audit_log --output export.json
python audit/verify_export.py --file export.json --key <clé HMAC>
```

La première commande exporte une période du journal en JSON, signée HMAC-SHA256
(clé lue dans l'environnement, jamais committée). La seconde ne se connecte à
**aucune base de données** — elle ne prend en entrée que le fichier exporté et la
clé. Elle rapporte deux verdicts distincts :

- **Signature du fichier** : le fichier exporté a-t-il été modifié depuis sa
  création ? (intégrité du transport)
- **Chaîne d'intégrité** : les données elles-mêmes ont-elles été altérées avant
  l'export ? Si non conforme, le message désigne précisément l'enregistrement
  concerné (« modification détectée sur l'id X ») ou l'endroit où un enregistrement
  manque (« suppression probable entre l'id X et l'id Y »).

Sortie `VERDICT : CONFORME` ou `VERDICT : NON CONFORME`, code de sortie 0 ou 1 —
exploitable telle quelle dans un contrôle automatisé.

## Ce qui a été vérifié concrètement (pas seulement en théorie)

Sur une instance Postgres réelle : le rôle applicatif restreint peut écrire
normalement (SELECT/INSERT) mais un `UPDATE`, `DELETE` ou `TRUNCATE` direct échoue.
Le rôle propriétaire, lui, peut toujours modifier une ligne — c'est le geste attendu
pour la démonstration devant le contrôleur. Une modification directe en base,
ré-exportée puis vérifiée, désigne exactement la ligne touchée. Une suppression,
ré-exportée puis vérifiée, est rapportée comme une rupture de chaîne, explicitement
différenciée d'une modification.
