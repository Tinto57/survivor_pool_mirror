import re
from rest_framework import serializers
from django.contrib.auth import get_user_model
from partners.models import Partner

User = get_user_model()
PUBLIC_ROLES = ('employee', 'partner')

class PartnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Partner
        fields = ["business_name", "siren", "business_purpose", "address", "latitude", "longitude"]
        extra_kwargs = {
            "business_name": {"required": True},
            "siren": {"required": True},
            "business_purpose": {"required": True},
            "address": {"required": True},
        }

    def validate_siren(self, value):
        if not re.fullmatch(r"\d{9}", str(value)):
            raise serializers.ValidationError("SIREN must contain exactly 9 digits")
        return value


class UserSerializer(serializers.ModelSerializer):
    """Pour la lecture et la mise à jour (GET, PATCH)."""
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email", "date_joined", "role"]
        read_only_fields = ["id", "username", "date_joined", "role"]

class UserRegistrationSerializer(serializers.ModelSerializer):
    """Gère l'inscription complexe (POST) avec création de Partenaire imbriquée."""
    partner = PartnerSerializer(required=False)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email", "role", "password", "partner"]

    def validate_role(self, value):
        if value not in PUBLIC_ROLES:
            raise serializers.ValidationError("Invalid role")
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
            Partner.objects.create(user=user, status="pending", **partner_data)
        return user
