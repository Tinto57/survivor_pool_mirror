from django.urls import path
from .views import (
    PaymentIntentCreateView,
    PaymentIntentDetailView,
    TransactionsView,
    SingleTransactionView
)

urlpatterns = [

    path('payments/', PaymentIntentCreateView.as_view(), name='payment-intent-create'),
    path('payments/<str:token>/', PaymentIntentDetailView.as_view(), name='payment-intent-get'),
    path('transactions/', TransactionsView.as_view(), name="transaction-list"),
    path('transactions/<int:transaction_id>/', SingleTransactionView.as_view(), name="transaction-delete-or-get")
]
