from rest_framework import permissions
from rest_framework.request import Request

from accounts.permissions import is_admin_role


class IsOwnerOrAdminEmployee(permissions.BasePermission):
    def has_object_permission(self, request: Request, view, obj) -> bool:
        if is_admin_role(request.user):
            return True
        return obj.user_id == request.user.id


class HasExternalApiKey(permissions.BasePermission):
    """Accorde l'accès si `ExternalApiKeyAuthentication` a validé une clé API
    (elle place alors la clé dans `request.auth`)."""

    def has_permission(self, request: Request, view) -> bool:
        return bool(request.auth)
