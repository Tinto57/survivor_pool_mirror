from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.exceptions import NotFound
from django.db import transaction
from drf_spectacular.utils import extend_schema

from accounts.permissions import IsAdminRole
from wallet.permissions import IsOwnerOrAdminEmployee
from .models import Employee
from .serializers import (
    EmployeeSerializer,
    EmployeeBalanceReadSerializer,
    EmployeeBalanceUpdateSerializer,
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

    def get_object(self):
        try:
            return self.queryset.get(user=self.request.user)
        except Employee.DoesNotExist:
            raise NotFound(detail="Employee does not exist for you")


class SingleEmployeeView(generics.RetrieveDestroyAPIView):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdminEmployee]
    lookup_url_kwarg = "employee_id"
    http_method_names = ["get", "delete"]


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
        summary="Créditer le solde d'un employé",
        request=EmployeeBalanceUpdateSerializer,
        responses={200: EmployeeBalanceReadSerializer},
    )
    @transaction.atomic
    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        updated_employee = serializer.save()

        read_serializer = EmployeeBalanceReadSerializer(updated_employee)
        return Response(read_serializer.data, status=status.HTTP_200_OK)
