from django.urls import path
from .views import (
    CategoriesView,
    PartnersView,
    PartnerMeView,
    SinglePartnerView,
    PartnerDecisionCreateView,
    PartnerDecisionsListView,
)

urlpatterns = [
    path('categories/', CategoriesView.as_view(), name='category-list-create'),
    path('partners/', PartnersView.as_view(), name='partner-list'),
    path('partners/me/', PartnerMeView.as_view(), name='partner-me'),
    path('partners/<int:partner_id>/', SinglePartnerView.as_view(), name='partner-detail'),
    path('partners/<int:partner_id>/decision/', PartnerDecisionCreateView.as_view(), name='partner-decision-create'),
    path('partners/<int:partner_id>/decisions/', PartnerDecisionsListView.as_view(), name='partner-decisions-list'),
]
