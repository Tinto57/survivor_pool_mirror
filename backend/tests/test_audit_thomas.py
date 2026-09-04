from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from rest_framework import status
from rest_framework.test import APITestCase

from partners.models import Category, Partner
from transactions.models import Transaction
from wallet.models import Employee

User = get_user_model()


class AuditIntegrityTestCase(APITestCase):
    def setUp(self):
        cache.clear()

        self.user_emp = User.objects.create_user(
            username="emp_dupont", email="dupont@test.fr", password="password123", role="employee"
        )
        self.employee = Employee.objects.create(user=self.user_emp, balance=Decimal("50.00"))

        self.user_partner = User.objects.create_user(
            username="resto_delice", email="contact@delice.fr", password="password123", role="partner"
        )
        self.category = Category.objects.create(name="Restauration")
        self.partner = Partner.objects.create(
            user=self.user_partner,
            business_name="Le Délice",
            siren="123456789",
            category=self.category,
            status="active",
        )

    ## Test 1
    def test_01_transaction_immutability(self):
        tx = Transaction.objects.create(
            token="audit_token_immutability",
            employee=self.employee,
            partner=self.partner,
            amount=Decimal("15.00"),
        )

        tx.amount = Decimal("30.00")
        with self.assertRaises(ValidationError):
            tx.save()

        with self.assertRaises(ValidationError):
            tx.delete()

        tx.refresh_from_db()
        self.assertEqual(tx.amount, Decimal("15.00"))
        self.assertTrue(Transaction.objects.filter(id=tx.id).exists())

    ## Test 2
    def test_02_employee_balance_never_negative_constraint(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.employee.balance = Decimal("-10.00")
                self.employee.save()

        self.employee.refresh_from_db()
        self.assertEqual(self.employee.balance, Decimal("50.00"))

    ## Test 3
    def test_03_payment_intent_idempotency_on_replay(self):
        token = "qr_unique_test_token_123"
        amount = Decimal("20.00")

        cache.set(
            f"PaymentIntent:{token}",
            {"employee_id": self.employee.id, "amount": str(amount)},
            timeout=300,
        )

        self.client.force_authenticate(user=self.user_partner)
        url = f"/api/v1/payments/{token}/"

        response_1 = self.client.post(url)
        print("\n[DEBUG 404 RESPONSE]:", response_1.status_code, response_1.data)
        self.assertEqual(response_1.status_code, status.HTTP_200_OK)
        tx_id_1 = response_1.data["id"]

        self.employee.refresh_from_db()
        self.assertEqual(self.employee.balance, Decimal("30.00"))

        response_2 = self.client.post(url)
        self.assertEqual(response_2.status_code, status.HTTP_200_OK)

        tx_id_2 = response_2.data["id"]
        self.assertEqual(tx_id_1, tx_id_2, "Le rejeu doit renvoyer exactement la même transaction")
        self.assertEqual(
            Transaction.objects.filter(token=token).count(),
            1,
            "Il ne doit exister qu'une seule écriture comptable en base",
        )

        self.employee.refresh_from_db()
        self.assertEqual(self.employee.balance, Decimal("30.00"))
