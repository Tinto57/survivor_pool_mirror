from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.exceptions import NotFound
from django.db import transaction
from django.db.models.deletion import ProtectedError
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse

from accounts.permissions import IsAdminRole
from audit.request_context import actor_info, get_client_ip
from audit.services import record_audit_event
from config.serializers import ErrorDetailSerializer
from wallet.permissions import IsOwnerOrAdminEmployee
from .models import Employee
from .serializers import (
    EmployeeSerializer,
    EmployeeBalanceReadSerializer,
    EmployeeBalanceUpdateSerializer,
)


@extend_schema_view(
    get=extend_schema(
        tags=["Salariés"],
        summary="Lister les salariés",
        description="Liste tous les comptes salariés. Réservé aux administrateurs.",
        responses={200: EmployeeSerializer(many=True)},
    ),
    post=extend_schema(
        tags=["Salariés"],
        summary="Créer un compte salarié",
        description="Rattache un compte salarié à un utilisateur existant. Réservé aux administrateurs.",
        responses={201: EmployeeSerializer},
    ),
)
class EmployeesView(generics.ListCreateAPIView):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [IsAdminRole]

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class EmployeeMe(generics.RetrieveAPIView):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Salariés"],
        summary="Consulter mon profil salarié",
        description="Renvoie la fiche salarié (dont le solde) de l'utilisateur actuellement authentifié.",
        responses={
            200: EmployeeSerializer,
            404: OpenApiResponse(response=ErrorDetailSerializer, description="L'utilisateur authentifié n'a pas de fiche salarié."),
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_object(self):
        try:
            return self.queryset.get(user=self.request.user)
        except Employee.DoesNotExist:
            raise NotFound(detail="Employee does not exist for you")


@extend_schema_view(
    get=extend_schema(
        tags=["Salariés"],
        summary="Consulter un salarié",
        description="Consultable par le salarié lui-même ou par un administrateur.",
        responses={200: EmployeeSerializer},
    ),
    delete=extend_schema(
        tags=["Salariés"],
        summary="Supprimer un compte salarié",
        description="Supprimable par le salarié lui-même ou par un administrateur.",
        responses={
            204: OpenApiResponse(description="Compte salarié supprimé avec succès."),
            409: OpenApiResponse(response=ErrorDetailSerializer, description="Des transactions sont rattachées à ce salarié."),
        },
    ),
)
class SingleEmployeeView(generics.RetrieveDestroyAPIView):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdminEmployee]
    lookup_url_kwarg = "employee_id"
    http_method_names = ["get", "delete"]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            instance.delete()
        except ProtectedError:
            return Response(
                {"detail": "Impossible de supprimer ce salarié : des transactions lui sont rattachées."},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class SingleEmployeeBalanceView(generics.RetrieveUpdateAPIView):
    queryset = Employee.objects.all()
    lookup_url_kwarg = "employee_id"
    http_method_names = ["get", "patch"]

    def get_permissions(self):
        if self.request.method in ("PATCH", "PUT"):
            return [IsAdminRole()]
        return [IsAuthenticated(), IsOwnerOrAdminEmployee()]

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return EmployeeBalanceUpdateSerializer
        return EmployeeBalanceReadSerializer

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        if self.request.method == "PATCH":
            queryset = queryset.select_for_update()

        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        obj = generics.get_object_or_404(queryset, **filter_kwargs)
        self.check_object_permissions(self.request, obj)
        return obj

    @extend_schema(
        tags=["Salariés"],
        summary="Consulter le solde d'un salarié",
        description="Consultable par le salarié lui-même ou par un administrateur.",
        responses={200: EmployeeBalanceReadSerializer},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        tags=["Salariés"],
        summary="Créditer le solde d'un employé",
        description="Ajoute un montant positif au solde d'un salarié. Réservé aux administrateurs.",
        request=EmployeeBalanceUpdateSerializer,
        responses={
            200: EmployeeBalanceReadSerializer,
            400: OpenApiResponse(response=ErrorDetailSerializer, description="Montant invalide (nul, négatif ou mal formé)."),
        },
    )
    @transaction.atomic
    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)

        updated_employee = serializer.save()

        actor_id, actor_role = actor_info(request)
        record_audit_event(
            actor_id=actor_id,
            actor_role=actor_role,
            action="BALANCE_TOPUP",
            target_type="Employee",
            target_id=updated_employee.id,
            payload={
                "amount": str(serializer.validated_data.get("amount", "")),
                "balance_after": str(updated_employee.balance),
            },
            ip=get_client_ip(request),
        )

        read_serializer = EmployeeBalanceReadSerializer(updated_employee)
        return Response(read_serializer.data, status=status.HTTP_200_OK)
