from decimal import Decimal
from rest_framework import serializers
from .models import Transaction

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
        fields = ["id", "employee", "partner", "amount", "validated_at", "is_cancelled"]
        read_only_fields = list(fields)

class TransactionCancellationSerializer(serializers.ModelSerializer):
    """ Serializer when cancelling a token """
    class Meta:
        model = Transaction
        fields = ["id", "is_cancelled", "cancelled_by", "cancellation_reaseon"]
        read_only_fields = ["id"]
