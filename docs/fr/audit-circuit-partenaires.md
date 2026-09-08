# Audit — circuit de validation des partenaires

Vérification demandée : le circuit d'origine (demande → contrôle SIREN/objet social
par un agent → décision motivée → traçabilité) est-il intact ?

**Oui, au niveau applicatif.** Le seul point d'entrée qui fait passer un dossier de
`pending` à `active`/`closed` est `POST /partners/{id}/decision/`
(`PartnerDecisionCreateView`, `backend/partners/views.py`) : réservé aux
administrateurs, refuse toute demande déjà traitée, et crée systématiquement une
`PartnerDecision` (agent, motif, date). `PATCH /partners/{id}/` exclut explicitement
le champ `status` (`PartnerUpdateSerializer`) — impossible de l'activer par cette
route.

**Mais le circuit peut être court-circuité hors API.** `Partner` et
`PartnerDecision` sont enregistrés dans l'admin Django
(`partners/admin.py`, `admin.site.register(...)` sans `ModelAdmin` restrictif) : un
compte staff peut y éditer `status` directement, sans passer par la décision motivée.
C'est très probablement ce qui explique les activations "en direct" constatées.

Régularisation : la commande `manage.py regularize_partner_activations` identifie les
partenaires `active` sans `PartnerDecision` acceptée et consigne pour chacun une
décision de régularisation (motif « régularisation du 07/09 »). Idempotente. Sur la
base de développement locale, 2 dossiers concernés : `Café du Ministère` et
`Chapelier E2E` (tous deux créés hors circuit — seed de démo et test e2e).
