from django.db import models
from django.contrib import admin
from decimal import Decimal
from django.core.validators import MinValueValidator

class Employee(models.Model):
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE)
    employer = models.CharField(max_length=200)
    balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[
            MinValueValidator(
                Decimal('0.00'),
                message='Le solde ne peut pas être négatif.',
            )
        ],
    )

    # NOTE: Add a contraint to ensure that balance will be >= 0
    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(balance__gte=Decimal('0.00')),
                name='employee_balance_non_negative',
            )
        ]

    def __str__(self):
        return f'{self.user.username}: ({self.balance}€)'

# Unused ?
class TopUp(models.Model):
    user = models.OneToOneField(Employee, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"+{self.amount}€ for {self.employee.user.username}"
