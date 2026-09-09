from django.urls import path

from .views import AdminAuditLogView

urlpatterns = [
    path("admin/audit/", AdminAuditLogView.as_view(), name="admin-audit-log"),
]
