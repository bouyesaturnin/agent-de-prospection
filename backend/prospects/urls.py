from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CampaignViewSet,
    LeadViewSet,
    MessageViewSet,
    AgentLogViewSet,
    DiscoveredProspectViewSet,
    unsubscribe_view,
)
from .auth_views import login_view, logout_view, me_view

router = DefaultRouter()
router.register(r'campaigns', CampaignViewSet, basename='campaign')
router.register(r'leads', LeadViewSet, basename='lead')
router.register(r'messages', MessageViewSet, basename='message')
router.register(r'logs', AgentLogViewSet, basename='log')
router.register(r'discovered-prospects', DiscoveredProspectViewSet, basename='discovered-prospect')

urlpatterns = [
    path('unsubscribe/<uuid:lead_id>/', unsubscribe_view, name='unsubscribe'),
    path('auth/login/', login_view, name='auth-login'),
    path('auth/logout/', logout_view, name='auth-logout'),
    path('auth/me/', me_view, name='auth-me'),
    path('', include(router.urls)),
]