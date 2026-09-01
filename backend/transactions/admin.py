from django.contrib import admin
from .models import Transaction, QRCode

admin.site.register(Transaction)
admin.site.register(QRCode)