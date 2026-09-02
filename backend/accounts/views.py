# from rest_framework_simplejwt.tokens import RefreshToken
# from django.views.decorators.csrf import csrf_exempt
# from django.http import HttpRequest, JsonResponse
# from django.contrib.auth import authenticate
# from django.db import transaction
# from partners.models import Partner
# from utils.get_payload import get_payload
# from utils.wrappers import require_jwt
# from .models import *
# from django.views import View
# from django.utils.decorators import method_decorator
# import re

# PUBLIC_ROLES: tuple = ('employee', 'partner')

# def check_partner_payload(payload: dict) -> str | None:
#     """
#     Verify the company details sent by a partner applicant.

#     payload:
#         The "partner" object of the registration body

#     returns:
#         An error message, or None if everything is valid
#     """
#     for field in ("business_name", "siren", "business_purpose", "address"):
#         if not payload.get(field):
#             return "Missing partner field: %s" % field

#     if not re.fullmatch(r"\d{9}", str(payload.get("siren"))):
#         return "SIREN must contain exactly 9 digits"

#     for field in ("latitude", "longitude"):
#         value = payload.get(field)

#         if value is not None and not isinstance(value, (int, float)):
#             return "Invalid partner field: %s" % field

#     return None


# @method_decorator(csrf_exempt, name='dispatch')
# class UsersView(View):
#     @method_decorator(require_jwt)
#     def get(
#             self: "UsersView",
#             req: HttpRequest
#         ) -> JsonResponse:
#         """
#         Register a user if not exists, then generate a brand new JWT token.

#             req:
#                 A HttpRequest object containing required datas

#             returns:
#                 A JsonResponse object with message and status 
#         """
#         users: list[dict] = User.objects.all().values("id", "username", "last_name", "first_name", "email", "date_joined")
#         return JsonResponse({
#             "users": list(users)
#         }, status=200)

#     def post(
#             self,
#             req: HttpRequest
#         ) -> JsonResponse:
#         """
#             Register a user if not exists, then generate a brand new JWT token.

#             req:
#                 the HttpRequest object that contains the body and the headers of the request
            
#             returns:
#                 A JsonResponse object with details and status code
#         """
#         payload: dict = get_payload(req)

#         firstName: str        = payload.get("first_name", "")
#         lastName : str        = payload.get("last_name", "")
#         email    : str        = payload.get("email", "")
#         username : str | None = payload.get("username")
#         password : str | None = payload.get("password")
#         role     : str | None = payload.get("role")

#         if not username or not password:
#             return JsonResponse({
#                 "error": "Need an username and a password",
#             }, status=400)

#         if role not in PUBLIC_ROLES:
#             return JsonResponse({
#                 "error": "Invalid role"
#             }, status=400)

#         if User.objects.filter(username=username).exists():
#             return JsonResponse({
#                 "error": "Username already taken"
#             }, status=400)

#         partnerPayload: dict = payload.get("partner") or {}

#         if role == "partner":
#             error: str | None = check_partner_payload(partnerPayload)

#             if error is not None:
#                 return JsonResponse({
#                     "error": error
#                 }, status=400)

#         with transaction.atomic():
#             user = User.objects.create_user(
#                 username=username,
#                 first_name=firstName,
#                 last_name=lastName,
#                 email=email,
#                 role=role,
#                 password=password
#             )

#             partner: Partner | None = None

#             if role == "partner":
#                 partner = Partner.objects.create(
#                     user=user,
#                     status="pending",
#                     business_name=partnerPayload.get("business_name"),
#                     siren=partnerPayload.get("siren"),
#                     business_purpose=partnerPayload.get("business_purpose"),
#                     address=partnerPayload.get("address"),
#                     latitude=partnerPayload.get("latitude"),
#                     longitude=partnerPayload.get("longitude")
#                 )

#         token = RefreshToken.for_user(user)

#         body: dict = {
#             "message":"User successfully registered",
#             "user": {
#                 "id": user.id,
#                 "username": user.username,
#                 "role": user.role
#             },
#             "token": {
#                 "access": str(token.access_token),
#                 "refresh": str(token)
#             }
#         }

#         if partner is not None:
#             body["partner"] = {
#                 "id": partner.id,
#                 "business_name": partner.business_name,
#                 "status": partner.status
#             }

#         return JsonResponse(body, status=201)

# # FIXME: Crsf_exempt needed ?
# @csrf_exempt
# def account_get_token(req: HttpRequest) -> JsonResponse:
#     """
#         Authenticate a user if exists

#         req:
#             An HttpRequest object with all parameters of the request

#         returns:
#             A new JWT token (refreshed)
#     """
#     if req.method != "POST":
#         return JsonResponse({
#             "error": "Method not allowed"
#         }, status=405)

#     payload: dict = get_payload(req)

#     username: str | None = payload.get("username")
#     password: str | None = payload.get("password")

#     if not username or not password:
#         return JsonResponse({
#             "error": "Need username and password"
#         }, status=400)

#     user: User = authenticate(username=username, password=password)

#     if user is None:
#         return JsonResponse({
#             "error": "Invalid credentials"
#         }, status=401)

#     token: RefreshToken = RefreshToken.for_user(user)

#     return JsonResponse({
#         "message": "Ok",
#         "user": {
#             "id": user.id,
#             "username": user.username,
#             "role": user.role
#         },
#         "token": {
#             "access": str(token.access_token),
#             "refresh": str(token)
#         }
#     }, status=200)

# @require_jwt
# def account_get_self(req: HttpRequest) -> JsonResponse:
#     """ Get self """
#     if req.method != "GET":
#         return JsonResponse({"error": "Method not allowed"}, status=405)

#     user: User = req.user;

#     return JsonResponse({
#         "user": {
#             "id": user.id,
#             "username": user.username,
#             "first_name": user.first_name,
#             "last_name": user.last_name,
#             "email": user.email,
#             "joined_at": user.date_joined
#         }
#     }, status=200)

# @method_decorator(csrf_exempt, name='dispatch')
# class SingleUserView(View):
#     @method_decorator(require_jwt)
#     def get(
#             self: "SingleUserView",
#             req: HttpRequest,
#             user_id: int
#         ) -> JsonResponse:
#         """
#             Get a user by its id

#             req:
#                 A HttpRequest object containing required datas

#             user_id:
#                 The id of the user to get

#             Returns:
#                 A JsonResponse containing return code (see http codes)
#         """
#         try:
#             user: User = User.objects.get(id=user_id)
#         except User.DoesNotExist:
#             return JsonResponse({
#                 "error": "User does not exists"
#             }, status=404)

#         return JsonResponse({
#             "user": {
#                 "id": user.id,
#                 "username": user.username,
#                 "first_name": user.first_name,
#                 "last_name": user.last_name,
#                 "email": user.email,
#                 "joined_at": user.date_joined
#             }
#         }, status=200)


#     @method_decorator(require_jwt)
#     def delete(
#             self: "SingleUserView",
#             req: HttpRequest,
#             user_id: int
#         ) -> JsonResponse:
#         """
#             Delete a user by its id

#             req:
#                 A HttpRequest containing all the data

#             user_id:
#                 The id of the user to delete

#             returns:
#                 A JsonResponse with status and details
#         """
#         try:
#             user: User = User.objects.get(id=user_id)
#         except User.DoesNotExist:
#             return JsonResponse({
#                 "error": "User does not exists"
#             }, status=400)

#         if user_id != req.user.id and not req.user.is_superuser:
#             return JsonResponse({
#                 "error": "Forbidden"
#             }, status=403)

#         user.delete()

#         return JsonResponse({
#             "message": f"Successfully deleted user {user_id}"
#         }, status=200)

#     @method_decorator(require_jwt)
#     def patch(
#             self: "SingleUserView",
#             req: HttpRequest,
#             user_id: int
#         ) -> JsonResponse:
#         """
#             Modify email, last name and first name of a user.

#             req:
#                 HttpRequest blabla

#             user_id:
#                 The id of the user to alterate

#             returns:
#                 JsonResponse
#         """
#         try:
#             user: User = User.objects.get(id=user_id)
#         except User.DoesNotExist:
#             return JsonResponse({
#                 "error": "User does not exists"
#             }, status=400)

#         if user_id != req.user.id and not req.user.is_superuser:
#             return JsonResponse({
#                 "error": "Forbidden"
#             }, status=403)

#         payload = get_payload(req)

#         user.first_name = payload.get("first_name", user.first_name)
#         user.last_name  = payload.get("last_name", user.last_name)
#         user.email      = payload.get("email", user.email)

#         user.save()

#         return JsonResponse({
#             "message": "ok",
#             "user": {
#                 "id": user.id,
#                 "username": user.username,
#                 "last_name": user.last_name,
#                 "first_name": user.first_name,
#                 "email": user.email,
#                 "joined_at": user.date_joined,
#                 "role": user.role
#             }}, status=200)

from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from django.db import transaction

from partners.models import Partner
from .serializers import UserSerializer, UserRegistrationSerializer
from .permissions import IsOwnerOrStaff

User = get_user_model()

class UsersView(generics.ListCreateAPIView):
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserRegistrationSerializer
        return UserSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [AllowAny()]
        return [IsAuthenticated()]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Surcharge pour formater la réponse exacte attendue (Token + User + Partner)."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        token = RefreshToken.for_user(user)

        response_data = {
            "message": "User successfully registered",
            "user": UserSerializer(user).data,
            "token": {
                "access": str(token.access_token),
                "refresh": str(token)
            }
        }
        
        if user.role == "partner":
            partner = Partner.objects.get(user=user)
            response_data["partner"] = {
                "id": partner.id,
                "business_name": partner.business_name,
                "status": partner.status
            }

        return Response(response_data, status=status.HTTP_201_CREATED)


class UserMeView(generics.RetrieveAPIView):
    """Remplace account_get_self."""
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class SingleUserView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrStaff]
    lookup_url_kwarg = "user_id"
    http_method_names = ['get', 'patch', 'delete']

    def destroy(self, request, *args, **kwargs):
        """Surcharge optionnelle pour renvoyer un message JSON au lieu d'un 204 vide."""
        user = self.get_object()
        user_id = user.id
        user.delete()
        return Response({
            "message": f"Successfully deleted user {user_id}"
        }, status=status.HTTP_200_OK)

class CustomTokenObtainPairView(TokenObtainPairView):
    """Remplace account_get_token pour inclure les données utilisateur dans la réponse."""
    def post(
            self   : "CustomTokenObtainPairView",
            request:  Request,
            *args,
            **kwargs
        ) -> Response:
        response: Response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            user = User.objects.get(username=request.data["username"])
            token_data = response.data
            response.data = {
                "message": "Ok",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "role": user.role
                },
                "token": {
                    "access": token_data["access"],
                    "refresh": token_data["refresh"]
                }
            }
        return response
