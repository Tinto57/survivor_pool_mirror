from decimal import Decimal

from django.db import IntegrityError, transaction
from django.http import HttpResponse
from drf_spectacular.types import OpenApiTypes
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
        tags=["Paiements"],
        operation_id="payments_create_intent",
        summary="Créer une intention de paiement",
        description=(
            "Un salarié réserve un montant sur son solde et obtient un token à courte durée "
            "de vie (5 minutes), à encoder en QR code et présenter à un partenaire. "
            "Réservé aux comptes de rôle `employee`."
        ),
        request=PaymentIntentCreateSerializer,
        responses={
            201: PaymentIntentResponseSerializer,
            400: OpenApiResponse(description="Solde insuffisant."),
            403: OpenApiResponse(description="Seul un salarié peut générer une intention de paiement."),
        },
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
                {"error": "Insufficient balance"},
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
                "expires_in": EXPIRE_TIMEOUT,
            },
            status=status.HTTP_201_CREATED,
        )


class PaymentIntentDetailView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsActivePartner()]
        return [CanInspectPaymentIntent()]

    @extend_schema(
        tags=["Paiements"],
        operation_id="payments_retrieve_intent",
        summary="Consulter une intention de paiement via son token (scan QR code)",
        description=(
            "Consultable par le salarié qui a créé l'intention, par un partenaire actif, "
            "ou par un administrateur."
        ),
        responses={
            200: PaymentIntentResponseSerializer,
            403: OpenApiResponse(description="Ni le créateur de l'intention, ni un partenaire actif, ni un administrateur."),
            404: OpenApiResponse(description="Token expiré ou introuvable."),
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
                "expires_in": EXPIRE_TIMEOUT,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=["Paiements"],
        operation_id="payments_confirm_intent",
        summary="Confirmer et exécuter le paiement",
        description=(
            "Débite le salarié et crée l'écriture comptable de paiement au bénéfice du partenaire. "
            "Idempotent : rejouer la confirmation d'un token déjà consommé renvoie la même transaction "
            "sans débiter à nouveau. Réservé à un compte partenaire actif."
        ),
        request=None,
        responses={
            200: TransactionSerializer,
            400: OpenApiResponse(description="Solde insuffisant."),
            403: OpenApiResponse(description="Seul un partenaire actif peut valider un paiement."),
            404: OpenApiResponse(description="Token expiré, introuvable, ou déjà utilisé par un autre partenaire."),
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


@extend_schema(
    tags=["Transactions"],
    summary="Lister les transactions",
    description=(
        "Liste les écritures comptables visibles par l'utilisateur authentifié : "
        "toutes pour un administrateur, uniquement les siennes pour un salarié ou un partenaire."
    ),
    responses={200: TransactionSerializer(many=True)},
)
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


@extend_schema(
    tags=["Transactions"],
    summary="Consulter une transaction",
    description="Consultable par le salarié ou le partenaire impliqué dans la transaction, ou par un administrateur.",
    responses={
        200: TransactionSerializer,
        403: OpenApiResponse(description="L'utilisateur n'est ni impliqué dans la transaction, ni administrateur."),
        404: OpenApiResponse(description="Transaction introuvable."),
    },
)
class SingleTransactionView(generics.RetrieveAPIView):
    queryset = Transaction.objects.select_related("employee__user", "partner__user").all()
    serializer_class = TransactionSerializer
    lookup_url_kwarg = "transaction_id"
    http_method_names = ["get"]
    permission_classes = [IsAuthenticated, IsParticipantOrAdmin]


class AbondmentCreateView(APIView):
    permission_classes = [IsAdminRole]

    @extend_schema(
        tags=["Transactions"],
        summary="Créditer le solde d'un employé avec un abondement",
        description="Crée une écriture comptable d'abondement et crédite immédiatement le solde du salarié concerné. Réservé aux administrateurs.",
        request=AbondmentCreateSerializer,
        responses={
            201: TransactionSerializer,
            400: OpenApiResponse(description="Montant invalide ou salarié introuvable."),
        },
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
        tags=["Transactions"],
        summary="Créer la contre-écriture d'une transaction",
        description=(
            "Annule une transaction existante en créant sa contre-écriture (un paiement est "
            "contré par un abondement, et inversement), sans jamais modifier ni supprimer "
            "l'écriture d'origine. Réservé aux administrateurs."
        ),
        request=None,
        responses={
            201: TransactionSerializer,
            400: OpenApiResponse(description="Contre-écriture déjà existante, ou solde insuffisant pour la contre-écriture."),
            404: OpenApiResponse(description="Transaction introuvable."),
        },
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

    @extend_schema(
        tags=["Transactions"],
        operation_id="transactions_export_csv",
        summary="Exporter toutes les transactions en CSV",
        description="Génère un export CSV (délimiteur `;`) de toutes les transactions en base. Réservé aux administrateurs.",
        request=None,
        responses={(200, "text/csv"): OpenApiTypes.BINARY},
    )
    def get(self, request, *args, **kwargs):
        csv_data = export_transactions()
        response = HttpResponse(
            csv_data.encode("utf-8"),
            content_type="text/csv; charset=utf-8",
        )
        response["Content-Disposition"] = 'attachment; filename="transactions.csv"'
        return response
