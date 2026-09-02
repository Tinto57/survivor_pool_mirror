from rest_framework import permissions
from rest_framework.request import Request

class IsOwnerOrStaff(permissions.BasePermission):
    def has_object_permission(
            self,
            request: Request,
            view,
            obj
        ) -> bool:
        if request.user.is_staff or request.user.is_superuser:
            return True
        return obj.id == request.user.id
