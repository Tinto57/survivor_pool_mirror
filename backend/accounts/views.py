from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from django.contrib.auth.models import update_last_login
from django.db import transaction
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse

from partners.models import Partner
from .serializers import (
    LoginResponseSerializer,
    RegistrationResponseSerializer,
    UserSerializer,
    UserRegistrationSerializer,
)
from .permissions import IsOwnerOrAdmin, IsAdminRole

User = get_user_model()


@extend_schema_view(
    get=extend_schema(
        tags=["Utilisateurs"],
        summary="Lister les utilisateurs",
        description="Liste tous les comptes utilisateurs. Réservé aux administrateurs.",
        responses={200: UserSerializer(many=True)},
    ),
    post=extend_schema(
        tags=["Utilisateurs"],
        summary="Créer un compte (inscription)",
        description=(
            "Inscrit un nouveau compte salarié ou partenaire et renvoie immédiatement "
            "une paire de tokens JWT. Endpoint public, non authentifié. "
            "Un compte partenaire est créé avec le statut `pending` (à valider par un admin)."
        ),
        request=UserRegistrationSerializer,
        responses={
            201: RegistrationResponseSerializer,
            400: OpenApiResponse(description="Données invalides (mot de passe faible, rôle inconnu, SIREN invalide, fiche partenaire manquante...)."),
        },
    ),
)
class UsersView(generics.ListCreateAPIView):
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return UserRegistrationSerializer
        return UserSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [AllowAny()]
        return [IsAdminRole()]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        token = RefreshToken.for_user(user)

        response_data = {
            "message": "User successfully registered",
            "user": UserSerializer(user).data,
            "token": {
                "access": str(token.access_token),
                "refresh": str(token),
            },
        }

        if user.role == "partner":
            partner = Partner.objects.get(user=user)
            response_data["partner"] = {
                "id": partner.id,
                "business_name": partner.business_name,
                "status": partner.status,
            }

        return Response(response_data, status=status.HTTP_201_CREATED)


class UserMeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Utilisateurs"],
        summary="Consulter mon compte",
        description="Renvoie le compte de l'utilisateur actuellement authentifié.",
        responses={200: UserSerializer},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_object(self):
        return self.request.user


@extend_schema_view(
    get=extend_schema(
        tags=["Utilisateurs"],
        summary="Consulter un utilisateur",
        description="Consultable par son propriétaire ou par un administrateur.",
        responses={200: UserSerializer},
    ),
    patch=extend_schema(
        tags=["Utilisateurs"],
        summary="Mettre à jour un utilisateur",
        description="Modifiable par son propriétaire ou par un administrateur.",
        responses={200: UserSerializer},
    ),
    delete=extend_schema(
        tags=["Utilisateurs"],
        summary="Supprimer un utilisateur",
        description="Supprimable par son propriétaire ou par un administrateur.",
        responses={200: OpenApiResponse(description="Utilisateur supprimé avec succès.")},
    ),
)
class SingleUserView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    lookup_url_kwarg = "user_id"
    http_method_names = ["get", "patch", "delete"]

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        user_id = user.id
        user.delete()
        return Response(
            {"message": f"Successfully deleted user {user_id}"},
            status=status.HTTP_200_OK,
        )


class CustomTokenObtainPairView(TokenObtainPairView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Authentification"],
        summary="Se connecter (obtenir un token JWT)",
        description="Authentifie un utilisateur avec son nom d'utilisateur et son mot de passe, et renvoie une paire de tokens JWT.",
        responses={
            200: LoginResponseSerializer,
            401: OpenApiResponse(description="Identifiants invalides."),
        },
    )
    def post(self, request: Request, *args, **kwargs) -> Response:
        response: Response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            user = User.objects.get(username=request.data["username"])
            update_last_login(None, user)
            token_data = response.data
            response.data = {
                "message": "Ok",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "role": user.role,
                },
                "token": {
                    "access": token_data["access"],
                    "refresh": token_data["refresh"],
                },
            }
        return response
