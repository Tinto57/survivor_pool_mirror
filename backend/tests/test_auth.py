from rest_framework import status

from .base import BaseAPITestCase, STRONG_PASSWORD


class AuthTests(BaseAPITestCase):
    def test_login_success_returns_tokens_and_user_summary(self):
        response = self.client.post(
            "/api/v1/auth/",
            {"username": "employee_one", "password": STRONG_PASSWORD},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Ok")
        self.assertEqual(response.data["user"]["username"], "employee_one")
        self.assertEqual(response.data["user"]["role"], "employee")
        self.assertIn("access", response.data["token"])
        self.assertIn("refresh", response.data["token"])

        self.employee_user.refresh_from_db()
        self.assertIsNotNone(self.employee_user.last_login)

    def test_login_wrong_password_is_rejected(self):
        response = self.client.post(
            "/api/v1/auth/",
            {"username": "employee_one", "password": "not-the-password"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_unknown_username_is_rejected(self):
        response = self.client.post(
            "/api/v1/auth/",
            {"username": "does-not-exist", "password": STRONG_PASSWORD},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_missing_password_is_bad_request(self):
        response = self.client.post(
            "/api/v1/auth/",
            {"username": "employee_one"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_missing_username_is_bad_request(self):
        response = self.client.post(
            "/api/v1/auth/",
            {"password": STRONG_PASSWORD},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_empty_body_is_bad_request(self):
        response = self.client.post("/api/v1/auth/", {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_does_not_leak_whether_username_exists(self):
        # Un attaquant ne doit pas pouvoir distinguer "username inconnu" de
        # "mot de passe faux" via le code HTTP.
        unknown = self.client.post(
            "/api/v1/auth/",
            {"username": "does-not-exist", "password": "whatever123"},
            format="json",
        )
        wrong_password = self.client.post(
            "/api/v1/auth/",
            {"username": "employee_one", "password": "whatever123"},
            format="json",
        )
        self.assertEqual(unknown.status_code, wrong_password.status_code)

    def test_login_get_not_allowed(self):
        response = self.client.get("/api/v1/auth/")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
