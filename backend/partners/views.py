from django.db import transaction
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse
from rest_framework import generics, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAdminRole, is_admin_role
from config.serializers import ErrorDetailSerializer

from .models import Category, Partner, PartnerDecision
from .permissions import CanViewPartner, CanViewPartnerDecisions, IsPartnerOwnerOrAdmin
from .serializers import (
    CategorySerializer,
    PartnerDecisionCreateSerializer,
    PartnerDecisionSerializer,
    PartnerSerializer,
    PartnerUpdateSerializer,
)


@extend_schema_view(
    get=extend_schema(
        tags=["Partenaires"],
        summary="Lister les catégories",
        description="Public : nécessaire pour renseigner la fiche partenaire à l'inscription (`POST /users/`).",
        responses={200: CategorySerializer(many=True)},
    ),
    post=extend_schema(
        tags=["Partenaires"],
        summary="Créer une catégorie",
        description="Réservé aux administrateurs.",
        responses={201: CategorySerializer},
    ),
)
class CategoriesView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdminRole()]
        return [AllowAny()]


@extend_schema(
    tags=["Partenaires"],
    summary="Lister les partenaires (catalogue)",
    description=(
        "Pour un salarié ou un partenaire, ne renvoie que les partenaires actifs "
        "(le catalogue consultable). Un administrateur voit tous les partenaires quel "
        "que soit leur statut, et peut filtrer avec `status`."
    ),
    parameters=[
        OpenApiParameter("category", int, description="Filtrer par identifiant de catégorie."),
        OpenApiParameter("status", str, description="Filtrer par statut (`pending`, `active`, `suspended`, `closed`) — administrateurs uniquement."),
        OpenApiParameter("q", str, description="Recherche texte sur le nom de l'établissement."),
    ],
    responses={200: PartnerSerializer(many=True)},
)
class PartnersView(generics.ListAPIView):
    serializer_class = PartnerSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Partner.objects.select_related("category", "user").order_by("business_name")
        user = self.request.user

        if is_admin_role(user):
            status_param = self.request.query_params.get("status")
            if status_param:
                queryset = queryset.filter(status=status_param)
        else:
            queryset = queryset.filter(status="active")

        category_param = self.request.query_params.get("category")
        if category_param:
            if not category_param.isdigit():
                raise ValidationError({"category": "Doit être un identifiant numérique."})
            queryset = queryset.filter(category_id=category_param)

        query = self.request.query_params.get("q")
        if query:
            queryset = queryset.filter(business_name__icontains=query)

        return queryset


class PartnerMeView(generics.RetrieveAPIView):
    queryset = Partner.objects.select_related("category", "user").all()
    serializer_class = PartnerSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Partenaires"],
        summary="Consulter ma fiche partenaire",
        description="Renvoie la fiche partenaire de l'utilisateur actuellement authentifié, quel que soit son statut.",
        responses={
            200: PartnerSerializer,
            404: OpenApiResponse(response=ErrorDetailSerializer, description="L'utilisateur authentifié n'a pas de fiche partenaire."),
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_object(self):
        try:
            return self.queryset.get(user=self.request.user)
        except Partner.DoesNotExist:
            raise NotFound(detail="Partner does not exist for you")


@extend_schema_view(
    get=extend_schema(
        tags=["Partenaires"],
        summary="Consulter un partenaire",
        description=(
            "Consultable par tout utilisateur authentifié si le partenaire est actif, "
            "par le partenaire lui-même quel que soit son statut, ou par un administrateur."
        ),
        responses={
            200: PartnerSerializer,
            403: OpenApiResponse(response=ErrorDetailSerializer, description="Partenaire non actif, et ni le propriétaire ni un administrateur."),
            404: OpenApiResponse(response=ErrorDetailSerializer, description="Partenaire introuvable."),
        },
    ),
)
class SinglePartnerView(generics.RetrieveUpdateAPIView):
    queryset = Partner.objects.select_related("category", "user").all()
    lookup_url_kwarg = "partner_id"
    http_method_names = ["get", "patch"]

    def get_permissions(self):
        if self.request.method == "PATCH":
            return [IsAuthenticated(), IsPartnerOwnerOrAdmin()]
        return [IsAuthenticated(), CanViewPartner()]

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return PartnerUpdateSerializer
        return PartnerSerializer

    @extend_schema(
        tags=["Partenaires"],
        summary="Mettre à jour la fiche partenaire",
        description=(
            "Modifiable par le partenaire lui-même ou par un administrateur. "
            "Le statut ne se modifie pas ici : voir `POST /partners/{id}/decision/`."
        ),
        request=PartnerUpdateSerializer,
        responses={
            200: PartnerSerializer,
            400: OpenApiResponse(response=ErrorDetailSerializer, description="Données invalides."),
        },
    )
    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(PartnerSerializer(instance).data, status=status.HTTP_200_OK)


class PartnerDecisionCreateView(APIView):
    permission_classes = [IsAdminRole]

    @extend_schema(
        tags=["Partenaires"],
        summary="Accepter ou refuser une demande de référencement",
        description=(
            "Statue sur une fiche partenaire en attente (`pending`) : elle passe en "
            "statut `active` si la décision est `accepted`, `closed` si elle est "
            "`rejected`. La décision est archivée (agent, motif, date) et ne peut être "
            "prise qu'une seule fois par demande. Réservé aux administrateurs."
        ),
        request=PartnerDecisionCreateSerializer,
        responses={
            201: PartnerDecisionSerializer,
            400: OpenApiResponse(response=ErrorDetailSerializer, description="Cette demande a déjà été traitée, ou motif de refus manquant."),
            404: OpenApiResponse(response=ErrorDetailSerializer, description="Partenaire introuvable."),
        },
    )
    @transaction.atomic
    def post(self, request, partner_id):
        try:
            partner = Partner.objects.select_for_update().get(id=partner_id)
        except Partner.DoesNotExist:
            return Response({"detail": "Partenaire introuvable."}, status=status.HTTP_404_NOT_FOUND)

        if partner.status != "pending":
            return Response(
                {"detail": "Cette demande a déjà été traitée."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = PartnerDecisionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        decision_value = serializer.validated_data["decision"]
        reason = serializer.validated_data.get("reason", "")

        partner.status = "active" if decision_value == "accepted" else "closed"
        partner.save(update_fields=["status"])

        decision = PartnerDecision.objects.create(
            partner=partner,
            decision=decision_value,
            reason=reason,
            agent=request.user,
        )
        return Response(PartnerDecisionSerializer(decision).data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["Partenaires"],
    summary="Historique des décisions d'un partenaire",
    description="Consultable par le partenaire concerné ou par un administrateur.",
    responses={200: PartnerDecisionSerializer(many=True)},
)
class PartnerDecisionsListView(generics.ListAPIView):
    serializer_class = PartnerDecisionSerializer
    permission_classes = [IsAuthenticated, CanViewPartnerDecisions]

    def get_queryset(self):
        partner = generics.get_object_or_404(Partner, id=self.kwargs["partner_id"])
        return PartnerDecision.objects.filter(partner=partner).select_related("agent").order_by("-created_at")
