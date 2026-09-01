from functools import wraps
from django.http import HttpRequest, JsonResponse
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

User = get_user_model()

def require_jwt(f):
    @wraps(f)
    def wrapper(req: HttpRequest, *args, **kwargs):
        bearer = req.headers.get("Authorization", "")

        if not bearer.startswith("Bearer "):
            return JsonResponse({
                "error": "Invalid credentials"
            }, status=401)

        splitted = bearer.split(" ")[1]

        try:
            token = AccessToken(splitted)
            req.user = User.objects.get(id=token["user_id"])
        except (InvalidToken, TokenError, User.DoesNotExist):
            return JsonResponse({
                "error": "invalid token"
            }, status=401)

        return f(req, *args, **kwargs)
    return wrapper
