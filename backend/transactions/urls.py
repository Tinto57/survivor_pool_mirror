from django.urls import path
from .views import (
    PaymentIntentCreateView,
    PaymentIntentDetailView,
    TransactionsView,
    SingleTransactionView,
    AbondmentCreateView,
    CounterEntryCreateView,
    AdminTransactionsCsvExportView
)

urlpatterns = [

    path('payments/', PaymentIntentCreateView.as_view(), name='payment-intent-create'),
    path('payments/<str:token>/', PaymentIntentDetailView.as_view(), name='payment-intent-get'),
    path('transactions/', TransactionsView.as_view(), name="transaction-list"),
    path('transactions/abondments/', AbondmentCreateView.as_view(), name="abondment-create"),
    path('admin/transactions.csv/', AdminTransactionsCsvExportView.as_view(), name="get-all-transactions"),
    path('transactions/<int:transaction_id>/', SingleTransactionView.as_view(), name="transaction-detail"),
    path('transactions/<int:transaction_id>/counter-entry/', CounterEntryCreateView.as_view(), name="transaction-counter-entry"),
]
