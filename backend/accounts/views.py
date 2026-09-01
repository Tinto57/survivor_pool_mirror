from rest_framework_simplejwt.tokens import RefreshToken
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpRequest, JsonResponse
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from utils.get_payload import get_payload
from utils.wrappers import require_jwt
from .models import *

# Create your views here.

# NOTE: Old login route
# @csrf_exempt
# def account_login(request: HttpRequest) -> JsonResponse:
#     """ Login user (ensure user exists, valid pwd...) """
#     if request.method != "POST":
#         return JsonResponse({
#             "error": "Method not allowed"
#         }, status=405)

#     username: str | None = request.POST.get("username", None)
#     password: str | None = request.POST.get("password", None)

#     if not username or not password:
#         return JsonResponse({
#             "error": "Bad request"
#         }, status=400)

#     user: User = authenticate(username=username, password=password)

#     if user is None:
#         return JsonResponse({
#             "error": "Invalid username or password"
#         }, status=401)

#     login(request, user)

#     return JsonResponse({
#         "message": "Login good",
#         "username": user.username
#     }, status=200)

@csrf_exempt
def account_register(req: HttpRequest) -> JsonResponse:
    """
        Register a user if not exists, then generate a brand new JWT token.

        req:
            the HttpRequest object that contains the body and the headers of the request
        
        returns:
            A JsonResponse object with details and status code
    """
    if req.method != "POST":
        return JsonResponse({
            "error": "Method not allowed"
        }, status=405)

    payload: dict = get_payload(req)

    firstName: str        = payload.get("first_name", "")
    lastName : str        = payload.get("last_name", "")
    username : str | None = payload.get("username")
    password : str | None = payload.get("password")

    if not username or not password:
        return JsonResponse({
            "error": "Need an username and a password",
        }, status=400)

    if User.objects.filter(username=username).exists():
        return JsonResponse({
            "error": "Username already taken"
        }, status=400)

    user = User.objects.create_user(
        username=username,
        first_name=firstName,
        last_name=lastName,
        password=password
    )

    # NOTE: Create a JWT token for user
    token = RefreshToken.for_user(user)

    return JsonResponse({
        "message":"User successfully registered",
        "user": {
            "id": user.id,
            "username": user.username
        },
        "token": {
            "access": str(token.access_token),
            "refresh": str(token)
        }
    }, status=201)

@csrf_exempt
def account_get_token(req: HttpRequest) -> JsonResponse:
    """
        Authenticate a user if exists

        req:
            An HttpRequest object with all parameters of the request

        returns:
            A new JWT token (refreshed)
    """
    if req.method != "POST":
        return JsonResponse({
            "error": "Method not allowed"
        }, status=405)

    payload: dict = get_payload(req)

    username: str | None = payload.get("username")
    password: str | None = payload.get("password")

    if not username or not password:
        return JsonResponse({
            "error": "Need username and password"
        }, status=400)

    user: User = authenticate(username=username, password=password)

    if user is None:
        return JsonResponse({
            "error": "Invalid credentials"
        }, status=401)

    token: RefreshToken = RefreshToken.for_user(user)

    return JsonResponse({
        "message": "Ok",
        "token": {
            "access": str(token.access_token),
            "refresh": str(token)
        }
    }, status=200)

@require_jwt
def account_get_user(req: HttpRequest, user_id: int) -> JsonResponse:
    """
        Get a user by its id

        req:
            A HttpRequest object containing required datas

        user_id:
            The id of the user to get

        Returns:
            A JsonResponse containing return code (see http codes)
    """
    if req.method != 'GET':
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        user: User = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({
            "error": "User does not exists"
        }, status=404)

    return JsonResponse({
        "user": {
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name
        }
    }, status=200)
