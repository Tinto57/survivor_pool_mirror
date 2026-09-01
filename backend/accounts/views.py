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
    if (request.method != "POST"):
        return JsonResponse({
            "error": "Method not allowed"
        }, status=405)

    username: str | None = request.POST.get("username", None)
    password: str | None = request.POST.get("password", None)

    # if not username or not password:
    #     return JsonResponse({
    #         "error": "You must provide username or password"
    #     }, status=401)

    # NOTE: Authenticate already check if exists ?
    # if not User.objects.filter(username=username).exists():
    #     messages.error(request, f"Cannot find user {username}")
    #     return JsonResponse({"error": "Invalid username or password"}, status=401)

    user: User = authenticate(username=username, password=password)

    if user is None:
        messages.error(request, "Invalid username or password")
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
    if (req.method == "POST"):
        firstName = req.POST.get('first_name', '')
        lastName  = req.POST.get('last_name', '')
        username  = req.POST.get('username')
        password  = req.POST.get('password')

        if User.objects.filter(username=username).exists():
            messages.error(req, "Error: User already exists")
            raise TypeError("Error error")
        user = User.objects.create_user(
            username=username,
            first_name=firstName,
            last_name=lastName,
            password=password
        ).save()
        messages.info("Ok bro ehe")
        return Response(200)
    else:
        messages.error(req, "Error: not POST method")
        raise TypeError("Error error")
