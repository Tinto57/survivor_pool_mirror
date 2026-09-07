# Déclaration d'accessibilité — Ticket Tout (CartePro)

Démonstrateur technique, ne constitue pas un service public en exploitation — simulation, aucune valeur réelle ne circule.
État établi le 4 septembre 2026, sur le code réellement déployé (pas sur une maquette).

## 1. État de conformité

Le présent démonstrateur est **partiellement conforme** au RGAA version 4.1.

Aucun audit RGAA complet, outillé et mené selon la méthodologie officielle (échantillon de
pages, grille des 106 critères, tests avec technologies d'assistance) n'a été réalisé par
un tiers. Annoncer un taux de conformité chiffré serait donc une affirmation non vérifiée —
précisément le type de fiche recopiée que nous voulons éviter. Cette déclaration liste ce
qui a été corrigé, sur quelle base, et ce qui reste hors de portée d'une revue de code seule.

## 2. Résultats des tests

Un état des lieux interne a été mené sur le code en fonctionnement le 4 septembre 2026,
puis les manques identifiés ont été corrigés le jour même. Le détail :

**Corrigé lors de cette revue :**
- Lien d'évitement (« Aller au contenu ») ajouté en tout premier élément focusable de
  chaque page, ciblant un repère `#main-content` posé sur le `<main>` de toutes les pages
  (`frontend/app/components/SkipLink/`, `frontend/app/global.css`)
- Indicateur de focus clavier visible généralisé (`outline` 3px sur tout élément
  interactif qui n'a pas déjà son propre style de focus)
- Les 10 messages d'erreur du site portent désormais `role="alert"` pour être annoncés
  immédiatement par un lecteur d'écran (connexion, inscription, catalogue, tableau de bord,
  registre, historique, réglages, accueil salarié)
- Icônes décoratives (`Mail`, `Lock`, `Eye`, `User`, `Store`, `MapPin`, `FileText`,
  `Check`, `X`, `Loader2`, `AlertCircle`, flèche d'historique) marquées `aria-hidden`
  pour ne plus être lues en double avec le texte qui les accompagne
- Parcours d'inscription (3 étapes) : progression désormais portée par une liste
  ordonnée avec `aria-current="step"` et un texte masqué (« Étape 2 sur 3 (en cours) »)
  au lieu de trois pastilles uniquement visuelles
- Critères de robustesse du mot de passe : l'état conforme/non conforme de chaque règle,
  jusque-là visible seulement par la couleur et une icône, est maintenant aussi annoncé
  en texte (« (respecté) » / « (non respecté) »)
- Suggestions d'adresse (inscription partenaire) : la liste, auparavant sélectionnable
  uniquement à la souris (`onMouseDown` sur un `<li>`), repose maintenant sur de vrais
  `<button>` au clavier, avec `role="listbox"`/`role="option"` et une zone `aria-live`
  pour annoncer le résultat de la recherche d'adresse
- Résultats du catalogue (recherche et filtre par catégorie) annoncés via `aria-live`
  quand ils changent
- Barre de navigation principale nommée (`aria-label="Navigation principale"`)

**Déjà en place avant cette revue :**
- `lang="fr"` déclaré globalement
- Un repère `<main>` sur l'intégralité des pages (porté soit par le composant `Page`
  partagé, soit posé à la main sur les pages de connexion/inscription/accueil)
- Contrastes de texte relevés à 4,5:1 minimum sur fond blanc et sur fond `--bg`
  (`--text-soft` et `--success` ont été recalculés à cet effet, cf. commit
  « Raise text-soft and success colors to meet WCAG AA contrast »)
- QR code de simulation porteur d'un `title` explicite
- Formulaires de connexion et d'inscription entièrement étiquetés (`label`/`htmlFor`)

**Non vérifiable par une revue de code, reste à faire avant mise en ligne publique :**
- Aucun test réalisé avec un lecteur d'écran réel (NVDA, JAWS ou VoiceOver) — la
  correction ci-dessus repose sur la connaissance des règles RGAA, pas sur une écoute
  effective du rendu
- Aucun audit outillé (axe, Lighthouse) exécuté sur l'application qui tourne
- Navigation clavier non éprouvée de bout en bout sur un parcours complet (connexion →
  catalogue → historique)
- Comportement en zoom 200 % et en reflow non vérifié visuellement

## 3. Contenus non accessibles

| Contenu / page | État | Détail |
|---|---|---|
| Ensemble du site | Corrigé sous réserve de test | Lien d'évitement, focus visible, `aria-live`, `role="alert"` ajoutés sans validation par un test utilisateur ou un outil d'audit |
| Écrans non encore développés (QR, validation partenaire, dashboard partenaire) | Non applicable | Ces écrans n'existent pas dans le code ; rien à corriger tant qu'ils ne sont pas construits |

Aucune dérogation pour charge disproportionnée n'est invoquée : le chantier est traité,
pas écarté.

## 4. Établissement de la présente déclaration

- **Technologies utilisées :** Next.js / React, CSS Modules
- **Agents utilisateurs et technologies d'assistance testés :** aucun test formalisé à ce
  jour — point bloquant à traiter avant toute mise en ligne publique
- **Outils d'audit utilisés :** aucun outil automatisé ; revue de code exhaustive des 11
  pages de l'application (composants partagés inclus) le 4 septembre 2026
- **Pages de l'échantillon :** l'intégralité des pages existantes a été revue

## 5. Retour d'information et contact

Si vous n'arrivez pas à accéder à un contenu ou à un service de ce démonstrateur, vous
pouvez contacter le responsable du dispositif pour être orienté vers une solution
alternative accessible. *(Coordonnées à compléter par le responsable du dispositif avant publication.)*

## 6. Voies de recours

Si vous constatez un défaut d'accessibilité vous empêchant d'accéder à un contenu, vous
pouvez adresser vos doléances ou une demande de saisine aux services du Défenseur des
droits, selon les modalités prévues par le RGAA.

---

**Engagement :** les corrections listées en section 2 ont été faites sur le code, pas
seulement documentées. Elles restent cependant non éprouvées par un test réel avec
technologie d'assistance ni par un outil d'audit — c'est ce qui sépare aujourd'hui ce
démonstrateur d'une conformité déclarée avec un taux chiffré. Cette déclaration sera mise
à jour dès qu'un audit outillé et un test utilisateur auront eu lieu.
