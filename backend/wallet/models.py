from django.db import models
from django.contrib import admin

class Employee(models.Model):
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE)
    employer = models.CharField(max_length=200)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.user.username}: ({self.balance}€)"

class TopUp(models.Model):
    user = models.OneToOneField(Employee, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"+{self.amount}€ for {self.employee.user.username}"

admin.site.register((Employee, TopUp))
