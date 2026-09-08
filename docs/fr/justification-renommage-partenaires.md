# Point 1 — partenaires : justification et migration

## Justification du choix (pour Thomas)

Substitution en place : les 4 partenaires nommés gardent leur identifiant mais
changent d'enseigne. Aucune transaction n'est réécrite ni supprimée — seule la
fiche du partenaire change, ce que la contrainte `PROTECT` autorise sans y toucher.

## Contrainte de clé étrangère

Non désactivée, à aucun moment. `Transaction.partner` reste `on_delete=PROTECT`
(inchangé dans `backend/transactions/models.py`). La migration
`partners/migrations/0005_rename_named_partners.py` ne fait que des `UPDATE` sur la
ligne `Partner` existante — aucune suppression, donc la contrainte n'est jamais
sollicitée.

## Migration de données

`partners/migrations/0005_rename_named_partners.py` : si une ligne `Partner` porte
encore l'un des 4 anciens noms (Poney Dream 78, KostumParty, Glaces Artisanales
Corrèze, Chapelier Fontaine), elle est mise à jour vers l'enseigne correspondante
(nom, catégorie, SIREN, adresse). Aucun environnement connu n'avait ces lignes en
base — les 4 noms n'existaient que dans les données de démo frontend (`seed.ts`),
déjà corrigées dans #98 — mais la migration protège tout déploiement où elles
auraient existé entre-temps. Sans effet si la ligne n'existe pas (no-op constaté sur
la base de développement locale).
