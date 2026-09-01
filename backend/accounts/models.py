from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib import admin

# Create your models here.
class User(AbstractUser):
    ROLE_CHOICES = [
        ('salarie', 'Salarié'),
        ('partenaire', 'Partenaire'),
        ('admin', 'Admin')
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

admin.site.register(User)
