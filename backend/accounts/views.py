from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import *
from django.http.request import HttpRequest

# Create your views here.

def account_login(request: HttpRequest) -> None:
    """ Login user (ensure user exists, valid pwd...) """
    if (request.method == "POST"):
        username = request.POST.get("login")
        password = request.POST.get("password")
        if not User.objects.filter(username=login).exists():
            messages.error(request, f"Cannot find user {username}")
            # FIXME: Redirect to register API ?
            raise TypeError(f"Cannot find user {username}")
        user: User = authenticate(username=username, password=password)
        if user is None:
            messages.error(request, "Invalid username or password")
            raise TypeError("Invalid username or password")
        else:
            login(request, user)
    else:
        raise TypeError("Login request should be a POST")

def account_register(req: HttpRequest) -> None:
    """ Register user """
    if (req.method == "POST"):
        firstName = req.POST.get('first_name')
        lastName  = req.POST.get('last_name')
        username  = req.POST.get('username')
        password  = req.POST.get('password')

        if not User.objects.filter(username=username).exists():
            messages.error(req, "Error: User already exists")
            raise TypeError("Error error")
        user = User.objects.create(
            username=username,
            first_name=firstName,
            last_name=lastName,
            password=password
        ).save()
        messages.info("Ok bro ehe")
    else:
        messages.error(req, "Error: not POST method")
        raise TypeError("Error error")
