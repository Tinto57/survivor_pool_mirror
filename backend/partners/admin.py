from django.contrib import admin
from .models import Category, Partner, PartnerDecision

admin.site.register(Category)
admin.site.register(Partner)
admin.site.register(PartnerDecision)
