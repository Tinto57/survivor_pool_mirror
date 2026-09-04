from rest_framework.permissions import BasePermission
from rest_framework.request import Request

from accounts.permissions import is_admin_role


class IsParticipantOrAdmin(BasePermission):
    def has_permission(self, request: Request, view) -> bool:
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request: Request, view, obj) -> bool:
        if is_admin_role(request.user):
            return True

        current_user_id = request.user.id

        employee_user_id = getattr(getattr(obj, "employee", None), "user_id", None)
        if employee_user_id == current_user_id:
            return True

        partner_user_id = getattr(getattr(obj, "partner", None), "user_id", None)
        if partner_user_id == current_user_id:
            return True

        return False


class CanInspectPaymentIntent(BasePermission):
    """QR payload: the employee who created it, an active partner, or an admin."""

    def has_permission(self, request: Request, view) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if is_admin_role(user) or getattr(user, "role", None) == "employee":
            return True
        partner = getattr(user, "partner", None)
        return partner is not None and partner.status == "active"
