from django.db import models
from django.utils import timezone
from datetime import timedelta
import secrets
from django.contrib import admin

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
    qr_code = models.OneToOneField(QRCode, on_delete=models.PROTECT)
    employee = models.ForeignKey('wallet.Employee', on_delete=models.PROTECT)
    partner = models.ForeignKey('partners.Partner', on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    validated_at = models.DateTimeField(auto_now_add=True)
    is_cancelled = models.BooleanField(default=False)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='cancelled_transactions')
    cancellation_reason = models.TextField(blank=True)

    def __str__(self):
        return f"{self.amount}€ - {self.employee.user.username} → {self.partner.business_name}"

admin.site.register((Transaction, QRCode))
