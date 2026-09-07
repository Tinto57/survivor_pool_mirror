from django.db import models
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

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(balance__gte=Decimal('0.00')),
                name='employee_balance_non_negative',
            )
        ]

    def __str__(self):
        return f'{self.user.username}: ({self.balance}€)'
