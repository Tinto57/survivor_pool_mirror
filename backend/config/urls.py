"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from accounts.views import *
from wallet.views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth', account_get_token, name="get-token-user"),
    path('api/v1/users', UsersView.as_view(), name="users-collection"),
    path('api/v1/user/me', account_get_self, name="get-self-account"),
    path('api/v1/user/<int:user_id>', SingleUserView.as_view(), name="user-collection"),
    path('api/v1/employees', EmployeesView.as_view(), name="transactions-collection"),
]
