from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib import admin

# Create your models here.
class User(AbstractUser):
    ROLE_CHOICES = [
        ('employee', 'Salarié'),
        ('partner', 'Partenaire'),
        ('admin', 'Admin')
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    def __str__(self):
        return self.username

admin.site.register(User)
