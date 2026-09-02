# Mention "Simulation" — état des lieux

Suivi de la demande de Florine Pontaillac (RGPD) : afficher une mention "Simulation" visible
(pas un astérisque) partout où un montant apparaît dans l'application. Ce document liste,
pour chaque emplacement demandé, ce qui est fait et ce qui reste à faire ou à justifier.

## Fait

| Emplacement | Implémentation | Fichier(s) |
|---|---|---|
| Écran de solde | Badge `SimulationBadge` à côté du libellé "Solde Ticket Tout" et sur les stats "Crédité"/"Dépensé ce mois-ci" | `frontend/app/components/BalanceCard/BalanceCard.tsx` |
| Historique des transactions | Badge sur le titre de page + sur "Reçu au total"/"Dépensé au total" | `frontend/app/historique/page.tsx` |
| Titres de pages | Prop `simulation` ajoutée au composant `Page`, réutilisable sur tout futur écran | `frontend/app/components/Page/Page.tsx` |
| Écran d'accueil employé | Badge dans le bandeau supérieur, à côté du solde affiché | `frontend/app/employee/page.tsx` |

Le composant `SimulationBadge` (`frontend/app/components/SimulationBadge/`) est centralisé :
toute nouvelle mention doit le réutiliser plutôt que recréer un badge ad hoc.

## Pas fait — techniquement impossible actuellement

Ces emplacements sont demandés par Florine mais **n'existent pas encore dans l'application** :
la fonctionnalité elle-même n'est pas développée, il n'y a donc rien à annoter pour l'instant.

| Emplacement demandé | État réel de la fonctionnalité | Justification |
|---|---|---|
| Écran de génération du QR code | Non implémenté — bouton "Payer" désactivé, libellé "Bientôt" (`BalanceCard.tsx`) | Aucun montant n'est encore affiché à cet endroit ; le badge sera ajouté dès le développement de l'écran |
| Écran de validation côté partenaire | Non implémenté — page `/partner` affiche "arrivent bientôt" | Idem |
| Tableau de bord financier du partenaire | Non implémenté — même page stub | Idem |
| Tableau de bord national | Non implémenté — page `/admin` affiche "arrivent bientôt" | Idem |
| Messages d'erreur citant un montant | Aucun message d'erreur de ce type n'existe dans le code actuel (aucun endpoint d'encaissement n'est encore branché) | Rien à annoter tant que ces messages n'existent pas |
| Documents/exports générés par l'app | Aucune génération de PDF/CSV/reçu n'existe, ni côté frontend ni côté backend | Rien à annoter tant que cette fonctionnalité n'existe pas |

**Engagement :** chacun de ces emplacements devra intégrer `SimulationBadge` (ou une variante
adaptée au format, ex. PDF) au moment de son développement — ce n'est pas une exemption
définitive, seulement un report tant que la fonctionnalité sous-jacente n'existe pas.

## Reste à faire (indépendant du code)

- [ ] Prendre une capture d'écran par emplacement listé ci-dessus dans "Fait", sur l'application
      qui tourne réellement (pas une maquette).
- [ ] Joindre ce document + les captures en annexe du livrable transmis à Florine.
