import hmac

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


class ExternalApiKeyAuthentication(BaseAuthentication):
    """Authentifie un système tiers (SIRH employeur) via une clé API statique
    transmise dans l'en-tête `X-Api-Key`. Distinct du JWT utilisateur : ce
    canal ne représente aucun compte CartePro, seulement un système partenaire
    de confiance habilité à interroger un solde salarié en lecture seule."""

    def authenticate(self, request):
        provided_key = request.META.get("HTTP_X_API_KEY")
        if not provided_key:
            return None

        configured_keys = settings.SIRH_API_KEYS
        if not configured_keys:
            raise AuthenticationFailed("Aucune clé API SIRH n'est configurée côté serveur.")

        for key in configured_keys:
            if hmac.compare_digest(provided_key, key):
                return (AnonymousUser(), provided_key)

        raise AuthenticationFailed("Clé API invalide.")
