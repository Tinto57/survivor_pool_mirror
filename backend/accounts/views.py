from rest_framework_simplejwt.tokens import RefreshToken
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpRequest, JsonResponse
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from utils.get_payload import get_payload
from utils.wrappers import require_jwt
from .models import *
from django.views import View
from django.utils.decorators import method_decorator

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

@method_decorator(csrf_exempt, name='dispatch')
class UsersView(View):
    @method_decorator(require_jwt)
    def get(
            self: "UsersView",
            req: HttpRequest
        ) -> JsonResponse:
        """
            Get a list of all users existing

            req:
                A HttpRequest object containing required datas

            returns:
                A JsonResponse object with message and status 
        """
        users: list[dict] = User.objects.all().values("id", "username", "last_name", "first_name", "email", "date_joined")
        return JsonResponse({
            "users": list(users)
        }, status=200)

    def post(
            self,
            req: HttpRequest
        ) -> JsonResponse:
        """
            Register a user if not exists, then generate a brand new JWT token.

            req:
                the HttpRequest object that contains the body and the headers of the request
            
            returns:
                A JsonResponse object with details and status code
        """
        payload: dict = get_payload(req)

        firstName: str        = payload.get("first_name", "")
        lastName : str        = payload.get("last_name", "")
        email    : str        = payload.get("email", "")
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
            password=password,
            email=email
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

# FIXME: Crsf_exempt needed ?
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

@method_decorator(csrf_exempt, name='dispatch')
class SingleUserView(View):
    @method_decorator(require_jwt)
    def get(
            self: "SingleUserView",
            req: HttpRequest,
            user_id: int
        ) -> JsonResponse:
        """
            Get a user by its id

            req:
                A HttpRequest object containing required datas

            user_id:
                The id of the user to get

            Returns:
                A JsonResponse containing return code (see http codes)
        """
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
                "last_name": user.last_name,
                "email": user.email,
                "joined_at": user.date_joined
            }
        }, status=200)

    @method_decorator(require_jwt)
    def delete(
            self: "SingleUserView",
            req: HttpRequest,
            user_id: int
        ) -> JsonResponse:
        """
            Delete a user by its id

            req:
                A HttpRequest containing all the data

            user_id:
                The id of the user to delete

            returns:
                A JsonResponse with status and details
        """
        try:
            user: User = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({
                "error": "User does not exists"
            }, status=400)

        # TODO: Add a check to know if the user is admin
        user.delete()

        return JsonResponse({
            "message": f"Successfully deleted user {user_id}"
        }, status=200)

    @method_decorator(require_jwt)
    def patch(
            self: "SingleUserView",
            req: HttpRequest,
            user_id: int
        ) -> JsonResponse:
        """
            Modify email, last name and first name of a user.

            req:
                HttpRequest blabla

            user_id:
                The id of the user to alterate

            returns:
                JsonResponse
        """
        try:
            user: User = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({
                "error": "User does not exists"
            }, status=400)

        payload = get_payload(req)

        user.first_name = payload.get("first_name", user.first_name)
        user.last_name  = payload.get("last_name", user.last_name)
        user.email      = payload.get("email", user.email)

        user.save()

        return JsonResponse({
            "message": "ok",
            "user": {
                "id": user.id,
                "username": user.username,
                "last_name": user.last_name,
                "first_name": user.first_name,
                "email": user.email,
                "joined_at": user.date_joined
            }
        }, status=200)
