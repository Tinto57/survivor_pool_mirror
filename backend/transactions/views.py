from decimal import Decimal

from django.db import IntegrityError, transaction
from django.http import HttpResponse
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.cache import cache
import secrets

from accounts.permissions import IsAdminRole, IsActivePartner, IsEmployee, is_admin_role
from partners.models import Partner
from wallet.models import Employee
from .models import Transaction
from .permissions import CanInspectPaymentIntent, IsParticipantOrAdmin
from .serializers import (
    AbondmentCreateSerializer,
    PaymentIntentCreateSerializer,
    PaymentIntentResponseSerializer,
    TransactionSerializer,
)
from .services import export_transactions

EXPIRE_TIMEOUT = 60 * 5


class PaymentIntentCreateView(APIView):
    permission_classes = [IsEmployee]

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
            employee = Employee.objects.get(user=req.user)
        except Employee.DoesNotExist:
            return Response(
                {"error": "Only employees can generate payment intents"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if employee.balance < amount:
            return Response(
                {"error": "Not enough cash xD"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        token = secrets.token_urlsafe(32)
        payload = {
            "token": token,
            "amount": str(amount),
            "employee_id": employee.id,
        }
        cache.set(f"PaymentIntent:{token}", payload, timeout=EXPIRE_TIMEOUT)

        return Response(
            {
                "token": token,
                "amount": str(amount),
                "expire": EXPIRE_TIMEOUT,
            },
            status=status.HTTP_201_CREATED,
        )


class PaymentIntentDetailView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsActivePartner()]
        return [CanInspectPaymentIntent()]

    @extend_schema(
        summary="Consulter une intention de paiement via son token (scan QR code)",
        responses={
            200: PaymentIntentResponseSerializer,
            404: OpenApiResponse(description="Token expiré ou introuvable"),
        },
    )
    def get(self, request, token: str):
        payload = cache.get(f"PaymentIntent:{token}")
        if not payload:
            return Response(
                {"error": "QR code expired or invalid"},
                status=status.HTTP_404_NOT_FOUND,
            )

        user = request.user
        employee_id = payload.get("employee_id")
        is_creator = False
        try:
            is_creator = user.employee.id == employee_id
        except Employee.DoesNotExist:
            pass

        partner = getattr(user, "partner", None)
        is_active_partner = partner is not None and partner.status == "active"

        if not (is_admin_role(user) or is_creator or is_active_partner):
            return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

        return Response(
            {
                "token": payload.get("token", token),
                "amount": payload.get("amount"),
                "expire": EXPIRE_TIMEOUT,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="Confirmer et exécuter le paiement",
        responses={
            200: TransactionSerializer,
            400: OpenApiResponse(description="Solde insuffisant ou compte partenaire inactif"),
            403: OpenApiResponse(description="Seul un partenaire peut valider un paiement"),
            404: OpenApiResponse(description="Token expiré ou introuvable"),
        },
    )
    def post(self, request, token: str):
        partner = request.user.partner
        key = f"PaymentIntent:{token}"
        payload = cache.get(key)

        if not payload:
            return self._replay_or_not_found(token, partner)

        amount = Decimal(str(payload["amount"]))
        employee_id = payload["employee_id"]

        try:
            with transaction.atomic():
                try:
                    emitter = Employee.objects.select_for_update().get(id=employee_id)
                except Employee.DoesNotExist:
                    return Response(
                        {"error": "Emitter not found"},
                        status=status.HTTP_404_NOT_FOUND,
                    )

                if emitter.balance < amount:
                    return Response(
                        {"error": "Insufficient balance"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                emitter.balance -= amount
                emitter.save(update_fields=["balance"])

                tx = Transaction.objects.create(
                    token=token,
                    transaction_type=Transaction.PAYMENT,
                    employee=emitter,
                    partner=partner,
                    amount=amount,
                )
                cache.delete(key)
        except IntegrityError:
            return self._replay_or_not_found(token, partner)

        return Response(TransactionSerializer(tx).data, status=status.HTTP_200_OK)

    def _replay_or_not_found(self, token: str, partner: Partner) -> Response:
        tx = Transaction.objects.filter(token=token).first()
        if tx is None or tx.partner_id != partner.id:
            return Response(
                {"error": "QR code expired or already used"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(TransactionSerializer(tx).data, status=status.HTTP_200_OK)


class TransactionsView(generics.ListAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if is_admin_role(user):
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


class SingleTransactionView(generics.RetrieveAPIView):
    queryset = Transaction.objects.select_related("employee__user", "partner__user").all()
    serializer_class = TransactionSerializer
    lookup_url_kwarg = "transaction_id"
    http_method_names = ["get"]
    permission_classes = [IsAuthenticated, IsParticipantOrAdmin]


class AbondmentCreateView(APIView):
    permission_classes = [IsAdminRole]

    @extend_schema(
        summary="Créditer le solde d'un employé avec un abondement",
        request=AbondmentCreateSerializer,
        responses={201: TransactionSerializer},
    )
    @transaction.atomic
    def post(self, request):
        serializer = AbondmentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        employee = Employee.objects.select_for_update().get(
            id=serializer.validated_data["employee"].id
        )
        amount = serializer.validated_data["amount"]
        employee.balance += amount
        employee.save(update_fields=["balance"])

        tx = Transaction.objects.create(
            transaction_type=Transaction.ABONDMENT,
            employee=employee,
            amount=amount,
        )
        return Response(TransactionSerializer(tx).data, status=status.HTTP_201_CREATED)


class CounterEntryCreateView(APIView):
    permission_classes = [IsAdminRole]

    @extend_schema(
        summary="Créer la contre-écriture d'une transaction",
        responses={201: TransactionSerializer},
    )
    @transaction.atomic
    def post(self, request, transaction_id):
        try:
            tx = Transaction.objects.select_for_update().get(id=transaction_id)
        except Transaction.DoesNotExist:
            return Response(
                {"error": "Transaction introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if hasattr(tx, "counter_entry"):
            return Response(
                {"error": "Cette transaction possède déjà une contre-écriture."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        employee = Employee.objects.select_for_update().get(id=tx.employee_id)
        if tx.transaction_type == Transaction.PAYMENT:
            employee.balance += tx.amount
            counter_type = Transaction.ABONDMENT
        else:
            if employee.balance < tx.amount:
                return Response(
                    {"error": "Solde insuffisant pour la contre-écriture."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            employee.balance -= tx.amount
            counter_type = Transaction.PAYMENT
        employee.save(update_fields=["balance"])

        counter_entry = Transaction.objects.create(
            transaction_type=counter_type,
            employee=employee,
            partner=tx.partner if counter_type == Transaction.PAYMENT else None,
            amount=tx.amount,
            counter_entry_of=tx,
        )
        return Response(TransactionSerializer(counter_entry).data, status=status.HTTP_201_CREATED)


class AdminTransactionsCsvExportView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request, *args, **kwargs):
        csv_data = export_transactions()
        response = HttpResponse(
            csv_data.encode("utf-8"),
            content_type="text/csv; charset=utf-8",
        )
        response["Content-Disposition"] = 'attachment; filename="transactions.csv"'
        return response
