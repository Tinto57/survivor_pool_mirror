from django.utils import timezone
from rest_framework import generics
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
import secrets
from django.core.cache import cache
from .serializers import (
    PaymentIntentCreateSerializer,
    PaymentIntentResponseSerializer
)
from wallet.models import Employee
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework.exceptions import NotFound
from decimal import Decimal
from django.db import transaction
from .models import Transaction
from partners.models import Partner
from .serializers import TransactionSerializer, TransactionCancellationSerializer
from .permissions import IsParticipantOrStaff, IsAdminRole
from django.http import HttpResponse

EXPIRE_TIMEOUT = 60 * 5

class PaymentIntentCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
            summary="Create a payment intent",
            request=PaymentIntentCreateSerializer,
            responses={201: PaymentIntentResponseSerializer},
    )
    def post(self, req: Request):
        serializer = PaymentIntentCreateSerializer(data=req.data)
        serializer.is_valid(raise_exception=True)
        amount = serializer.validated_data["amount"]

        try:
            e: Employee = Employee.objects.get(user=req.user)
        except Employee.DoesNotExist:
            return Response({"error": "Only employees can generate payment intents"}, status=status.HTTP_403_FORBIDDEN,)

        if e.balance < amount:
            return Response({"error": "Not enough cash xD"}, status=status.HTTP_400_BAD_REQUEST)

        token = secrets.token_urlsafe(32)

        payload: dict = {
            "token"      : token,
            "amount"     : str(amount),
            "employee_id": e.id
        }

        cache.set(f"PaymentIntent:{token}", payload, timeout=EXPIRE_TIMEOUT)

        return Response({
            "token" : token,
            "amount": str(amount),
            "expire": EXPIRE_TIMEOUT
        }, status=status.HTTP_201_CREATED)

class PaymentIntentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Consulter une intention de paiement via son token (scan QR code)",
        responses={
            200: PaymentIntentResponseSerializer,
            404: OpenApiResponse(description="Token expiré ou introuvable"),
        }
    )
    def get(self, request, token: str):
        payload = cache.get(f"PaymentIntent:{token}")

        if not payload:
            return Response(
                {"error": "QR code expired or invalid"},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(payload, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Confirmer et exécuter le paiement",
        responses={
            200: TransactionSerializer,
            400: OpenApiResponse(description="Solde insuffisant ou compte partenaire inactif"),
            403: OpenApiResponse(description="Seul un partenaire peut valider un paiement"),
            404: OpenApiResponse(description="Token expiré ou introuvable"),
        }
    )
    def post(self, request, token: str):
        try:
            partner = request.user.partner
        except Partner.DoesNotExist:
            return Response(
                {"error": "Only partners can validate payments"},
                status=status.HTTP_403_FORBIDDEN
            )

        if partner.status != "active":
            return Response(
                {"error": "Partner account is not active"},
                status=status.HTTP_400_BAD_REQUEST
            )

        key: str = f"PaymentIntent:{token}"
        payload = cache.get(key)

        if not payload:
            return Response(
                {"error": "QR code expired or already used"},
                status=status.HTTP_404_NOT_FOUND
            )

        amount = Decimal(str(payload["amount"]))
        employee_id = payload["employee_id"]

        with transaction.atomic():
            try:
                emitter = Employee.objects.select_for_update().get(id=employee_id)
            except Employee.DoesNotExist:
                return Response(
                    {"error": "Emitter not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

            if emitter.balance < amount:
                return Response(
                    {"error": "Insufficient balance"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            emitter.balance -= amount
            emitter.save(update_fields=["balance"])

            tx = Transaction.objects.create(
                token=token,
                employee=emitter,
                partner=partner,
                amount=amount,
            )

        cache.delete(key)

        serializer = TransactionSerializer(tx)
        return Response(serializer.data, status=status.HTTP_200_OK)

class TransactionsView(generics.ListAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.is_staff or user.is_superuser:
            return Transaction.objects.select_related("employee__user", "partner__user").all()

        if hasattr(user, "partner"):
            return Transaction.objects.filter(
                partner=user.partner
            ).select_related("employee__user", "partner__user")

        if hasattr(user, "employee"):
            return Transaction.objects.filter(
                employee=user.employee
            ).select_related("employee__user", "partner__user")

        return Transaction.objects.none()

class SingleTransactionView(generics.RetrieveDestroyAPIView):
    queryset = Transaction.objects.select_related("employee__user", "partner__user").all()
    serializer_class = TransactionSerializer
    lookup_url_kwarg = "transaction_id"
    http_method_names = ["get", "delete"]

    def get_permissions(self):
        if self.request.method == "DELETE":
            return [IsAuthenticated(), IsAdminUser()]
        return [IsAuthenticated(), IsParticipantOrStaff()]

    @extend_schema(
        summary="Annuler une transaction et rembourser l'employé (Admin)",
        responses={
            200: TransactionSerializer,
            400: OpenApiResponse(description="Transaction déjà annulée"),
            404: OpenApiResponse(description="Transaction introuvable"),
        },
    )
    def delete(self, request, *args, **kwargs):
        transaction_id = self.kwargs[self.lookup_url_kwarg]
        reason = request.data.get("reason", "Annulation administrative")

        with transaction.atomic():
            try:
                tx = (
                    Transaction.objects.select_for_update()
                    .select_related("employee")
                    .get(id=transaction_id)
                )
            except Transaction.DoesNotExist:
                return Response(
                    {"error": "Transaction introuvable."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            if tx.is_cancelled:
                return Response(
                    {"error": "Cette transaction a déjà été annulée."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            employee = tx.employee.__class__.objects.select_for_update().get(id=tx.employee_id)
            employee.balance += tx.amount
            employee.save(update_fields=["balance"])

            tx.is_cancelled = True
            tx.cancelled_at = timezone.now()
            tx.cancelled_by = request.user
            tx.cancellation_reason = reason
            tx.save(update_fields=["is_cancelled", "cancelled_at", "cancelled_by", "cancellation_reason"])

        serializer = self.get_serializer(tx)
        return Response(serializer.data, status=status.HTTP_200_OK)

# class AdminTransactionsCsvExportView(APIView):
#     """GET /api/v1/admin/transactions.csv

#         Génère à la volée le CSV des transactions. Réservé au rôle admin.
#     """
#     permission_classes = [IsAdminRole]

#     def get(self, request, *args, **kwargs):
#         # csv_data = export_csv()

#         response = HttpResponse(
#             csv_data.encode('utf-8'), content_type='text/csv; charset=utf-8'
#         )
#         response['Content-Disposition'] = 'attachment; filename="transactions.csv"'
#         return response
