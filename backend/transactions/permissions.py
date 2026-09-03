from rest_framework.permissions import BasePermission


class IsParticipantOrStaff(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff or request.user.is_superuser:
            return True

        current_user_id = request.user.id

        employee_user_id = getattr(getattr(obj, "employee", None), "user_id", None)
        if employee_user_id == current_user_id:
            return True

        partner_user_id = getattr(getattr(obj, "partner", None), "user_id", None)
        if partner_user_id == current_user_id:
            return True

        return False
