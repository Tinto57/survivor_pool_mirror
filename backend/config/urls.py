from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from accounts.permissions import IsAdminRole

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("accounts.urls")),
    path("api/v1/", include("wallet.urls")),
    path("api/v1/", include("transactions.urls")),
    path(
        "api/schema/",
        SpectacularAPIView.as_view(permission_classes=[IsAdminRole]),
        name="schema",
    ),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(
            url_name="schema",
            permission_classes=[IsAdminRole],
        ),
        name="swagger-ui",
    ),
]
