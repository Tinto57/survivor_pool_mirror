from rest_framework.permissions import BasePermission
from rest_framework.request import Request

from accounts.permissions import is_admin_role

from .models import Partner


class IsPartnerOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request: Request, view, obj: Partner) -> bool:
        if is_admin_role(request.user):
            return True
        return obj.user_id == request.user.id


class CanViewPartner(BasePermission):
    """Un partenaire actif est visible de tous ; sinon uniquement par son
    propriétaire ou un administrateur (ex : fiche encore en attente)."""

    def has_object_permission(self, request: Request, view, obj: Partner) -> bool:
        if is_admin_role(request.user):
            return True
        if obj.user_id == request.user.id:
            return True
        return obj.status == "active"


class CanViewPartnerDecisions(BasePermission):
    def has_permission(self, request: Request, view) -> bool:
        if is_admin_role(request.user):
            return True
        partner_id = view.kwargs.get("partner_id")
        return Partner.objects.filter(id=partner_id, user=request.user).exists()
