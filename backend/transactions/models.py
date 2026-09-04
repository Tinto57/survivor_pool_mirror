from django.db import models
from django.utils import timezone
from datetime import timedelta
import secrets
from django.core.exceptions import ValidationError
from django.db import models

def generate_transaction_token():
    return secrets.token_urlsafe(32)

class QRCode(models.Model):
    employee = models.ForeignKey('wallet.Employee', on_delete=models.CASCADE)
    token = models.CharField(max_length=100, unique=True, editable=False)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(editable=False)
    is_used = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_urlsafe(32)
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=30)
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"QR {self.token[:8]}... ({self.amount}€)"

class Transaction(models.Model):
    PAYMENT = 'PAYMENT'
    ABONDMENT = 'ABONDMENT'
    TYPE_CHOICES = [
        (PAYMENT, 'Payment'),
        (ABONDMENT, 'Abondment'),
    ]

    token    = models.CharField(max_length=100, default=generate_transaction_token, unique=True, editable=False)
    transaction_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=PAYMENT)
    employee = models.ForeignKey('wallet.Employee', on_delete=models.PROTECT)
    partner  = models.ForeignKey('partners.Partner', on_delete=models.PROTECT, null=True, blank=True)
    amount   = models.DecimalField(max_digits=10, decimal_places=2)
    validated_at = models.DateTimeField(auto_now_add=True)
    counter_entry_of = models.OneToOneField(
        'self',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='counter_entry',
    )

    def save(self, *args, **kwargs):
        if self.pk and not kwargs.get("force_insert", False):
            raise ValidationError("Une transaction comptable validée est strictement immuable.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Interdiction absolue de supprimer une écriture comptable.")

    def __str__(self):
        recipient = self.partner.business_name if self.partner else self.employee.employer
        return f"{self.amount}€ - {self.employee.user.username} → {recipient}"
