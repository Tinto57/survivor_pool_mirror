from decimal import Decimal

from django.db import IntegrityError, transaction
from django.http import HttpResponse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import BaseRenderer, JSONRenderer
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.cache import cache
import secrets

from accounts.permissions import IsAdminRole, IsActivePartner, IsEmployee, is_admin_role
from audit.request_context import actor_info, get_client_ip
from audit.services import record_audit_event
from config.serializers import ErrorDetailSerializer
from partners.models import Partner
from wallet.models import Employee
from .models import Transaction
from .permissions import CanInspectPaymentIntent, IsParticipantOrAdmin
from .serializers import (
    AbondmentCreateSerializer,
    PaymentConfirmSerializer,
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
            "Un salarié obtient un token à courte durée de vie (5 minutes), à encoder en QR "
            "code et présenter à un partenaire. Le montant n'est pas fixé ici : c'est le "
            "partenaire qui le choisit en confirmant le paiement. Réservé aux comptes de rôle "
            "`employee`."
        ),
        request=None,
        responses={
            201: PaymentIntentResponseSerializer,
            403: OpenApiResponse(response=ErrorDetailSerializer, description="Seul un salarié peut générer une intention de paiement."),
        },
    )
    def post(self, req: Request):
        try:
            employee = Employee.objects.get(user=req.user)
        except Employee.DoesNotExist:
            return Response(
                {"detail": "Only employees can generate payment intents"},
                status=status.HTTP_403_FORBIDDEN,
            )

        token = secrets.token_urlsafe(32)
        payload = {
            "token": token,
            "employee_id": employee.id,
        }
        cache.set(f"PaymentIntent:{token}", payload, timeout=EXPIRE_TIMEOUT)

        return Response(
            {
                "token": token,
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
            403: OpenApiResponse(response=ErrorDetailSerializer, description="Ni le créateur de l'intention, ni un partenaire actif, ni un administrateur."),
            404: OpenApiResponse(response=ErrorDetailSerializer, description="Token expiré ou introuvable."),
        },
    )
    def get(self, request, token: str):
        payload = cache.get(f"PaymentIntent:{token}")
        if not payload:
            return Response(
                {"detail": "QR code expired or invalid"},
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
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

        return Response(
            {
                "token": payload.get("token", token),
                "expires_in": EXPIRE_TIMEOUT,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=["Paiements"],
        operation_id="payments_confirm_intent",
        summary="Confirmer et exécuter le paiement",
        description=(
            "Le partenaire choisit le montant du paiement et le confirme : le salarié est "
            "débité et l'écriture comptable est créée au bénéfice du partenaire. "
            "Idempotent : rejouer la confirmation d'un token déjà consommé renvoie la même "
            "transaction sans débiter à nouveau (le montant renvoyé au rejeu est celui de la "
            "transaction déjà créée, pas celui du corps de la requête). Réservé à un compte "
            "partenaire actif."
        ),
        request=PaymentConfirmSerializer,
        responses={
            200: TransactionSerializer,
            400: OpenApiResponse(response=ErrorDetailSerializer, description="Solde insuffisant ou montant invalide."),
            403: OpenApiResponse(response=ErrorDetailSerializer, description="Seul un partenaire actif peut valider un paiement."),
            404: OpenApiResponse(response=ErrorDetailSerializer, description="Token expiré, introuvable, ou déjà utilisé par un autre partenaire."),
        },
    )
    def post(self, request, token: str):
        partner = request.user.partner
        key = f"PaymentIntent:{token}"
        payload = cache.get(key)

        if not payload:
            return self._replay_or_not_found(token, partner)

        serializer = PaymentConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        amount = serializer.validated_data["amount"]
        employee_id = payload["employee_id"]

        try:
            with transaction.atomic():
                try:
                    emitter = Employee.objects.select_for_update().get(id=employee_id)
                except Employee.DoesNotExist:
                    return Response(
                        {"detail": "Emitter not found"},
                        status=status.HTTP_404_NOT_FOUND,
                    )

                if emitter.balance < amount:
                    record_audit_event(
                        actor_id=partner.id,
                        actor_role="partner",
                        action="TRANSACTION_REJECTED",
                        target_type="Employee",
                        target_id=emitter.id,
                        payload={"amount_requested": str(amount), "reason": "insufficient_balance"},
                        ip=get_client_ip(request),
                    )
                    return Response(
                        {"detail": "Insufficient balance"},
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

                record_audit_event(
                    actor_id=partner.id,
                    actor_role="partner",
                    action="TRANSACTION_VALIDATED",
                    target_type="Transaction",
                    target_id=tx.id,
                    payload={"amount": str(amount), "employee_id": emitter.id},
                    ip=get_client_ip(request),
                )
        except IntegrityError:
            return self._replay_or_not_found(token, partner)

        return Response(TransactionSerializer(tx).data, status=status.HTTP_200_OK)

    def _replay_or_not_found(self, token: str, partner: Partner) -> Response:
        tx = Transaction.objects.filter(token=token).first()
        if tx is None or tx.partner_id != partner.id:
            return Response(
                {"detail": "QR code expired or already used"},
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
            return Transaction.objects.select_related("employee__user", "partner__user", "counter_entry").all()

        if hasattr(user, "partner"):
            return Transaction.objects.filter(
                partner=user.partner
            ).select_related("employee__user", "partner__user", "counter_entry")

        if hasattr(user, "employee"):
            return Transaction.objects.filter(
                employee=user.employee
            ).select_related("employee__user", "partner__user", "counter_entry")

        return Transaction.objects.none()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        user = self.request.user

        if hasattr(user, "employee"):
            context["balance_after_map"] = self._balance_after_map(user.employee)

        return context

    def _balance_after_map(self, employee) -> dict:
        """Reconstitue, pour chaque écriture du salarié, le solde juste après elle.

        Transaction n'a pas de solde figé (immuable, pas de champ balance_after
        stocké) : on part du solde actuel et on retranche les deltas en ordre
        chronologique inverse pour retrouver le solde après chaque écriture.
        """
        transactions = list(
            Transaction.objects.filter(employee=employee).order_by("-validated_at", "-id")
        )
        running = employee.balance
        balance_after_map = {}
        for tx in transactions:
            balance_after_map[tx.id] = running
            delta = tx.amount if tx.transaction_type == Transaction.ABONDMENT else -tx.amount
            running -= delta
        return balance_after_map


@extend_schema(
    tags=["Transactions"],
    summary="Consulter une transaction",
    description="Consultable par le salarié ou le partenaire impliqué dans la transaction, ou par un administrateur.",
    responses={
        200: TransactionSerializer,
        403: OpenApiResponse(response=ErrorDetailSerializer, description="L'utilisateur n'est ni impliqué dans la transaction, ni administrateur."),
        404: OpenApiResponse(response=ErrorDetailSerializer, description="Transaction introuvable."),
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
            400: OpenApiResponse(response=ErrorDetailSerializer, description="Montant invalide ou salarié introuvable."),
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
            400: OpenApiResponse(response=ErrorDetailSerializer, description="Contre-écriture déjà existante, transaction non contre-passable (ex : paiement annulé), ou solde insuffisant pour la contre-écriture."),
            404: OpenApiResponse(response=ErrorDetailSerializer, description="Transaction introuvable."),
        },
    )
    @transaction.atomic
    def post(self, request, transaction_id):
        try:
            tx = Transaction.objects.select_for_update().get(id=transaction_id)
        except Transaction.DoesNotExist:
            return Response(
                {"detail": "Transaction introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if hasattr(tx, "counter_entry"):
            return Response(
                {"detail": "Cette transaction possède déjà une contre-écriture."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if tx.transaction_type not in (Transaction.PAYMENT, Transaction.ABONDMENT):
            return Response(
                {"detail": "Seules les transactions de type paiement ou abondement peuvent être contre-passées."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        employee = Employee.objects.select_for_update().get(id=tx.employee_id)
        if tx.transaction_type == Transaction.PAYMENT:
            employee.balance += tx.amount
            counter_type = Transaction.ABONDMENT
        else:
            if employee.balance < tx.amount:
                return Response(
                    {"detail": "Solde insuffisant pour la contre-écriture."},
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

        actor_id, actor_role = actor_info(request)
        record_audit_event(
            actor_id=actor_id,
            actor_role=actor_role,
            action="ADMIN_ACTION",
            target_type="Transaction",
            target_id=counter_entry.id,
            payload={"detail": "COUNTER_ENTRY_CREATED", "counter_entry_of": tx.id, "amount": str(tx.amount)},
            ip=get_client_ip(request),
        )

        return Response(TransactionSerializer(counter_entry).data, status=status.HTTP_201_CREATED)


class CSVRenderer(BaseRenderer):
    media_type = "text/csv"
    format = "csv"
    charset = "utf-8"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data


class AdminTransactionsCsvExportView(APIView):
    permission_classes = [IsAdminRole]
    renderer_classes = [CSVRenderer]

    def finalize_response(self, request, response, *args, **kwargs):
        # Une erreur DRF (401/403/404...) passe aussi par CSVRenderer, qui ne
        # sait pas sérialiser le dict {"detail": ...} : on bascule sur du JSON
        # pour ces réponses-là. Le chemin succès (HttpResponse brute, plus bas)
        # n'est pas concerné par cette bascule.
        # NB : c'est `request.accepted_renderer` qu'il faut réécrire, pas
        # `response.accepted_renderer` — la classe de base copie l'un vers
        # l'autre juste après, ce qui écraserait silencieusement le nôtre.
        if getattr(response, "exception", False):
            request.accepted_renderer = JSONRenderer()
            request.accepted_media_type = "application/json"
        return super().finalize_response(request, response, *args, **kwargs)

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
