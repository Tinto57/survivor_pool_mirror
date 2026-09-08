# Checklist — CartePro : retour à la v1.0 (échéance mardi 12h00)

Instruction du cabinet (Thomas Vignal, 07/09/2026) : retour à la version 1.0 du cahier des charges (31 août). Le document annoté du 1er septembre n'a plus de valeur contractuelle.

## 0. Avant de commencer

- [ ] Créer une branche dédiée (`cartepro/rollback-v1` ou équivalent), ne rien faire sur `main`/`employee-page` directement
- [ ] Ne pas réécrire l'historique git existant — les commits restent tels quels, seule la suite du journal compte

## 1. Partenaires : remplacement des 4 enseignes nominatives

- [ ] Identifier tous les emplacements où les 4 partenaires actuels apparaissent : base de données, `seed.py`/`seed_demo.py`, fixtures de tests (`tests/base.py` et tests unitaires), captures d'écran, brand book, exemples dans le schéma OpenAPI (`drf-spectacular`), vidéo de démo
- [ ] Créer les 6 nouvelles enseignes fictives avec leurs catégories exactes :
  - [ ] Le Comptoir du Midi — Restauration
  - [ ] Épicerie Sainte-Claire — Alimentation
  - [ ] Librairie Vasseur — Culture
  - [ ] Pharmacie du Parc — Santé
  - [ ] Transports Régionaux Unifiés — Mobilité
  - [ ] Sport Loisirs Aubagne — Sport
  - [ ] Vérifier/créer les catégories manquantes en base (`Category`) si elles n'existent pas déjà
- [ ] **Décider du sort des transactions existantes qui référencent les 4 anciens partenaires** (elles sont immuables, `partner_id` en FK PROTECT — impossible de simplement supprimer les lignes) :
  - [ ] Choisir une option : substitution vers une nouvelle enseigne / partenaire archivé mais conservé (statut dédié, masqué du catalogue) / contre-écriture de régularisation
  - [ ] Écrire les 2 lignes de justification du choix pour Thomas
  - [ ] **Ne pas** désactiver la contrainte de clé étrangère pour faire passer le script (explicitement refusé)
  - [ ] Implémenter la migration de données correspondante

## 2. Suppression : Coup de cœur du Ministre

- [ ] Confirmer si des clics ont été enregistrés en base (compter `click_count` avant suppression) et le noter pour la réponse à Thomas
- [ ] Supprimer côté backend : modèle `MinisterSpotlight`, migration de retrait, serializers, vues (public + admin), routes (`ministre/coup-de-coeur/*`)
- [ ] Supprimer côté frontend : composants `MinisterSpotlight`/`MinisterSpotlightDetail`, page admin `/admin/coup-de-coeur`, page publique `/coup-de-coeur`, lien dans `AdminNav`, appel dans `employee/page.tsx`, fonctions `catalog.ts`/`api.ts` associées, entrée `BARE_ROUTES` dans `AppShell`
- [ ] Supprimer les tests associés (`test_minister_features.py` côté spotlight)
- [ ] Vérifier qu'aucune trace ne subsiste dans les seeds/fixtures de démo

## 3. Suppression : découvert de -150 €

- [ ] Revenir à un solde plancher à 0 : restaurer `MinValueValidator(0)` + `CheckConstraint(balance__gte=0)` sur `Employee.balance`, migration correspondante
- [ ] Restaurer le refus de débit avec message explicite quand le solde est insuffisant (`PaymentIntentDetailView`, `CounterEntryCreateView`)
- [ ] Retirer l'endpoint `decouvert-total` et son affichage admin
- [ ] Retirer l'affichage/mention du découvert côté frontend (`BalanceCard`, badge « passage en découvert » dans l'historique, `balance_after` si jugé lié — vérifier s'il faut le garder pour d'autres usages ou le retirer aussi)
- [ ] **Écrire le script de migration de régularisation des soldes déjà négatifs** :
  - [ ] Identifier tous les salariés actuellement en négatif
  - [ ] Choisir la méthode (abondement de régularisation à la charge du Ministère / contre-écriture ligne à ligne / autre) et la justifier
  - [ ] Le script doit être **idempotent** (rejouable sans rien casser)
  - [ ] Rédiger la note de 10 lignes : méthode choisie + coût total en euros pour le Ministère
- [ ] Restaurer/adapter les tests d'intégrité liés au solde (`test_audit_thomas.py`, `test_transactions.py`, `test_payments.py`) à leur comportement d'origine (solde jamais négatif)

## 4. Débaptisation : « Ministre » → CartePro

- [ ] Retirer toute mention du nom de travail du Ministre : interface (textes, titres, messages), dépôt (README, docs), branches actives, documents (`docs/fr/*`), jeux de démonstration, métadonnées (titre de page, meta description, `package.json`, etc.)
- [ ] Renommer le dispositif en **CartePro** partout où c'est pertinent (UI, docs, éventuellement noms de variables/routes si le nom du Ministre y apparaît littéralement — sinon inutile de tout renommer techniquement)
- [ ] Ne pas toucher aux anciens messages de commit — seulement mentionner le renommage dans le journal des modifications

## 5. Restauration : circuit de validation partenaires

- [ ] Vérifier que le circuit d'origine (demande → contrôle SIREN/objet social par un agent → décision motivée → traçabilité) est bien intact et n'a pas été court-circuité (a priori inchangé de notre côté, à confirmer)
- [ ] Identifier tous les partenaires activés « en direct » pendant la semaine écoulée sans passer par ce circuit
- [ ] Créer pour chacun une `PartnerDecision` cohérente avec le circuit (motif type « régularisation du 07/09 »)

## 6. Non-régression — ce qui doit continuer à marcher à l'identique

- [ ] Export CSV (`AdminTransactionsCsvExportView` / `export_transactions`) : colonnes et ordre inchangés — comparer avant/après
- [ ] Contrat de `GET /api/v1/employees/{id}/balance/` inchangé (forme de la réponse)
- [ ] Seed déterministe : après migration, tourne toujours sur base vide, produit toujours le même jeu, avec les 6 nouvelles enseignes
- [ ] Tests d'intégrité existants (mardi dernier) toujours au vert après toutes les modifications
- [ ] Faire tourner la suite de tests complète avant envoi

## 7. Livrables pour Thomas (demain 12h00)

- [ ] **Exemple concret** d'un salarié qui était en négatif : les 2-3 lignes de transactions concernées avant migration, les lignes après, et le solde final résultant
- [ ] **Journal des modifications daté** : chaque retrait listé avec son motif et l'identifiant du commit correspondant (sera annexé à la note de la Direction Numérique de mercredi) — être factuel et précis
- [ ] La note de 10 lignes sur le coût de la régularisation des découverts (cf. point 3)
- [ ] Les 2 lignes de justification du choix fait pour les partenaires renommés (cf. point 1)
- [ ] Confirmation écrite à Thomas sur le sort des clics enregistrés sur le Coup de cœur (cf. point 2)
