from django.urls import path
from .views import (
    CustomTokenObtainPairView,
    UsersView,
    UserMeView,
    SingleUserView
)

urlpatterns = [
    # Authentification JWT
    path('auth/', CustomTokenObtainPairView.as_view(), name='token-obtain'),

    # Utilisateurs
    path('users/', UsersView.as_view(), name='user-list-create'),
    path('users/me/', UserMeView.as_view(), name='user-me'),
    path('users/<int:user_id>/', SingleUserView.as_view(), name='user-detail'),
]
