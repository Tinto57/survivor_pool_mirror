from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from django.utils.dateparse import parse_datetime

from accounts.permissions import IsAdminRole
from config.serializers import ErrorDetailSerializer

from .models import AuditLog
from .serializers import AuditLogSerializer


@extend_schema(
    tags=["Audit"],
    summary="Consulter le journal d'audit",
    description=(
        "Liste paginée du journal d'audit en ajout seul. Réservé aux administrateurs. "
        "Filtrable par type d'action (`action`), acteur (`actor_id`, `actor_role`), "
        "type de cible (`target_type`) et période (`start`, `end`, bornes incluses, "
        "ISO 8601 sur `occurred_at`)."
    ),
    parameters=[
        OpenApiParameter("action", str, description="Filtre exact sur le type d'action (ex. `TRANSACTION_VALIDATED`)."),
        OpenApiParameter("actor_id", int, description="Filtre exact sur l'identifiant de l'acteur."),
        OpenApiParameter("actor_role", str, description="Filtre exact sur le rôle de l'acteur."),
        OpenApiParameter("target_type", str, description="Filtre exact sur le type de cible (ex. `Transaction`)."),
        OpenApiParameter("start", str, description="Borne inférieure incluse sur `occurred_at`, ISO 8601."),
        OpenApiParameter("end", str, description="Borne supérieure incluse sur `occurred_at`, ISO 8601."),
    ],
    responses={
        200: AuditLogSerializer(many=True),
        400: OpenApiResponse(response=ErrorDetailSerializer, description="Paramètre de filtre invalide (`actor_id`, `start` ou `end` mal formé)."),
    },
)
class AdminAuditLogView(generics.ListAPIView):
    serializer_class = AuditLogSerializer
    permission_classes = [IsAdminRole]

    def get_queryset(self):
        queryset = AuditLog.objects.order_by("-id")
        params = self.request.query_params

        action = params.get("action")
        if action:
            queryset = queryset.filter(action=action)

        actor_role = params.get("actor_role")
        if actor_role:
            queryset = queryset.filter(actor_role=actor_role)

        target_type = params.get("target_type")
        if target_type:
            queryset = queryset.filter(target_type=target_type)

        actor_id = params.get("actor_id")
        if actor_id:
            if not actor_id.lstrip("-").isdigit():
                raise ValidationError({"actor_id": "Doit être un identifiant numérique."})
            queryset = queryset.filter(actor_id=int(actor_id))

        start = params.get("start")
        if start:
            parsed_start = parse_datetime(start)
            if parsed_start is None:
                raise ValidationError({"start": "Doit être une date ISO 8601."})
            queryset = queryset.filter(occurred_at__gte=parsed_start)

        end = params.get("end")
        if end:
            parsed_end = parse_datetime(end)
            if parsed_end is None:
                raise ValidationError({"end": "Doit être une date ISO 8601."})
            queryset = queryset.filter(occurred_at__lte=parsed_end)

        return queryset
