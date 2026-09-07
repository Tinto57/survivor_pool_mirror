from rest_framework import permissions
from rest_framework.request import Request


def is_admin_role(user) -> bool:
    return bool(user and user.is_authenticated and getattr(user, "role", None) == "admin")


class IsAdminRole(permissions.BasePermission):
    def has_permission(self, request: Request, view) -> bool:
        return is_admin_role(request.user)


class IsEmployee(permissions.BasePermission):
    def has_permission(self, request: Request, view) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "role", None) == "employee"
        )


class IsActivePartner(permissions.BasePermission):
    def has_permission(self, request: Request, view) -> bool:
        user = request.user
        if not user or not user.is_authenticated or getattr(user, "role", None) != "partner":
            return False
        partner = getattr(user, "partner", None)
        return partner is not None and partner.status == "active"


class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request: Request, view, obj) -> bool:
        if is_admin_role(request.user):
            return True
        return obj.id == request.user.id
