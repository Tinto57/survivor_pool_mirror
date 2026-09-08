from django.urls import path
from .views import (
    CategoriesView,
    MinisterSpotlightClickView,
    MinisterSpotlightListCreateView,
    MinisterSpotlightPublicListView,
    MinisterSpotlightPublicView,
    MinisterSpotlightRepublishView,
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
    path('ministre/coup-de-coeur/', MinisterSpotlightPublicView.as_view(), name='minister-spotlight-public'),
    path('ministre/coup-de-coeur/toutes/', MinisterSpotlightPublicListView.as_view(), name='minister-spotlight-public-list'),
    path('ministre/coup-de-coeur/click/', MinisterSpotlightClickView.as_view(), name='minister-spotlight-click'),
    path('ministre/coup-de-coeur/historique/', MinisterSpotlightListCreateView.as_view(), name='minister-spotlight-history'),
    path('ministre/coup-de-coeur/<int:spotlight_id>/republier/', MinisterSpotlightRepublishView.as_view(), name='minister-spotlight-republish'),
]
