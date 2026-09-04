import re
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from django.contrib.auth import get_user_model
from partners.models import Category, Partner

User = get_user_model()
PUBLIC_ROLES = ("employee", "partner")
DEFAULT_PARTNER_CATEGORY = "Non catégorisé"


class PartnerRegistrationSerializer(serializers.ModelSerializer):
    """Données de la fiche partenaire à fournir lors de l'inscription d'un compte partenaire."""

    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        required=False,
        help_text="Identifiant de la catégorie du partenaire. Si omise, une catégorie « Non catégorisé » est utilisée.",
    )

    class Meta:
        model = Partner
        fields = [
            "business_name",
            "siren",
            "business_purpose",
            "address",
            "latitude",
            "longitude",
            "category",
        ]
        extra_kwargs = {
            "business_name": {"required": True, "help_text": "Raison sociale de l'établissement."},
            "siren": {"required": True, "help_text": "Numéro SIREN de l'entreprise (9 chiffres)."},
            "business_purpose": {"required": True, "help_text": "Description de l'activité du partenaire."},
            "address": {"required": True, "help_text": "Adresse postale complète de l'établissement."},
            "latitude": {"help_text": "Latitude GPS de l'établissement (optionnel)."},
            "longitude": {"help_text": "Longitude GPS de l'établissement (optionnel)."},
        }

    def validate_siren(self, value):
        if not re.fullmatch(r"\d{9}", str(value)):
            raise serializers.ValidationError("SIREN must contain exactly 9 digits")
        return value


class UserSerializer(serializers.ModelSerializer):
    """Représentation publique d'un compte utilisateur."""

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email", "date_joined", "role"]
        read_only_fields = ["id", "username", "date_joined", "role"]


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Payload d'inscription d'un nouveau compte (salarié ou partenaire)."""

    partner = PartnerRegistrationSerializer(
        required=False,
        help_text="Obligatoire et pris en compte uniquement si `role` vaut `partner`.",
    )
    password = serializers.CharField(
        write_only=True,
        help_text="Mot de passe en clair, soumis à la politique de sécurité Django (longueur, complexité...).",
    )

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email", "role", "password", "partner"]
        extra_kwargs = {
            "role": {"help_text": "Rôle du compte à créer : `employee` ou `partner` (`admin` non ouvert à l'inscription)."},
        }

    def validate_role(self, value):
        if value not in PUBLIC_ROLES:
            raise serializers.ValidationError("Invalid role")
        return value

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        role = attrs.get("role")
        partner_data = attrs.get("partner")

        if role == "partner" and not partner_data:
            raise serializers.ValidationError({"partner": "Partner data is required for partner role"})
        return attrs

    def create(self, validated_data):
        partner_data = validated_data.pop("partner", None)
        password = validated_data.pop("password")

        user = User.objects.create_user(**validated_data, password=password)

        if user.role == "partner" and partner_data:
            if not partner_data.get("category"):
                category, _ = Category.objects.get_or_create(name=DEFAULT_PARTNER_CATEGORY)
                partner_data["category"] = category
            Partner.objects.create(user=user, status="pending", **partner_data)
        return user


class TokenPairSerializer(serializers.Serializer):
    """Paire de tokens JWT."""

    access = serializers.CharField(help_text="Token d'accès JWT, à envoyer dans l'en-tête `Authorization: Bearer <access>`.")
    refresh = serializers.CharField(help_text="Token de rafraîchissement JWT.")


class PartnerSummarySerializer(serializers.Serializer):
    """Résumé du partenaire créé, renvoyé lors de l'inscription."""

    id = serializers.IntegerField()
    business_name = serializers.CharField()
    status = serializers.ChoiceField(choices=Partner.STATUS_CHOICE)


class RegistrationResponseSerializer(serializers.Serializer):
    """Réponse renvoyée après inscription d'un compte."""

    message = serializers.CharField()
    user = UserSerializer()
    token = TokenPairSerializer()
    partner = PartnerSummarySerializer(
        required=False,
        help_text="Présent uniquement si le compte inscrit est un partenaire.",
    )


class UserSummarySerializer(serializers.Serializer):
    """Résumé de l'utilisateur, renvoyé lors de la connexion."""

    id = serializers.IntegerField()
    username = serializers.CharField()
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES)


class LoginResponseSerializer(serializers.Serializer):
    """Réponse renvoyée après une authentification réussie."""

    message = serializers.CharField()
    user = UserSummarySerializer()
    token = TokenPairSerializer()
