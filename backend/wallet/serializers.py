import re
from rest_framework import serializers
from django.contrib.auth import get_user_model
from wallet.models import Employee
from accounts.models import User

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ["id", "user", "balance", "employer"]
        read_only_fields = ["id", "balance"]
