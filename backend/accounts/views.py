from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.tokens import RefreshToken
from utils.get_payload import *
from .models import *

# Create your views here.

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
    """ Register user """
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
    """ Get token aha """
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
    }, status=201)
