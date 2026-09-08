# Point 2 — Coup de cœur du Ministre : clics enregistrés et seeds

## Clics enregistrés (pour la réponse à Thomas)

Oui, des clics ont été enregistrés. Sur la base de développement locale
(`db.sqlite3`) au moment de l'audit : 2 publications `MinisterSpotlight`, `5` et `2`
clics respectivement, soit **7 clics au total**. Ce chiffre est celui de
l'environnement local — à revérifier sur la base réelle avant suppression et avant
d'envoyer une confirmation définitive à Thomas (`manage.py shell` :
`MinisterSpotlight.objects.aggregate(Sum('click_count'))`).

## Traces dans les seeds/fixtures de démo

Aucune. `MinisterSpotlight` n'apparaît ni dans `accounts/management/commands/seed.py`
ni dans `seed_demo.py`, ni dans `backend/tests/base.py` : ces fixtures ne créent
jamais de publication. Les seules occurrences du modèle dans le dépôt sont son
propre fichier (`partners/models.py`), les vues/routes/serializers qui l'exposent, sa
migration de création (`0004_ministerspotlight.py`), et les tests dédiés
(`tests/test_minister_features.py`, classe `MinisterSpotlightTestCase`) — tous
concernés par la suppression prévue en #66/#68, pas par ce point.
