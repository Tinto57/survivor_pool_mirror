from django.db import models
from decimal import Decimal
from django.core.validators import MinValueValidator

OVERDRAFT_LIMIT = Decimal('-150.00')

class Employee(models.Model):
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE)
    employer = models.CharField(max_length=200)
    balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[
            MinValueValidator(
                OVERDRAFT_LIMIT,
                message='Le solde ne peut pas descendre sous le découvert autorisé de 150€.',
            )
        ],
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(balance__gte=OVERDRAFT_LIMIT),
                name='employee_balance_overdraft_limit',
            )
        ]

    def __str__(self):
        return f'{self.user.username}: ({self.balance}€)'
