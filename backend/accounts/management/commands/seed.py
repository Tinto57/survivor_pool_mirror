import csv
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import random
import secrets

from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import User
from partners.models import Category, Partner
from transactions.models import QRCode, Transaction
from wallet.models import Employee, TopUp


class Command(BaseCommand):
    help = "Seed déterministe CartePro conforme au cahier des charges (50 salariés, 12 partenaires, 200 tx, CSV)."

    def handle(self, *args, **options):
        random.seed(42)
        date_ref = datetime(2026, 6, 1, 8, 0, 0, tzinfo=timezone.utc)
        total_seconds = 90 * 24 * 3600

        partners_raw = [
            ("Le Bistrot du Palais", "Restauration", "12 Rue de Rivoli, 75001 Paris", "123456781"),
            ("Brasserie Bellecour", "Restauration", "15 Place Bellecour, 69002 Lyon", "123456782"),
            ("La Table Lorraine", "Restauration", "4 Place Stanislas, 54000 Nancy", "123456783"),
            ("Boulangerie Saint-Honoré", "Alimentation", "8 Rue Saint-Honoré, 75001 Paris", "123456784"),
            ("Les Halles Gourmandes", "Alimentation", "22 Rue Sainte-Catherine, 33000 Bordeaux", "123456785"),
            ("Primeur & Terroir", "Alimentation", "5 Rue Mercière, 69002 Lyon", "123456786"),
            ("VéloCité Express", "Mobilité", "30 Boulevard Saint-Germain, 75005 Paris", "123456787"),
            ("Éco-Trott Services", "Mobilité", "18 Rue Saint-Dizier, 54000 Nancy", "123456788"),
            ("Navette & Bus Région", "Mobilité", "10 Cours Lafayette, 69003 Lyon", "123456789"),
            ("Librairie Gutenberg", "Culture & Loisirs", "40 Boulevard Saint-Michel, 75005 Paris", "123456790"),
            ("Cinéma Lumière", "Culture & Loisirs", "7 Place Gambetta, 33000 Bordeaux", "123456791"),
            ("Espace Bloc & Grimpe", "Sport & Bien-être", "12 Rue de la Commanderie, 54000 Nancy", "123456792"),
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
            QRCode.objects.all().delete()
            TopUp.objects.all().delete()
            Employee.objects.all().delete()
            Partner.objects.all().delete()
            Category.objects.all().delete()
            User.objects.filter(role__in=['employee', 'partner']).delete()

            categories_map = {}
            for _, cat_name, _, _ in partners_raw:
                if cat_name not in categories_map:
                    cat_obj, _ = Category.objects.get_or_create(name=cat_name)
                    categories_map[cat_name] = cat_obj

            partners_by_id = {}
            for p_id, (name, cat_name, addr, siren_val) in enumerate(partners_raw, start=1):
                p_user = User.objects.create_user(
                    username=f"partner_{p_id}",
                    email=f"partner{p_id}@cartepro.gouv.fr",
                    password="password123",
                    role="partner"
                )
                partner_obj = Partner.objects.create(
                    id=p_id,
                    user=p_user,
                    business_name=name,
                    category=categories_map[cat_name],
                    siren=siren_val,
                    business_purpose="Partenaire conventionné CartePro",
                    address=addr,
                    status="active"
                )
                partners_by_id[p_id] = partner_obj

            employee_state = {}
            for emp_id in range(1, 51):
                if emp_id == 1:
                    init_cents = 15000
                elif emp_id == 2:
                    init_cents = 12000
                elif emp_id == 3:
                    init_cents = 10000
                elif emp_id == 4:
                    init_cents = 8000
                elif emp_id == 5:
                    init_cents = 9500
                else:
                    init_cents = random.randint(25000, 45000)

                u = User.objects.create_user(
                    username=f"emp_{emp_id}",
                    first_name=first_names[emp_id - 1],
                    last_name=last_names[emp_id - 1],
                    email=f"{first_names[emp_id - 1].lower()}.{last_names[emp_id - 1].lower()}_{emp_id}@cartepro.gouv.fr",
                    password="password123",
                    role="employee"
                )
                emp_obj = Employee.objects.create(
                    id=emp_id,
                    user=u,
                    employer="Ministère du Job et Bonheur",
                    balance=Decimal(init_cents) / Decimal(100)
                )

                employee_state[emp_id] = {
                    "obj": emp_obj,
                    "balance_cents": init_cents
                }

            timestamps = sorted(random.sample(range(3600, total_seconds - 3600), 200))
            
            assignments = [
                # (150 €) -> 45 + 55 + 50 = 150 € -> reste 0 € -> refus 22 €
                (10, 1, 4500), (40, 1, 5500), (80, 1, 5000), (150, 1, 2200),
                # (120 €) -> 60 + 40 + 20 = 120 € -> reste 0 € -> refus 15 €
                (15, 2, 6000), (60, 2, 4000), (110, 2, 2000), (160, 2, 1500),
                # (100 €) -> 55 + 45 = 100 € -> reste 0 € -> refus 18 €
                (25, 3, 5500), (90, 3, 4500), (170, 3, 1800),
                # (80 €) -> 45 + 32.50 = 77.50 € -> reste 2,50 € -> refus 12 €
                (30, 4, 4500), (100, 4, 3250), (180, 4, 1200),
                # (95 €) -> 50 + 41.20 = 91.20 € -> reste 3,80 € -> refus 14 €
                (35, 5, 5000), (120, 5, 4120), (190, 5, 1400),
                # refus
                (45, 6, 6000), (195, 6, 50000),
            ]

            reserved_indices = {item[0] for item in assignments}
            for idx in range(200):
                if idx not in reserved_indices:
                    emp_id = random.randint(7, 50)
                    amount = random.randint(850, 4500)
                    assignments.append((idx, emp_id, amount))

            assignments.sort(key=lambda x: x[0])

            csv_rows = []
            valid_transactions_to_create = []
            tx_id = 1

            for idx, emp_id, amount in assignments:
                tx_date = date_ref + timedelta(seconds=timestamps[idx])
                iso_date = tx_date.strftime("%Y-%m-%dT%H:%M:%SZ")
                partner_id = random.randint(1, 12)

                if employee_state[emp_id]["balance_cents"] >= amount:
                    employee_state[emp_id]["balance_cents"] -= amount
                    status = "VALIDATED"
                    valid_transactions_to_create.append(Transaction(
                        id=tx_id,
                        token=secrets.token_urlsafe(32),
                        employee=employee_state[emp_id]["obj"],
                        partner=partners_by_id[partner_id],
                        amount=Decimal(amount) / Decimal(100),
                        validated_at=tx_date,
                        is_cancelled=False
                    ))
                else:
                    status = "REJECTED_INSUFFICIENT_FUNDS"

                csv_rows.append({
                    "id": tx_id,
                    "date_iso8601": iso_date,
                    "employee_id": emp_id,
                    "partner_id": partner_id,
                    "amount_cents": amount,
                    "status": status
                })
                tx_id += 1

            Transaction.objects.bulk_create(valid_transactions_to_create)

            for tx_obj in valid_transactions_to_create:
                Transaction.objects.filter(id=tx_obj.id).update(validated_at=tx_obj.validated_at)

            for emp_id, data in employee_state.items():
                Employee.objects.filter(id=emp_id).update(
                    balance=Decimal(data["balance_cents"]) / Decimal(100)
                )

        csv_fields = ["id", "date_iso8601", "employee_id", "partner_id", "amount_cents", "status"]
        with open("transactions.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=csv_fields, delimiter=";")
            writer.writeheader()
            writer.writerows(csv_rows)

        zero_balances = [e for e, d in employee_state.items() if d["balance_cents"] == 0]
        under_five = [e for e, d in employee_state.items() if 0 < d["balance_cents"] < 500]
        rejected_count = sum(1 for r in csv_rows if r["status"] == "REJECTED_INSUFFICIENT_FUNDS")

        self.stdout.write(self.style.SUCCESS(
            f"Seed exécuté avec succès !\n"
            f"- Transactions CSV : {len(csv_rows)} (dont {rejected_count} refusées)\n"
            f"- Transactions en base : {Transaction.objects.count()}\n"
            f"- Salariés à 0 € : {len(zero_balances)} (IDs: {zero_balances})\n"
            f"- Salariés < 5 € : {len(under_five)} (IDs: {under_five})\n"
            f"- Fichier exporté : transactions.csv"
        ))
