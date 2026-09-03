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
from .serializers import TransactionSerializer, TransactionCancellationSerializer

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
            200: OpenApiResponse(description="Paiement validé avec succès"),
            400: OpenApiResponse(description="Solde insuffisant"),
            404: OpenApiResponse(description="Token expiré ou introuvable"),
        }
    )
    def post(self, request, token: str):
        key   : str = f"PaymentIntent:{token}"
        payload     = cache.get(key)

        if not payload:
            return Response(
                {"error": "QR code expired or already used"},
                status=status.HTTP_404_NOT_FOUND
            )

        amount = Decimal(payload["amount"])
        employee_id = payload["employee_id"]

        with transaction.atomic():
            try:
                emitter = Employee.objects.select_for_update().get(id=employee_id)
            except Employee.DoesNotExist:
                return Response({"error": "Emitter not found"}, status=status.HTTP_404_NOT_FOUND)

            if emitter.balance < amount:
                return Response({"error": "Insufficient balance"}, status=status.HTTP_400_BAD_REQUEST)

            emitter.balance -= amount
            emitter.save(update_fields=["balance"])

            # TODO: Create a transaction

        cache.delete(key)

        return Response({"message": "Payment successful"}, status=status.HTTP_200_OK)

class TransactionsView(generics.ListAPIView):
    queryset = Transaction.objects.all()
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = TransactionSerializer
