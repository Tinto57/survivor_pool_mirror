from django.conf import settings
from django.core.cache import cache
from django.db import connections
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import HealthResponseSerializer


class HealthView(APIView):
    """Health check public, non authentifié : utilisé par les sondes de
    déploiement (Docker, Render...) pour savoir si l'API peut servir du trafic."""

    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        tags=["Système"],
        summary="État de santé de l'API",
        description=(
            "Vérifie la connectivité à la base de données et au cache, et renvoie "
            "la version de l'API. Renvoie 503 si un des deux échoue."
        ),
        responses={
            200: HealthResponseSerializer,
            503: HealthResponseSerializer,
        },
    )
    def get(self, request):
        checks = {
            "database": self._check_database(),
            "cache": self._check_cache(),
        }
        healthy = all(value == "ok" for value in checks.values())

        return Response(
            {
                "status": "ok" if healthy else "error",
                "version": settings.APP_VERSION,
                "checks": checks,
            },
            status=status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    def _check_database(self) -> str:
        try:
            with connections["default"].cursor() as cursor:
                cursor.execute("SELECT 1")
            return "ok"
        except Exception:  # noqa: BLE001 - un health check ne doit jamais lui-même planter
            return "error"

    def _check_cache(self) -> str:
        try:
            probe_key = "healthcheck:probe"
            cache.set(probe_key, "1", timeout=5)
            return "ok" if cache.get(probe_key) == "1" else "error"
        except Exception:  # noqa: BLE001 - idem : on veut un statut, jamais une exception
            return "error"
