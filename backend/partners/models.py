from django.db import models
from django.core.validators import RegexValidator
from django.contrib import admin

# Create your models here.
class Partner(models.Model):
    STATUS_CHOICE = [
        ('pending', "En attente"),
        ('active', "Actif"),
        ('suspended', "Suspendu"),
        ('closed', 'Cloturé'),
    ]
    status = models.CharField(choices=STATUS_CHOICE, max_length=20)
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE)
    business_name = models.CharField(max_length=200)
    siren = models.CharField(max_length=9, validators=[RegexValidator(r'^\d{9}$', 'Le SIREN doit contenir exactement 9 chiffres.')])
    business_purpose = models.TextField()
    address = models.CharField(max_length=300)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_featured = models.BooleanField(default=False)
    registered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.business_name

class PartnerDecision(models.Model):
    DECISION_CHOICES = [
        ('accepted', 'Acceptée'),
        ('rejected', 'Refusée'),
    ]
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name='decisions')
    decision = models.CharField(max_length=20, choices=DECISION_CHOICES)
    reason = models.TextField(blank=True)
    agent = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.partner.business_name} - {self.decision} ({self.created_at:%d/%m/%Y})"

admin.site.register((Partner, PartnerDecision))
