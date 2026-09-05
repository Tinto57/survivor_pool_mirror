from rest_framework import status

from partners.models import Category, Partner, PartnerDecision
from .base import BaseAPITestCase


class CategoryTests(BaseAPITestCase):
    def test_categories_are_public(self):
        response = self.client.get("/api/v1/categories/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_can_create_category(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post("/api/v1/categories/", {"name": "Sport"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_non_admin_cannot_create_category(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.post("/api/v1/categories/", {"name": "Sport"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_cannot_create_category(self):
        response = self.client.post("/api/v1/categories/", {"name": "Sport"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_duplicate_category_name_is_rejected(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/v1/categories/", {"name": self.category.name}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_category_name_is_rejected(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post("/api/v1/categories/", {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PartnerListTests(BaseAPITestCase):
    def test_anonymous_cannot_list_partners(self):
        response = self.client.get("/api/v1/partners/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_employee_only_sees_active_partners(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.get("/api/v1/partners/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        statuses = {p["status"] for p in response.data["results"]}
        self.assertEqual(statuses, {"active"})

    def test_partner_only_sees_active_partners(self):
        self.client.force_authenticate(user=self.partner_user)
        response = self.client.get("/api/v1/partners/")
        names = {p["business_name"] for p in response.data["results"]}
        self.assertIn("Café Actif", names)
        self.assertNotIn("Café En Attente", names)
        self.assertNotIn("Café Suspendu", names)

    def test_admin_sees_all_statuses_by_default(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/v1/partners/")
        statuses = {p["status"] for p in response.data["results"]}
        self.assertIn("pending", statuses)
        self.assertIn("suspended", statuses)

    def test_admin_can_filter_by_status(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/v1/partners/?status=pending")
        statuses = {p["status"] for p in response.data["results"]}
        self.assertEqual(statuses, {"pending"})

    def test_status_filter_is_ignored_for_non_admin(self):
        # Le paramètre `status` n'est appliqué que pour un admin : pour tout
        # autre rôle, seuls les partenaires actifs sont renvoyés quel que
        # soit le filtre demandé.
        self.client.force_authenticate(user=self.employee_user)
        with_filter = self.client.get("/api/v1/partners/?status=pending")
        without_filter = self.client.get("/api/v1/partners/")
        self.assertEqual(
            {p["id"] for p in with_filter.data["results"]},
            {p["id"] for p in without_filter.data["results"]},
        )
        statuses = {p["status"] for p in with_filter.data["results"]}
        self.assertEqual(statuses, {"active"})

    def test_filter_by_category(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(f"/api/v1/partners/?category={self.category.id}")
        for partner in response.data["results"]:
            self.assertEqual(partner["category"]["id"], self.category.id)

    def test_search_by_business_name(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.get("/api/v1/partners/?q=Actif 2")
        names = {p["business_name"] for p in response.data["results"]}
        self.assertEqual(names, {"Café Actif 2"})

    def test_search_is_case_insensitive(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.get("/api/v1/partners/?q=café actif")
        self.assertGreaterEqual(len(response.data["results"]), 1)

    def test_search_no_match_returns_empty(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.get("/api/v1/partners/?q=doesnotexist")
        self.assertEqual(response.data["results"], [])


class PartnerMeTests(BaseAPITestCase):
    def test_me_returns_own_partner_profile_regardless_of_status(self):
        self.client.force_authenticate(user=self.pending_partner_user)
        response = self.client.get("/api/v1/partners/me/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "pending")

    def test_me_404_when_not_a_partner(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.get("/api/v1/partners/me/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_me_requires_authentication(self):
        response = self.client.get("/api/v1/partners/me/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class SinglePartnerTests(BaseAPITestCase):
    def test_active_partner_visible_to_any_authenticated_user(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.get(f"/api/v1/partners/{self.partner.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_pending_partner_not_visible_to_others(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.get(f"/api/v1/partners/{self.pending_partner.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_pending_partner_visible_to_owner(self):
        self.client.force_authenticate(user=self.pending_partner_user)
        response = self.client.get(f"/api/v1/partners/{self.pending_partner.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_pending_partner_visible_to_admin(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(f"/api/v1/partners/{self.pending_partner.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unknown_partner_is_404(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.get("/api/v1/partners/999999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_anonymous_cannot_view_partner(self):
        response = self.client.get(f"/api/v1/partners/{self.partner.id}/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_owner_can_update_own_partner(self):
        self.client.force_authenticate(user=self.partner_user)
        response = self.client.patch(
            f"/api/v1/partners/{self.partner.id}/",
            {"business_name": "Nouveau Nom"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.partner.refresh_from_db()
        self.assertEqual(self.partner.business_name, "Nouveau Nom")

    def test_other_partner_cannot_update(self):
        self.client.force_authenticate(user=self.other_partner_user)
        response = self.client.patch(
            f"/api/v1/partners/{self.partner.id}/",
            {"business_name": "Hacked"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_update_any_partner(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            f"/api/v1/partners/{self.partner.id}/",
            {"business_name": "Renommé Par Admin"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_patch_cannot_change_status_directly(self):
        self.client.force_authenticate(user=self.partner_user)
        response = self.client.patch(
            f"/api/v1/partners/{self.partner.id}/",
            {"status": "suspended"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.partner.refresh_from_db()
        self.assertEqual(self.partner.status, "active")

    def test_patch_invalid_category_is_rejected(self):
        self.client.force_authenticate(user=self.partner_user)
        response = self.client.patch(
            f"/api/v1/partners/{self.partner.id}/",
            {"category": 999999},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_put_not_allowed(self):
        self.client.force_authenticate(user=self.partner_user)
        response = self.client.put(
            f"/api/v1/partners/{self.partner.id}/", {"business_name": "x"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_not_allowed(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(f"/api/v1/partners/{self.partner.id}/")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class PartnerDecisionTests(BaseAPITestCase):
    def test_admin_can_accept_pending_partner(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            f"/api/v1/partners/{self.pending_partner.id}/decision/",
            {"decision": "accepted"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.pending_partner.refresh_from_db()
        self.assertEqual(self.pending_partner.status, "active")
        self.assertEqual(response.data["agent"], "admin_user")

    def test_admin_can_reject_pending_partner_with_reason(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            f"/api/v1/partners/{self.pending_partner.id}/decision/",
            {"decision": "rejected", "reason": "SIREN invalide"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.pending_partner.refresh_from_db()
        self.assertEqual(self.pending_partner.status, "closed")

    def test_reject_without_reason_is_rejected(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            f"/api/v1/partners/{self.pending_partner.id}/decision/",
            {"decision": "rejected"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.pending_partner.refresh_from_db()
        self.assertEqual(self.pending_partner.status, "pending")

    def test_reject_with_blank_reason_is_rejected(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            f"/api/v1/partners/{self.pending_partner.id}/decision/",
            {"decision": "rejected", "reason": ""},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_decision_value_is_rejected(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            f"/api/v1/partners/{self.pending_partner.id}/decision/",
            {"decision": "maybe"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_decide_already_active_partner(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            f"/api/v1/partners/{self.partner.id}/decision/",
            {"decision": "accepted"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_decide_already_closed_partner(self):
        self.pending_partner.status = "closed"
        self.pending_partner.save(update_fields=["status"])
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            f"/api/v1/partners/{self.pending_partner.id}/decision/",
            {"decision": "accepted"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unknown_partner_decision_is_404(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/v1/partners/999999/decision/",
            {"decision": "accepted"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_non_admin_cannot_decide(self):
        self.client.force_authenticate(user=self.partner_user)
        response = self.client.post(
            f"/api/v1/partners/{self.pending_partner.id}/decision/",
            {"decision": "accepted"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_cannot_decide(self):
        response = self.client.post(
            f"/api/v1/partners/{self.pending_partner.id}/decision/",
            {"decision": "accepted"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PartnerDecisionsListTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.decision = PartnerDecision.objects.create(
            partner=self.pending_partner,
            decision="rejected",
            reason="Test",
            agent=self.admin,
        )

    def test_owner_can_view_own_decisions(self):
        self.client.force_authenticate(user=self.pending_partner_user)
        response = self.client.get(f"/api/v1/partners/{self.pending_partner.id}/decisions/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_other_partner_cannot_view_decisions(self):
        self.client.force_authenticate(user=self.partner_user)
        response = self.client.get(f"/api/v1/partners/{self.pending_partner.id}/decisions/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_view_any_decisions(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(f"/api/v1/partners/{self.pending_partner.id}/decisions/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unknown_partner_decisions_is_404(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/v1/partners/999999/decisions/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_anonymous_cannot_view_decisions(self):
        response = self.client.get(f"/api/v1/partners/{self.pending_partner.id}/decisions/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_agent_is_null_after_agent_account_deleted(self):
        self.admin.delete()
        self.client.force_authenticate(user=self.pending_partner_user)
        response = self.client.get(f"/api/v1/partners/{self.pending_partner.id}/decisions/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data["results"][0]["agent"])
