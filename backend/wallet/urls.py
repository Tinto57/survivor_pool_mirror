from django.urls import path
from .views import (
    EmployeesView,
    EmployeeMe,
    EmployeesOverdraftTotalView,
    SingleEmployeeView,
    SingleEmployeeBalanceView,
)

urlpatterns = [

    path('employees/', EmployeesView.as_view(), name='employee-list-create'),
    path('employees/me/', EmployeeMe.as_view(), name='employee-me'),
    path('employees/decouvert-total/', EmployeesOverdraftTotalView.as_view(), name='employee-overdraft-total'),
    path('employees/<int:employee_id>/', SingleEmployeeView.as_view(), name='employee-detail'),
    path('employees/<int:employee_id>/balance/', SingleEmployeeBalanceView.as_view(), name='employee-balance-detail')
]
