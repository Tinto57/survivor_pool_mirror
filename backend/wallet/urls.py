from django.urls import path
from .views import EmployeesView, EmployeeMe

urlpatterns = [

    path('employees/', EmployeesView.as_view(), name='employee-list-create'),
    path('employees/me/', EmployeeMe.as_view(), name='employee-me'),
    # path('employees/<int:user_id>/', SingleEmployeeView.as_view(), name='employee-detail'),
]
