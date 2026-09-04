from decimal import Decimal
from rest_framework import serializers
from .models import Transaction
from wallet.models import Employee

class PaymentIntentCreateSerializer(serializers.Serializer):
    """Ce que le client envoie pour générer le paiement"""
    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.01"),
        help_text="Montant de la transaction"
    )

class PaymentIntentResponseSerializer(serializers.Serializer):
    """Ce que Swagger documente en sortie """
    token = serializers.CharField()
    amount = serializers.CharField()
    expires_in = serializers.IntegerField(help_text="Durée de validité en secondes")

class TransactionSerializer(serializers.ModelSerializer):
    """ Serialize une transaction """
    class Meta:
        model = Transaction
        fields = ["id", "token", "transaction_type", "employee", "partner", "amount", "validated_at", "counter_entry_of"]
        read_only_fields = list(fields)


class AbondmentCreateSerializer(serializers.Serializer):
    employee = serializers.PrimaryKeyRelatedField(queryset=Employee.objects.all())
    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.01"),
    )
