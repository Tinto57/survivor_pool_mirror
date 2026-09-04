from rest_framework import serializers


class ErrorDetailSerializer(serializers.Serializer):
    """Corps de réponse standard pour les erreurs de l'API (mêmes clés que
    les exceptions DRF natives : permissions, authentification, 404...)."""

    detail = serializers.CharField(help_text="Message décrivant l'erreur.")
