from rest_framework import serializers
from decimal import Decimal

from wallet.models import Employee


class EmployeeSerializer(serializers.ModelSerializer):
    """Fiche salarié complète."""

    class Meta:
        model = Employee
        fields = ["id", "user", "balance", "employer"]
        read_only_fields = ["id", "balance"]
        extra_kwargs = {
            "user": {"help_text": "Identifiant du compte utilisateur (rôle `employee`) rattaché à ce salarié."},
            "employer": {"help_text": "Nom de l'employeur du salarié."},
        }


class EmployeeBalanceReadSerializer(serializers.ModelSerializer):
    """Solde d'un salarié."""

    class Meta:
        model = Employee
        fields = ["id", "balance"]
        read_only_fields = ["id", "balance"]


class EmployeeBalanceUpdateSerializer(serializers.Serializer):
    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.01"),
        help_text="Montant positif à créditer",
    )

    def update(self, instance: Employee, validated_data: dict) -> Employee:
        amount = validated_data["amount"]
        instance.balance += amount
        instance.save(update_fields=["balance"])
        return instance
