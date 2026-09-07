from decimal import Decimal

from rest_framework import status

from transactions.models import Transaction
from .base import BaseAPITestCase


class TransactionListTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.payment_tx = Transaction.objects.create(
            token="tx-list-payment",
            transaction_type=Transaction.PAYMENT,
            employee=self.employee,
            partner=self.partner,
            amount=Decimal("10.00"),
        )
        self.other_payment_tx = Transaction.objects.create(
            token="tx-list-payment-other",
            transaction_type=Transaction.PAYMENT,
            employee=self.other_employee,
            partner=self.other_partner,
            amount=Decimal("5.00"),
        )

    def test_admin_sees_all_transactions(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/v1/transactions/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = {t["id"] for t in response.data["results"]}
        self.assertIn(self.payment_tx.id, ids)
        self.assertIn(self.other_payment_tx.id, ids)

    def test_employee_only_sees_own_transactions(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.get("/api/v1/transactions/")
        ids = {t["id"] for t in response.data["results"]}
        self.assertEqual(ids, {self.payment_tx.id})

    def test_partner_only_sees_own_transactions(self):
        self.client.force_authenticate(user=self.other_partner_user)
        response = self.client.get("/api/v1/transactions/")
        ids = {t["id"] for t in response.data["results"]}
        self.assertEqual(ids, {self.other_payment_tx.id})

    def test_anonymous_cannot_list_transactions(self):
        response = self.client.get("/api/v1/transactions/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_with_no_wallet_or_partner_sees_nothing(self):
        # Un compte admin sans fiche salarié ni fiche partenaire n'est pas
        # censé arriver ici (branche admin gérée avant), mais un compte dont
        # le rôle serait mal configuré ne doit renvoyer aucune fuite de données.
        self.admin.role = "employee"
        self.admin.save(update_fields=["role"])
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/v1/transactions/")
        self.assertEqual(response.data["results"], [])


class SingleTransactionTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.tx = Transaction.objects.create(
            token="tx-single",
            transaction_type=Transaction.PAYMENT,
            employee=self.employee,
            partner=self.partner,
            amount=Decimal("10.00"),
        )

    def test_involved_employee_can_view(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.get(f"/api/v1/transactions/{self.tx.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_involved_partner_can_view(self):
        self.client.force_authenticate(user=self.partner_user)
        response = self.client.get(f"/api/v1/transactions/{self.tx.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_uninvolved_employee_cannot_view(self):
        self.client.force_authenticate(user=self.other_employee_user)
        response = self.client.get(f"/api/v1/transactions/{self.tx.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_uninvolved_partner_cannot_view(self):
        self.client.force_authenticate(user=self.other_partner_user)
        response = self.client.get(f"/api/v1/transactions/{self.tx.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_view_any_transaction(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(f"/api/v1/transactions/{self.tx.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unknown_transaction_is_404(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/v1/transactions/999999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_anonymous_cannot_view(self):
        response = self.client.get(f"/api/v1/transactions/{self.tx.id}/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patch_not_allowed(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            f"/api/v1/transactions/{self.tx.id}/", {"amount": "1.00"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_not_allowed(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(f"/api/v1/transactions/{self.tx.id}/")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class AbondmentTests(BaseAPITestCase):
    def test_admin_can_credit_employee(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/v1/transactions/abondments/",
            {"employee": self.employee.id, "amount": "20.00"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["transaction_type"], Transaction.ABONDMENT)
        self.assertIsNone(response.data["partner"])
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.balance, Decimal("120.00"))

    def test_non_admin_cannot_create_abondment(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.post(
            "/api/v1/transactions/abondments/",
            {"employee": self.employee.id, "amount": "20.00"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_cannot_create_abondment(self):
        response = self.client.post(
            "/api/v1/transactions/abondments/",
            {"employee": self.employee.id, "amount": "20.00"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_negative_amount_is_rejected(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/v1/transactions/abondments/",
            {"employee": self.employee.id, "amount": "-5.00"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_zero_amount_is_rejected(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/v1/transactions/abondments/",
            {"employee": self.employee.id, "amount": "0.00"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unknown_employee_is_rejected(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/v1/transactions/abondments/",
            {"employee": 999999, "amount": "20.00"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_employee_is_rejected(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/v1/transactions/abondments/",
            {"amount": "20.00"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_amount_is_rejected(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/v1/transactions/abondments/",
            {"employee": self.employee.id},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_abondment_does_not_require_a_transaction_amount_ceiling(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/v1/transactions/abondments/",
            {"employee": self.employee.id, "amount": "500.00"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class CounterEntryTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.payment_tx = Transaction.objects.create(
            token="tx-counter-payment",
            transaction_type=Transaction.PAYMENT,
            employee=self.employee,
            partner=self.partner,
            amount=Decimal("30.00"),
        )
        self.abondment_tx = Transaction.objects.create(
            transaction_type=Transaction.ABONDMENT,
            employee=self.employee,
            amount=Decimal("15.00"),
        )

    def test_admin_can_counter_a_payment(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            f"/api/v1/transactions/{self.payment_tx.id}/counter-entry/"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["transaction_type"], Transaction.ABONDMENT)
        self.assertEqual(response.data["counter_entry_of"], self.payment_tx.id)
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.balance, Decimal("130.00"))

    def test_admin_can_counter_an_abondment(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            f"/api/v1/transactions/{self.abondment_tx.id}/counter-entry/"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["transaction_type"], Transaction.PAYMENT)
        # L'abondement d'origine n'a pas de partenaire, la contre-écriture
        # (bien que de type PAYMENT) n'en a donc pas non plus.
        self.assertIsNone(response.data["partner"])
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.balance, Decimal("85.00"))

    def test_countering_abondment_with_insufficient_balance_is_rejected(self):
        # Le découvert autorisé va jusqu'à -150€ : au-delà, la contre-écriture doit échouer.
        self.employee.balance = Decimal("-140.00")
        self.employee.save(update_fields=["balance"])
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            f"/api/v1/transactions/{self.abondment_tx.id}/counter-entry/"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.balance, Decimal("-140.00"))

    def test_cannot_counter_twice(self):
        self.client.force_authenticate(user=self.admin)
        first = self.client.post(f"/api/v1/transactions/{self.payment_tx.id}/counter-entry/")
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        second = self.client.post(f"/api/v1/transactions/{self.payment_tx.id}/counter-entry/")
        self.assertEqual(second.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unknown_transaction_is_404(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post("/api/v1/transactions/999999/counter-entry/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_non_admin_cannot_counter(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.post(
            f"/api/v1/transactions/{self.payment_tx.id}/counter-entry/"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_cannot_counter(self):
        response = self.client.post(
            f"/api/v1/transactions/{self.payment_tx.id}/counter-entry/"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_countering_a_counter_entry_is_currently_allowed(self):
        # La vue ne bloque que le fait de contrer une transaction qui a *déjà*
        # une contre-écriture (`hasattr(tx, "counter_entry")`) ; elle ne
        # bloque pas le fait de contrer une contre-écriture elle-même. On
        # peut donc chaîner les contre-écritures (ce qui, ici, ramène le
        # solde à sa valeur de départ) : comportement documenté, pas une
        # garantie explicite du modèle métier.
        self.client.force_authenticate(user=self.admin)
        first = self.client.post(f"/api/v1/transactions/{self.payment_tx.id}/counter-entry/")
        counter_id = first.data["id"]
        second = self.client.post(f"/api/v1/transactions/{counter_id}/counter-entry/")
        self.assertEqual(second.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.data["transaction_type"], Transaction.PAYMENT)
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.balance, Decimal("100.00"))


class AdminTransactionsCsvExportTests(BaseAPITestCase):
    def test_admin_can_export_csv(self):
        Transaction.objects.create(
            token="tx-csv",
            transaction_type=Transaction.PAYMENT,
            employee=self.employee,
            partner=self.partner,
            amount=Decimal("12.34"),
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/v1/admin/transactions.csv/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        self.assertIn("attachment", response["Content-Disposition"])
        content = response.content.decode("utf-8")
        self.assertIn("1234", content)  # amount_cents

    def test_csv_export_does_not_carry_a_mention_column(self):
        Transaction.objects.create(
            token="tx-csv-mention",
            transaction_type=Transaction.PAYMENT,
            employee=self.employee,
            partner=self.partner,
            amount=Decimal("5.00"),
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/v1/admin/transactions.csv/")
        header, row = response.content.decode("utf-8").strip().split("\r\n")
        self.assertNotIn("mention", header.split(";"))
        self.assertNotIn("SIMULATION", row.split(";"))

    def test_export_with_no_transactions_returns_header_only(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/v1/admin/transactions.csv/")
        content = response.content.decode("utf-8")
        lines = [line for line in content.strip().split("\r\n") if line]
        self.assertEqual(len(lines), 1)

    def test_non_admin_cannot_export_csv(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.get("/api/v1/admin/transactions.csv/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_cannot_export_csv(self):
        response = self.client.get("/api/v1/admin/transactions.csv/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
