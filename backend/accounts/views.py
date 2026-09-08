from django.db.models.deletion import ProtectedError
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

from audit.request_context import actor_info, get_client_ip
from audit.services import record_audit_event
from config.serializers import ErrorDetailSerializer
from partners.models import Partner
from .serializers import (
    LoginResponseSerializer,
    RegistrationResponseSerializer,
    UserSerializer,
    UserRegistrationSerializer,
    UserRoleUpdateSerializer,
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
            400: OpenApiResponse(response=ErrorDetailSerializer, description="Données invalides (mot de passe faible, rôle inconnu, SIREN invalide, fiche partenaire manquante...)."),
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

        record_audit_event(
            actor_id=user.id,
            actor_role=user.role,
            action="ACCOUNT_CREATED",
            target_type="User",
            target_id=user.id,
            payload={"username": user.username, "role": user.role},
            ip=get_client_ip(request),
        )

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
        responses={
            204: OpenApiResponse(description="Utilisateur supprimé avec succès."),
            409: OpenApiResponse(response=ErrorDetailSerializer, description="Des transactions sont rattachées au salarié ou au partenaire lié à ce compte."),
        },
    ),
)
class SingleUserView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    lookup_url_kwarg = "user_id"
    http_method_names = ["get", "patch", "delete"]

    TRACKED_FIELDS = ("first_name", "last_name", "email")

    def perform_update(self, serializer):
        before = {field: getattr(serializer.instance, field) for field in self.TRACKED_FIELDS}
        instance = serializer.save()
        changed = {
            field: {"before": before[field], "after": getattr(instance, field)}
            for field in self.TRACKED_FIELDS
            if before[field] != getattr(instance, field)
        }
        if changed:
            actor_id, actor_role = actor_info(self.request)
            record_audit_event(
                actor_id=actor_id,
                actor_role=actor_role,
                action="ACCOUNT_UPDATED",
                target_type="User",
                target_id=instance.id,
                payload={"changed_fields": changed},
                ip=get_client_ip(self.request),
            )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            instance.delete()
        except ProtectedError:
            return Response(
                {"detail": "Impossible de supprimer ce compte : des transactions sont rattachées au salarié ou au partenaire lié."},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    patch=extend_schema(
        tags=["Utilisateurs"],
        summary="Changer le rôle d'un compte",
        description=(
            "Modifie le rôle (`employee`, `partner`, `admin`) d'un compte existant. "
            "Réservé aux administrateurs. Ne crée ni ne modifie la fiche "
            "`Employee`/`Partner` associée."
        ),
        request=UserRoleUpdateSerializer,
        responses={200: UserSerializer},
    ),
)
class UserRoleUpdateView(generics.UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRoleUpdateSerializer
    permission_classes = [IsAdminRole]
    lookup_url_kwarg = "user_id"
    http_method_names = ["patch"]

    def perform_update(self, serializer):
        old_role = serializer.instance.role
        instance = serializer.save()
        if instance.role != old_role:
            actor_id, actor_role = actor_info(self.request)
            record_audit_event(
                actor_id=actor_id,
                actor_role=actor_role,
                action="ROLE_CHANGED",
                target_type="User",
                target_id=instance.id,
                payload={"before": old_role, "after": instance.role},
                ip=get_client_ip(self.request),
            )

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(UserSerializer(serializer.instance).data, status=status.HTTP_200_OK)


class CustomTokenObtainPairView(TokenObtainPairView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Authentification"],
        summary="Se connecter (obtenir un token JWT)",
        description="Authentifie un utilisateur avec son nom d'utilisateur et son mot de passe, et renvoie une paire de tokens JWT.",
        responses={
            200: LoginResponseSerializer,
            401: OpenApiResponse(response=ErrorDetailSerializer, description="Identifiants invalides."),
        },
    )
    def post(self, request: Request, *args, **kwargs) -> Response:
        try:
            response: Response = super().post(request, *args, **kwargs)
        except Exception:
            record_audit_event(
                actor_id=None,
                actor_role="",
                action="LOGIN_FAILED",
                target_type="User",
                target_id=None,
                payload={"username": request.data.get("username", "")},
                ip=get_client_ip(request),
            )
            raise

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
