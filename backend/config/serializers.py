from rest_framework import serializers


class ErrorDetailSerializer(serializers.Serializer):
    """Corps de réponse standard pour les erreurs de l'API (mêmes clés que
    les exceptions DRF natives : permissions, authentification, 404...)."""

    detail = serializers.CharField(help_text="Message décrivant l'erreur.")


class HealthChecksSerializer(serializers.Serializer):
    """Détail des sous-systèmes vérifiés par le health check."""

    database = serializers.CharField(help_text="`ok` ou `error` : connectivité à la base de données.")
    cache = serializers.CharField(help_text="`ok` ou `error` : connectivité au cache (Redis).")


class HealthResponseSerializer(serializers.Serializer):
    """Réponse du health check (`GET /api/v1/health/`)."""

    status = serializers.CharField(help_text="`ok` si tous les checks passent, `error` sinon.")
    version = serializers.CharField(help_text="Version de l'API.")
    checks = HealthChecksSerializer()
