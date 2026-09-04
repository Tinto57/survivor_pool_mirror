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
    """Intention de paiement : token à encoder en QR code, montant réservé et durée de validité."""
    token = serializers.CharField(help_text="Token opaque à encoder en QR code et transmettre au partenaire.")
    amount = serializers.CharField(help_text="Montant réservé sur le solde du salarié.")
    expires_in = serializers.IntegerField(help_text="Durée de validité restante du token, en secondes.")

class TransactionSerializer(serializers.ModelSerializer):
    """Écriture comptable, immuable une fois créée."""
    class Meta:
        model = Transaction
        fields = ["id", "token", "transaction_type", "employee", "partner", "amount", "validated_at", "counter_entry_of"]
        read_only_fields = list(fields)
        extra_kwargs = {
            "transaction_type": {"help_text": "`PAYMENT` (débit salarié → partenaire) ou `ABONDMENT` (crédit du solde salarié)."},
            "employee": {"help_text": "Identifiant du salarié concerné par l'écriture."},
            "partner": {"help_text": "Identifiant du partenaire bénéficiaire. Absent pour un abondement."},
            "amount": {"help_text": "Montant de l'écriture, toujours positif."},
            "validated_at": {"help_text": "Date et heure de validation de l'écriture (immuable)."},
            "counter_entry_of": {"help_text": "Identifiant de la transaction d'origine si cette écriture est une contre-écriture."},
        }


class AbondmentCreateSerializer(serializers.Serializer):
    """Payload de création d'un abondement (crédit administratif du solde d'un salarié)."""

    employee = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.all(),
        help_text="Identifiant du salarié à créditer.",
    )
    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.01"),
        help_text="Montant positif à créditer.",
    )
