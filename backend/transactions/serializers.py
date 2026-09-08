from decimal import Decimal
from rest_framework import serializers
from .models import Transaction
from wallet.models import Employee

class PaymentIntentResponseSerializer(serializers.Serializer):
    """Intention de paiement : token à encoder en QR code et durée de validité. Le montant n'est pas encore fixé."""
    token = serializers.CharField(help_text="Token opaque à encoder en QR code et transmettre au partenaire.")
    expires_in = serializers.IntegerField(help_text="Durée de validité restante du token, en secondes.")


class PaymentConfirmSerializer(serializers.Serializer):
    """Ce que le partenaire envoie pour fixer le montant et valider le paiement."""
    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.01"),
        help_text="Montant du paiement, choisi par le partenaire."
    )

class TransactionSerializer(serializers.ModelSerializer):
    """Écriture comptable, immuable une fois créée."""

    balance_after = serializers.SerializerMethodField(
        help_text="Solde du salarié juste après cette écriture. Fourni uniquement quand le "
        "salarié consulte ses propres transactions, `null` sinon (partenaire, admin)."
    )

    class Meta:
        model = Transaction
        fields = ["id", "token", "transaction_type", "employee", "partner", "amount", "validated_at", "counter_entry_of", "balance_after"]
        read_only_fields = ["id", "token", "transaction_type", "employee", "partner", "amount", "validated_at", "counter_entry_of"]
        extra_kwargs = {
            "transaction_type": {"help_text": "`PAYMENT` (débit salarié → partenaire) ou `ABONDMENT` (crédit du solde salarié)."},
            "employee": {"help_text": "Identifiant du salarié concerné par l'écriture."},
            "partner": {"help_text": "Identifiant du partenaire bénéficiaire. Absent pour un abondement."},
            "amount": {"help_text": "Montant de l'écriture, toujours positif."},
            "validated_at": {"help_text": "Date et heure de validation de l'écriture (immuable)."},
            "counter_entry_of": {"help_text": "Identifiant de la transaction d'origine si cette écriture est une contre-écriture."},
        }

    def get_balance_after(self, obj: Transaction):
        return self.context.get("balance_after_map", {}).get(obj.id)


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
