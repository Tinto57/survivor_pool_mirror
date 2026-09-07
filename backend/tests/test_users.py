from django.contrib.auth import get_user_model
from rest_framework import status

from partners.models import Partner
from .base import BaseAPITestCase, STRONG_PASSWORD

User = get_user_model()


class UserRegistrationTests(BaseAPITestCase):
    def test_register_employee_success(self):
        response = self.client.post(
            "/api/v1/users/",
            {
                "username": "new_employee",
                "password": STRONG_PASSWORD,
                "role": "employee",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["user"]["role"], "employee")
        self.assertIn("access", response.data["token"])
        self.assertNotIn("partner", response.data)
        self.assertTrue(User.objects.filter(username="new_employee").exists())

    def test_register_partner_success_with_explicit_category(self):
        response = self.client.post(
            "/api/v1/users/",
            {
                "username": "new_partner_explicit",
                "password": STRONG_PASSWORD,
                "role": "partner",
                "partner": {
                    "business_name": "Boulangerie",
                    "siren": "111222333",
                    "business_purpose": "Pain",
                    "address": "3 rue Test",
                    "category": self.other_category.id,
                },
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = Partner.objects.get(user__username="new_partner_explicit")
        self.assertEqual(created.category_id, self.other_category.id)
        self.assertEqual(created.status, "pending")
        self.assertEqual(response.data["partner"]["status"], "pending")

    def test_register_partner_without_partner_data_is_rejected(self):
        response = self.client.post(
            "/api/v1/users/",
            {
                "username": "partner_missing_data",
                "password": STRONG_PASSWORD,
                "role": "partner",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username="partner_missing_data").exists())

    def test_register_rejects_admin_role(self):
        response = self.client.post(
            "/api/v1/users/",
            {
                "username": "sneaky_admin",
                "password": STRONG_PASSWORD,
                "role": "admin",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username="sneaky_admin").exists())

    def test_register_rejects_unknown_role(self):
        response = self.client.post(
            "/api/v1/users/",
            {
                "username": "unknown_role_user",
                "password": STRONG_PASSWORD,
                "role": "superhero",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_partner_invalid_siren_too_short(self):
        response = self.client.post(
            "/api/v1/users/",
            {
                "username": "bad_siren_short",
                "password": STRONG_PASSWORD,
                "role": "partner",
                "partner": {
                    "business_name": "Boulangerie",
                    "siren": "123",
                    "business_purpose": "Pain",
                    "address": "3 rue Test",
                },
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_partner_invalid_siren_non_numeric(self):
        response = self.client.post(
            "/api/v1/users/",
            {
                "username": "bad_siren_alpha",
                "password": STRONG_PASSWORD,
                "role": "partner",
                "partner": {
                    "business_name": "Boulangerie",
                    "siren": "12345678A",
                    "business_purpose": "Pain",
                    "address": "3 rue Test",
                },
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_partner_duplicate_siren_is_currently_not_rejected(self):
        # Gap constaté : `Partner.siren` n'a pas de contrainte `unique` (ni en
        # base, ni au niveau serializer), donc deux partenaires peuvent être
        # créés avec le même SIREN. Ce test documente le comportement actuel,
        # pas une garantie souhaitable.
        response = self.client.post(
            "/api/v1/users/",
            {
                "username": "duplicate_siren",
                "password": STRONG_PASSWORD,
                "role": "partner",
                "partner": {
                    "business_name": "Autre Café",
                    "siren": self.partner.siren,
                    "business_purpose": "Café",
                    "address": "9 rue Test",
                },
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            Partner.objects.filter(siren=self.partner.siren).count(),
            2,
        )

    def test_register_password_too_short_is_rejected(self):
        response = self.client.post(
            "/api/v1/users/",
            {"username": "short_pw_user", "password": "ab1", "role": "employee"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_password_fully_numeric_is_rejected(self):
        response = self.client.post(
            "/api/v1/users/",
            {"username": "numeric_pw_user", "password": "13458762903", "role": "employee"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_password_too_common_is_rejected(self):
        response = self.client.post(
            "/api/v1/users/",
            {"username": "common_pw_user", "password": "password123", "role": "employee"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_password_similar_to_username_is_currently_not_enforced(self):
        # Gap constaté : `UserRegistrationSerializer.validate_password` appelle
        # `validate_password(value)` sans passer l'utilisateur en cours de
        # création, donc `UserAttributeSimilarityValidator` n'a jamais rien à
        # comparer et n'est jamais réellement déclenché à l'inscription. Ce
        # test documente le comportement actuel, pas une garantie souhaitable.
        response = self.client.post(
            "/api/v1/users/",
            {"username": "verysimilaruser", "password": "verysimilaruser42", "role": "employee"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_register_duplicate_username_is_rejected(self):
        response = self.client.post(
            "/api/v1/users/",
            {"username": "employee_one", "password": STRONG_PASSWORD, "role": "employee"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_missing_username_is_rejected(self):
        response = self.client.post(
            "/api/v1/users/",
            {"password": STRONG_PASSWORD, "role": "employee"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_missing_password_is_rejected(self):
        response = self.client.post(
            "/api/v1/users/",
            {"username": "no_password_user", "role": "employee"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_response_never_exposes_password(self):
        response = self.client.post(
            "/api/v1/users/",
            {"username": "no_password_leak", "password": STRONG_PASSWORD, "role": "employee"},
            format="json",
        )
        self.assertNotIn("password", response.data["user"])

    def test_register_is_public_even_when_authenticated(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.post(
            "/api/v1/users/",
            {"username": "still_public", "password": STRONG_PASSWORD, "role": "employee"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class UserListTests(BaseAPITestCase):
    def test_admin_can_list_users(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/v1/users/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertGreaterEqual(response.data["count"], 6)

    def test_employee_cannot_list_users(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.get("/api/v1/users/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_partner_cannot_list_users(self):
        self.client.force_authenticate(user=self.partner_user)
        response = self.client.get("/api/v1/users/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_cannot_list_users(self):
        response = self.client.get("/api/v1/users/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserMeTests(BaseAPITestCase):
    def test_me_returns_authenticated_user(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.get("/api/v1/users/me/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "employee_one")

    def test_me_requires_authentication(self):
        response = self.client.get("/api/v1/users/me/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class SingleUserTests(BaseAPITestCase):
    def test_owner_can_view_own_account(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.get(f"/api/v1/users/{self.employee_user.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_other_user_cannot_view_account(self):
        self.client.force_authenticate(user=self.other_employee_user)
        response = self.client.get(f"/api/v1/users/{self.employee_user.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_view_any_account(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(f"/api/v1/users/{self.employee_user.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unknown_user_is_404_for_admin(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/v1/users/999999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_anonymous_cannot_view_account(self):
        response = self.client.get(f"/api/v1/users/{self.employee_user.id}/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_owner_can_update_own_first_name(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.patch(
            f"/api/v1/users/{self.employee_user.id}/",
            {"first_name": "Alice"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["first_name"], "Alice")

    def test_owner_cannot_escalate_role_via_patch(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.patch(
            f"/api/v1/users/{self.employee_user.id}/",
            {"role": "admin"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.employee_user.refresh_from_db()
        self.assertEqual(self.employee_user.role, "employee")

    def test_owner_cannot_change_username_via_patch(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.patch(
            f"/api/v1/users/{self.employee_user.id}/",
            {"username": "renamed"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.employee_user.refresh_from_db()
        self.assertEqual(self.employee_user.username, "employee_one")

    def test_other_user_cannot_update_account(self):
        self.client.force_authenticate(user=self.other_employee_user)
        response = self.client.patch(
            f"/api/v1/users/{self.employee_user.id}/",
            {"first_name": "Hacker"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_put_is_not_allowed(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.put(
            f"/api/v1/users/{self.employee_user.id}/",
            {"first_name": "Alice"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_owner_can_delete_own_account(self):
        self.client.force_authenticate(user=self.other_employee_user)
        response = self.client.delete(f"/api/v1/users/{self.other_employee_user.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(id=self.other_employee_user.id).exists())

    def test_other_user_cannot_delete_account(self):
        self.client.force_authenticate(user=self.other_employee_user)
        response = self.client.delete(f"/api/v1/users/{self.employee_user.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(User.objects.filter(id=self.employee_user.id).exists())

    def test_admin_can_delete_any_account(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(f"/api/v1/users/{self.other_employee_user.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
