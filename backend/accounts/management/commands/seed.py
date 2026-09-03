import csv
from datetime import datetime, timedelta, timezone
import random
from django.core.management.base import BaseCommand
from django.db import transaction

from partners.models import *
from accounts.models import *
from wallet.models import *
from transactions.models import *
from datetime import datetime, timezone

date_ref = datetime(2026, 6, 1, 8, 0, 0, tzinfo=timezone.utc)

class Command(BaseCommand):
    help = "Seed déterministe pour CartePro (50 salariés, 12 partenaires, 200 transactions)"

    def handle(self, *args, **options):
        random.seed(42)
        date_ref = datetime(2026, 6, 1, 8, 0, 0, tzinfo=timezone.utc)
        total_seconds = 90 * 24 * 3600

        partners_data = [
            ("Le Bistrot du Palais", "Restauration", "Île-de-France"),
            ("Brasserie Bellecour", "Restauration", "Auvergne-Rhône-Alpes"),
            ("La Table Lorraine", "Restauration", "Grand Est"),
            ("Boulangerie Saint-Honoré", "Alimentation", "Île-de-France"),
            ("Les Halles Gourmandes", "Alimentation", "Nouvelle-Aquitaine"),
            ("Primeur & Terroir", "Alimentation", "Auvergne-Rhône-Alpes"),
            ("VéloCité Express", "Mobilité", "Île-de-France"),
            ("Éco-Trott Services", "Mobilité", "Grand Est"),
            ("Navette & Bus Région", "Mobilité", "Auvergne-Rhône-Alpes"),
            ("Librairie Gutenberg", "Culture & Loisirs", "Île-de-France"),
            ("Cinéma Lumière", "Culture & Loisirs", "Nouvelle-Aquitaine"),
            ("Espace Bloc & Grimpe", "Sport & Bien-être", "Grand Est"),
        ]

        first_names = [
            "Alexandre", "Camille", "Nicolas", "Sophie", "Thomas", "Julie", "Julien",
            "Élodie", "Pierre", "Léa", "Antoine", "Marie", "Lucas", "Manon", "Hugo",
            "Chloé", "Romain", "Sarah", "Maxime", "Emma", "Paul", "Clara", "Gabriel",
            "Inès", "Louis", "Jade", "Arthur", "Louise", "Jules", "Alice", "Théo",
            "Lina", "Mathis", "Eva", "Nathan", "Rose", "Adam", "Ambre", "Clément",
            "Mia", "Valentin", "Anna", "Florian", "Lucie", "Adrien", "Zoé", "Guillaume",
            "Mila", "Corentin", "Agathe"
        ]

        last_names = [
            "Martin", "Bernard", "Dubois", "Thomas", "Robert", "Richard", "Petit",
            "Durand", "Leroy", "Moreau", "Simon", "Laurent", "Lefebvre", "Michel",
            "Garcia", "David", "Bertrand", "Roux", "Vincent", "Fournier", "Morel",
            "Girard", "Andre", "Lefevre", "Mercier", "Dupont", "Lambert", "Bonnet",
            "Francois", "Martinez", "Legrand", "Garnier", "Faure", "Rousseau", "Blanc",
            "Guerin", "Muller", "Henry", "Roussel", "Nicolas", "Perrin", "Morin",
            "Mathieu", "Clement", "Gauthier", "Dumont", "Lopez", "Fontaine", "Chevalier", "Robin"
        ]

        with transaction.atomic():
            Transaction.objects.all().delete()
            Partner.objects.all().delete()
            Category.objects.all().delete()
            Employee.objects.all().delete()

            categories_map = {}
            unique_categories = sorted(list(set(cat for _, cat, _ in partners_data)))
            for cat_name in unique_categories:
                category_obj, _ = Category.objects.get_or_create(name=cat_name)
                categories_map[cat_name] = category_obj

            partner_objs = []
            for p_id, (p_name, p_cat_name, p_reg) in enumerate(partners_data, start=1):
                partner_objs.append(Partner(
                    id=p_id,
                    name=p_name,
                    category=categories_map[p_cat_name],
                    region=p_reg
                ))
            Partner.objects.bulk_create(partner_objs)
            employees = {}
            for emp_id in range(1, 51):
                if emp_id == 1:
                    init_credit = 15000  # 150,00 € -> finira à 0 €
                elif emp_id == 2:
                    init_credit = 12000  # 120,00 € -> finira à 0 €
                elif emp_id == 3:
                    init_credit = 10000  # 100,00 € -> finira à 0 €
                elif emp_id == 4:
                    init_credit = 8000   # Finira à 2,50 € (< 5 €)
                elif emp_id == 5:
                    init_credit = 9500   # Finira à 3,80 € (< 5 €)
                else:
                    init_credit = random.randint(25000, 45000)

                employees[emp_id] = {
                    "first_name": first_names[emp_id - 1],
                    "last_name": last_names[emp_id - 1],
                    "initial_credit": init_credit,
                    "balance": init_credit,
                }

            timestamps = sorted(random.sample(range(3600, total_seconds - 3600), 200))
            assignments = [
                # Salarié 1 (solde final 0 € + 1 refus)
                (10, 1, 4500), (40, 1, 5500), (80, 1, 5000), (150, 1, 2200),
                # Salarié 2 (solde final 0 € + 1 refus)
                (15, 2, 6000), (60, 2, 4000), (110, 2, 2000), (160, 2, 1500),
                # Salarié 3 (solde final 0 € + 1 refus)
                (25, 3, 5500), (90, 3, 4500), (170, 3, 1800),
                # Salarié 4 (solde final 2,50 € + 1 refus)
                (30, 4, 4500), (100, 4, 3250), (180, 4, 1200),
                # Salarié 5 (solde final 3,80 € + 1 refus)
                (35, 5, 5000), (120, 5, 4120), (190, 5, 1400),
                # Salarié 6 (1 refus supplémentaire)
                (45, 6, 6000), (195, 6, 40000),
            ]

            reserved_indices = {item[0] for item in assignments}
            for idx in range(200):
                if idx not in reserved_indices:
                    assignments.append((idx, random.randint(7, 50), random.randint(850, 4500)))

            assignments.sort(key=lambda x: x[0])

            transaction_records = []
            csv_rows = []
            tx_id = 1

            for idx, emp_id, amount in assignments:
                tx_date = date_ref + timedelta(seconds=timestamps[idx])
                iso_date = tx_date.strftime("%Y-%m-%dT%H:%M:%SZ")
                partner_id = random.randint(1, 12)

                if employees[emp_id]["balance"] >= amount:
                    employees[emp_id]["balance"] -= amount
                    status = "VALIDATED"
                else:
                    status = "REJECTED_INSUFFICIENT_FUNDS"

                transaction_records.append(Transaction(
                    id=tx_id,
                    date_iso8601=iso_date,
                    employee_id=emp_id,
                    partner_id=partner_id,
                    amount_cents=amount,
                    status=status
                ))

                csv_rows.append({
                    "id": tx_id,
                    "date_iso8601": iso_date,
                    "employee_id": emp_id,
                    "partner_id": partner_id,
                    "amount_cents": amount,
                    "status": status
                })
                tx_id += 1

            employee_objs = [
                Employee(
                    id=e_id,
                    first_name=d["first_name"],
                    last_name=d["last_name"],
                    balance_cents=d["balance"]
                )
                for e_id, d in employees.items()
            ]
            Employee.objects.bulk_create(employee_objs)
            Transaction.objects.bulk_create(transaction_records)

        csv_fields = ["id", "date_iso8601", "employee_id", "partner_id", "amount_cents", "status"]
        with open("transactions.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=csv_fields, delimiter=";")
            writer.writeheader()
            writer.writerows(csv_rows)

        self.stdout.write(self.style.SUCCESS("Seed terminé et 'transactions.csv' généré."))
