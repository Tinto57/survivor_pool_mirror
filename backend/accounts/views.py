from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import *
from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt

# Create your views here.

@csrf_exempt
def account_login(request: HttpRequest) -> JsonResponse:
    """ Login user (ensure user exists, valid pwd...) """
    if request.method != "POST":
        return JsonResponse({
            "error": "Method not allowed"
        }, status=405)

    username: str | None = request.POST.get("username", None)
    password: str | None = request.POST.get("password", None)

    if not username or not password:
        return JsonResponse({
            "error": "Bad request"
        }, status=400)

    user: User = authenticate(username=username, password=password)

    if user is None:
        return JsonResponse({
            "error": "Invalid username or password"
        }, status=401)

    login(request, user)

    return JsonResponse({
        "message": "Login good",
        "username": user.username
    }, status=200)


@csrf_exempt
def account_register(req: HttpRequest) -> JsonResponse:
    """ Register user """
    if req.method != "POST":
        messages.error(req, "Error: not POST method")
        return JsonResponse({
            "error":"Method not allowed"
        }, status=405)

    firstName: str        = req.POST.get('first_name', '')
    lastName : str        = req.POST.get('last_name', '')
    username : str | None = req.POST.get('username', None)
    password : str | None = req.POST.get('password', None)

    if not username or not password:
        return JsonResponse({
            "error":"Bad request",
        }, status=400)

    if User.objects.filter(username=username).exists():
        messages.error(req, "Error: User already exists")
        return JsonResponse({
            "error": "Username already taken"
        }, status=400)

    User.objects.create_user(
        username=username,
        first_name=firstName,
        last_name=lastName,
        password=password
    )

    return JsonResponse({
        "message":"Register good"
    }, status=201)
