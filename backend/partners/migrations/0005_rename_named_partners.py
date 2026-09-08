# Régularisation du point 1 (rollback v1.0) : substitue en base tout partenaire qui
# porterait encore l'une des 4 anciennes enseignes nominatives par la nouvelle
# enseigne fictive correspondante. N'a d'effet que si une telle ligne existe déjà —
# ce n'était le cas dans aucun environnement connu (les 4 noms n'existaient que dans
# les données de démo frontend), mais cette migration protège tout déploiement où
# elle aurait été créée entre-temps.
#
# Aucune contrainte de clé étrangère n'est désactivée : il s'agit d'une simple mise
# à jour de champs sur la ligne existante (UPDATE), jamais d'une suppression — les
# transactions PROTECT rattachées au partenaire restent intactes et continuent de
# pointer vers le même identifiant, désormais sous sa nouvelle identité.

from django.db import migrations

SUBSTITUTIONS = [
    {
        "old_name": "Poney Dream 78",
        "business_name": "Le Comptoir du Midi",
        "category": "Restauration",
        "business_purpose": (
            "Restaurant de quartier, cuisine du Sud-Ouest et menu du jour. Formule "
            "salariés avec addition fractionnable en fin de service."
        ),
        "siren": "267914530",
        "address": "6 rue du Taur, 31000 Toulouse",
    },
    {
        "old_name": "KostumParty",
        "business_name": "Épicerie Sainte-Claire",
        "category": "Alimentation",
        "business_purpose": (
            "Épicerie de proximité, produits frais et locaux. Livraison possible "
            "sur le quartier en fin de journée."
        ),
        "siren": "398215647",
        "address": "14 rue Sainte-Claire, 38000 Grenoble",
    },
    {
        "old_name": "Glaces Artisanales Corrèze",
        "business_name": "Librairie Vasseur",
        "category": "Culture",
        "business_purpose": (
            "Librairie indépendante généraliste, littérature et bandes dessinées. "
            "Rencontres d'auteurs organisées un samedi par mois."
        ),
        "siren": "145762893",
        "address": "9 rue des Trois Cailloux, 80000 Amiens",
    },
    {
        "old_name": "Chapelier Fontaine",
        "business_name": "Pharmacie du Parc",
        "category": "Santé",
        "business_purpose": (
            "Pharmacie de quartier, conseil officinal et service de garde. Bilan de "
            "médication proposé sur rendez-vous."
        ),
        "siren": "683920174",
        "address": "2 place du Parc, 69006 Lyon",
    },
]


def rename_named_partners(apps, schema_editor):
    Partner = apps.get_model('partners', 'Partner')
    Category = apps.get_model('partners', 'Category')

    for entry in SUBSTITUTIONS:
        partner = Partner.objects.filter(business_name=entry["old_name"]).first()
        if partner is None:
            continue

        category, _ = Category.objects.get_or_create(name=entry["category"])

        partner.business_name = entry["business_name"]
        partner.category = category
        partner.business_purpose = entry["business_purpose"]
        partner.siren = entry["siren"]
        partner.address = entry["address"]
        partner.save()


class Migration(migrations.Migration):

    dependencies = [
        ('partners', '0004_ministerspotlight'),
    ]

    operations = [
        migrations.RunPython(rename_named_partners, migrations.RunPython.noop),
    ]
