from rest_framework import status

from partners.models import MinisterSpotlight

from .base import BaseAPITestCase


class MinisterSpotlightTestCase(BaseAPITestCase):
    def test_public_can_read_active_spotlight_without_auth(self):
        MinisterSpotlight.objects.create(
            partner=self.partner, message="Un café qui a du cœur.", is_active=True
        )
        response = self.client.get("/api/v1/ministre/coup-de-coeur/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["partner"]["id"], self.partner.id)

    def test_public_read_without_active_spotlight_is_no_content(self):
        response = self.client.get("/api/v1/ministre/coup-de-coeur/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_public_list_shows_all_entries_without_click_count(self):
        MinisterSpotlight.objects.create(
            partner=self.partner, message="Actif.", is_active=True, click_count=42
        )
        MinisterSpotlight.objects.create(
            partner=self.other_partner, message="Archivé.", is_active=False, click_count=9
        )
        response = self.client.get("/api/v1/ministre/coup-de-coeur/toutes/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        self.assertNotIn("click_count", response.data["results"][0])

    def test_public_click_increments_counter_without_auth(self):
        spotlight = MinisterSpotlight.objects.create(
            partner=self.partner, message="Un café qui a du cœur.", is_active=True
        )
        response = self.client.post("/api/v1/ministre/coup-de-coeur/click/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        spotlight.refresh_from_db()
        self.assertEqual(spotlight.click_count, 1)

    def test_click_without_active_spotlight_is_not_found(self):
        response = self.client.post("/api/v1/ministre/coup-de-coeur/click/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_publish_deactivates_previous_active(self):
        old = MinisterSpotlight.objects.create(
            partner=self.partner, message="Ancien.", is_active=True
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/v1/ministre/coup-de-coeur/historique/",
            {"partner": self.other_partner.id, "message": "Nouveau coup de cœur."},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        old.refresh_from_db()
        self.assertFalse(old.is_active)

    def test_employee_cannot_publish_spotlight(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.post(
            "/api/v1/ministre/coup-de-coeur/historique/",
            {"partner": self.partner.id, "message": "Nouveau coup de cœur."},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_republish_reactivates_without_resetting_clicks(self):
        old = MinisterSpotlight.objects.create(
            partner=self.partner, message="Ancien.", is_active=False, click_count=7
        )
        current = MinisterSpotlight.objects.create(
            partner=self.other_partner, message="Actuel.", is_active=True
        )

        self.client.force_authenticate(user=self.admin)
        response = self.client.post(f"/api/v1/ministre/coup-de-coeur/{old.id}/republier/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        old.refresh_from_db()
        current.refresh_from_db()
        self.assertTrue(old.is_active)
        self.assertEqual(old.click_count, 7)
        self.assertFalse(current.is_active)
