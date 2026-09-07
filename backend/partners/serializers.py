from rest_framework import serializers

from .models import Category, MinisterSpotlight, Partner, PartnerDecision


class CategorySerializer(serializers.ModelSerializer):
    """Catégorie de partenaire (ex : Restauration, Mobilité...)."""

    class Meta:
        model = Category
        fields = ["id", "name"]


class PartnerSerializer(serializers.ModelSerializer):
    """Fiche partenaire complète, telle que renvoyée par le catalogue ou à l'administration."""

    category = CategorySerializer(read_only=True)

    class Meta:
        model = Partner
        fields = [
            "id",
            "user",
            "business_name",
            "business_purpose",
            "siren",
            "category",
            "address",
            "latitude",
            "longitude",
            "status",
            "is_featured",
            "registered_at",
        ]
        read_only_fields = list(fields)
        extra_kwargs = {
            "user": {"help_text": "Identifiant du compte utilisateur (rôle `partner`) propriétaire de cette fiche."},
            "status": {"help_text": "`pending`, `active`, `suspended` ou `closed`. Se modifie via POST /partners/{id}/decision/."},
            "is_featured": {"help_text": "Mis en avant dans le catalogue."},
        }


class PartnerUpdateSerializer(serializers.ModelSerializer):
    """Payload de mise à jour de la fiche partenaire.

    Le statut ne se modifie pas ici : voir `POST /partners/{id}/decision/`.
    """

    class Meta:
        model = Partner
        fields = ["business_name", "business_purpose", "address", "latitude", "longitude", "category"]
        extra_kwargs = {
            "business_name": {"help_text": "Raison sociale de l'établissement."},
            "business_purpose": {"help_text": "Description de l'activité du partenaire."},
            "address": {"help_text": "Adresse postale complète de l'établissement."},
            "latitude": {"help_text": "Latitude GPS de l'établissement."},
            "longitude": {"help_text": "Longitude GPS de l'établissement."},
            "category": {"help_text": "Identifiant de la nouvelle catégorie."},
        }


class PartnerDecisionCreateSerializer(serializers.Serializer):
    """Payload de décision (acceptation ou refus) d'une demande de référencement."""

    decision = serializers.ChoiceField(
        choices=PartnerDecision.DECISION_CHOICES,
        help_text="`accepted` (le partenaire passe en statut `active`) ou `rejected` (il passe en statut `closed`).",
    )
    reason = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Motif de la décision. Obligatoire si `decision` vaut `rejected`.",
    )

    def validate(self, attrs):
        if attrs["decision"] == "rejected" and not attrs.get("reason"):
            raise serializers.ValidationError({"reason": "Un motif est requis en cas de refus."})
        return attrs


class PartnerDecisionSerializer(serializers.ModelSerializer):
    """Décision de référencement archivée (traçabilité)."""

    agent = serializers.SerializerMethodField(
        help_text="Nom d'utilisateur de l'agent, ou `null` si l'agent a depuis été dissocié (politique de rétention)."
    )

    class Meta:
        model = PartnerDecision
        fields = ["id", "partner", "decision", "reason", "agent", "created_at"]
        read_only_fields = list(fields)

    def get_agent(self, obj: PartnerDecision) -> str | None:
        return obj.agent.username if obj.agent_id else None


class SpotlightPartnerSerializer(serializers.ModelSerializer):
    """Fiche partenaire allégée, telle qu'affichée dans le Coup de cœur du Ministre."""

    category = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Partner
        fields = ["id", "business_name", "category", "address"]
        read_only_fields = list(fields)


class MinisterSpotlightPublicSerializer(serializers.ModelSerializer):
    """Coup de cœur du Ministre tel que visible publiquement (sans le compteur de clics)."""

    partner = SpotlightPartnerSerializer(read_only=True)

    class Meta:
        model = MinisterSpotlight
        fields = ["id", "partner", "message", "is_active", "published_at"]
        read_only_fields = list(fields)


class MinisterSpotlightSerializer(serializers.ModelSerializer):
    """Publication du Coup de cœur du Ministre, avec ses statistiques (vue admin)."""

    partner = SpotlightPartnerSerializer(read_only=True)
    published_by = serializers.SerializerMethodField(
        help_text="Nom d'utilisateur de l'administrateur ayant publié cette entrée."
    )

    class Meta:
        model = MinisterSpotlight
        fields = ["id", "partner", "message", "is_active", "click_count", "published_by", "published_at"]
        read_only_fields = list(fields)

    def get_published_by(self, obj: MinisterSpotlight) -> str | None:
        return obj.published_by.username if obj.published_by_id else None


class MinisterSpotlightCreateSerializer(serializers.Serializer):
    """Payload de publication d'un nouveau Coup de cœur du Ministre."""

    partner = serializers.PrimaryKeyRelatedField(
        queryset=Partner.objects.filter(status="active"),
        help_text="Identifiant du partenaire actif à mettre en avant.",
    )
    message = serializers.CharField(
        max_length=280,
        help_text="Message du Ministre accompagnant la mise en avant (deux lignes environ).",
    )
