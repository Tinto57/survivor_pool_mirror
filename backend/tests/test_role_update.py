from rest_framework import status

from .base import BaseAPITestCase


class UserRoleUpdateViewTests(BaseAPITestCase):
    """Comportement de la route elle-même (permissions, validation, persistance,
    méthodes autorisées). Le déclenchement de l'écriture d'audit ROLE_CHANGED est
    déjà couvert par tests/test_audit_instrumentation.py::RoleChangedAuditTestCase —
    pas dupliqué ici."""

    def test_admin_can_change_role(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            f"/api/v1/users/{self.employee_user.id}/role/",
            {"role": "partner"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["role"], "partner")
        self.employee_user.refresh_from_db()
        self.assertEqual(self.employee_user.role, "partner")

    def test_admin_can_promote_to_admin(self):
        # Contrairement à l'inscription publique (POST /users/), qui interdit le
        # rôle admin, cette route est réservée aux administrateurs et n'a pas de
        # raison de bloquer ce choix : c'est le mécanisme prévu pour promouvoir.
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            f"/api/v1/users/{self.employee_user.id}/role/",
            {"role": "admin"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.employee_user.refresh_from_db()
        self.assertEqual(self.employee_user.role, "admin")

    def test_non_admin_cannot_change_role(self):
        self.client.force_authenticate(user=self.employee_user)
        response = self.client.patch(
            f"/api/v1/users/{self.other_employee_user.id}/role/",
            {"role": "admin"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.other_employee_user.refresh_from_db()
        self.assertEqual(self.other_employee_user.role, "employee")

    def test_partner_cannot_change_role(self):
        self.client.force_authenticate(user=self.partner_user)
        response = self.client.patch(
            f"/api/v1/users/{self.employee_user.id}/role/",
            {"role": "admin"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_cannot_change_role(self):
        response = self.client.patch(
            f"/api/v1/users/{self.employee_user.id}/role/",
            {"role": "admin"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unknown_role_value_is_rejected(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            f"/api/v1/users/{self.employee_user.id}/role/",
            {"role": "superhero"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.employee_user.refresh_from_db()
        self.assertEqual(self.employee_user.role, "employee")

    def test_missing_role_field_is_a_silent_no_op(self):
        # `update()` appelle get_serializer(..., partial=True) en dur : un payload
        # vide est valide pour DRF (rien à changer), pas une erreur. Documente le
        # comportement réel plutôt que celui, plus strict, qu'on pourrait attendre
        # d'un endpoint à vocation unique — à signaler si ce n'est pas voulu.
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            f"/api/v1/users/{self.employee_user.id}/role/",
            {},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.employee_user.refresh_from_db()
        self.assertEqual(self.employee_user.role, "employee")

    def test_unknown_user_is_404(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            "/api/v1/users/999999/role/",
            {"role": "admin"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_is_not_allowed(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(f"/api/v1/users/{self.employee_user.id}/role/")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_put_is_not_allowed(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.put(
            f"/api/v1/users/{self.employee_user.id}/role/",
            {"role": "admin"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_is_not_allowed(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(f"/api/v1/users/{self.employee_user.id}/role/")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_response_body_does_not_leak_password(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            f"/api/v1/users/{self.employee_user.id}/role/",
            {"role": "partner"},
            format="json",
        )
        self.assertNotIn("password", response.data)
