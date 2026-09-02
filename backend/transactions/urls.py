from django.urls import path
from .views import PaymentIntentCreateView, PaymentIntentDetailView

urlpatterns = [

    path('payments/', PaymentIntentCreateView.as_view(), name='payment-intent-create'),
    path('payments/<str:token>/', PaymentIntentDetailView.as_view(), name='payment-intent-get'),
]
