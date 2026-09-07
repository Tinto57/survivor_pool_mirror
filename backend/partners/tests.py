from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from wallet.models import Employee

from .models import Category, Partner, PartnerDecision

User = get_user_model()

STRONG_PASSWORD = "TicketTout-2026!"


class PartnersApiTests(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Restauration")

        self.admin = User.objects.create_user(username="admin_p", password=STRONG_PASSWORD, role="admin")

        self.employee_user = User.objects.create_user(username="emp_p", password=STRONG_PASSWORD, role="employee")
        Employee.objects.create(user=self.employee_user, employer="Ministère", balance=Decimal("0.00"))

        self.pending_user = User.objects.create_user(username="partner_pending", password=STRONG_PASSWORD, role="partner")
        self.pending_partner = Partner.objects.create(
            user=self.pending_user,
            business_name="Chez Bob",
            siren="123456789",
            business_purpose="Restauration",
            address="1 rue Test",
            category=self.category,
            status="pending",
        )

        self.active_user = User.objects.create_user(username="partner_active", password=STRONG_PASSWORD, role="partner")
        self.active_partner = Partner.objects.create(
            user=self.active_user,
            business_name="Café Actif",
            siren="987654321",
            business_purpose="Café",
            address="2 rue Test",
            category=self.category,
            status="active",
        )

    # --- Categories -------------------------------------------------

    def test_categories_are_public(self):
        response = self.client.get("/api/v1/categories/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["count"], 1)

    def test_only_admin_can_create_category(self):
        response = self.client.post("/api/v1/categories/", {"name": "Mobilité"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.force_authenticate(user=self.employee_user)
        response = self.client.post("/api/v1/categories/", {"name": "Mobilité"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.admin)
        response = self.client.post("/api/v1/categories/", {"name": "Mobilité"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # --- Catalogue ----------------------------------------------------

    def test_employee_only_sees_active_partners(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.get("/api/v1/partners/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [p["id"] for p in response.data["results"]]
        self.assertIn(self.active_partner.id, ids)
        self.assertNotIn(self.pending_partner.id, ids)

    def test_admin_can_filter_by_status(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/v1/partners/?status=pending")
        ids = [p["id"] for p in response.data["results"]]
        self.assertIn(self.pending_partner.id, ids)
        self.assertNotIn(self.active_partner.id, ids)

    def test_owner_can_see_own_pending_partner_but_others_cannot(self):
        self.client.force_authenticate(user=self.pending_user)
        response = self.client.get(f"/api/v1/partners/{self.pending_partner.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=self.employee_user)
        response = self.client.get(f"/api/v1/partners/{self.pending_partner.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_partner_me(self):
        self.client.force_authenticate(user=self.active_user)
        response = self.client.get("/api/v1/partners/me/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.active_partner.id)

    # --- Update ---------------------------------------------------------

    def test_owner_can_update_but_not_status(self):
        self.client.force_authenticate(user=self.active_user)
        response = self.client.patch(
            f"/api/v1/partners/{self.active_partner.id}/",
            {"business_name": "Nouveau nom", "status": "suspended"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.active_partner.refresh_from_db()
        self.assertEqual(self.active_partner.business_name, "Nouveau nom")
        self.assertEqual(self.active_partner.status, "active")

    def test_non_owner_cannot_update(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.patch(
            f"/api/v1/partners/{self.active_partner.id}/",
            {"business_name": "Hack"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --- Decision workflow ------------------------------------------------

    def test_admin_accepts_pending_partner(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            f"/api/v1/partners/{self.pending_partner.id}/decision/",
            {"decision": "accepted"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.pending_partner.refresh_from_db()
        self.assertEqual(self.pending_partner.status, "active")
        self.assertEqual(PartnerDecision.objects.filter(partner=self.pending_partner).count(), 1)

    def test_cannot_decide_twice(self):
        self.client.force_authenticate(user=self.admin)
        self.client.post(f"/api/v1/partners/{self.pending_partner.id}/decision/", {"decision": "accepted"}, format="json")
        response = self.client.post(f"/api/v1/partners/{self.pending_partner.id}/decision/", {"decision": "accepted"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rejection_requires_a_reason(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            f"/api/v1/partners/{self.pending_partner.id}/decision/",
            {"decision": "rejected"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.post(
            f"/api/v1/partners/{self.pending_partner.id}/decision/",
            {"decision": "rejected", "reason": "SIREN invalide"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.pending_partner.refresh_from_db()
        self.assertEqual(self.pending_partner.status, "closed")

    def test_only_admin_can_decide(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.post(
            f"/api/v1/partners/{self.pending_partner.id}/decision/",
            {"decision": "accepted"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_decisions_history_visible_to_owner_and_admin_only(self):
        decision = PartnerDecision.objects.create(
            partner=self.pending_partner, decision="rejected", reason="Test", agent=self.admin
        )

        self.client.force_authenticate(user=self.pending_user)
        response = self.client.get(f"/api/v1/partners/{self.pending_partner.id}/decisions/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], decision.id)

        self.client.force_authenticate(user=self.employee_user)
        response = self.client.get(f"/api/v1/partners/{self.pending_partner.id}/decisions/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_decision_agent_hidden_after_gdpr_dissociation(self):
        decision = PartnerDecision.objects.create(
            partner=self.pending_partner, decision="rejected", reason="Test", agent=None
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(f"/api/v1/partners/{self.pending_partner.id}/decisions/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = next(r for r in response.data["results"] if r["id"] == decision.id)
        self.assertIsNone(result["agent"])
