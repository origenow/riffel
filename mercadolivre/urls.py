from django.urls import path

from .views import (
    MeView, TokenStatusView, RefreshTokenView,
    MyProductsView, SyncProductsView,
    MyOrdersView, SyncOrdersView,
    ProductAdsView, DebugEnvView, CampaignAdsView,
)
from .auth_views import AuthLoginView, AuthCallbackView
from .user_views import UsersListView, UserDetailView, UserDeleteView
from .docs_view import docs_view

urlpatterns = [
    # Documentação
    path('docs', docs_view, name='docs'),
    
    # Autenticação OAuth2
    path('auth/login', AuthLoginView.as_view(), name='auth-login'),
    path('auth/callback', AuthCallbackView.as_view(), name='auth-callback'),
    
    # Gerenciamento de usuários
    path('users', UsersListView.as_view(), name='users-list'),
    path('users/<int:user_id>', UserDetailView.as_view(), name='user-detail'),
    path('users/<int:user_id>/delete', UserDeleteView.as_view(), name='user-delete'),
    
    # Endpoints por usuário
    path('users/<int:user_id>/me', MeView.as_view(), name='user-me'),
    path('users/<int:user_id>/myproducts', MyProductsView.as_view(), name='user-myproducts'),
    path('users/<int:user_id>/myproducts/sync', SyncProductsView.as_view(), name='user-myproducts-sync'),
    path('users/<int:user_id>/myorders', MyOrdersView.as_view(), name='user-myorders'),
    path('users/<int:user_id>/myorders/sync', SyncOrdersView.as_view(), name='user-myorders-sync'),
    path('users/<int:user_id>/productads', ProductAdsView.as_view(), name='user-productads'),
    path('users/<int:user_id>/productads/campaigns/<str:campaign_identifier>/ads', CampaignAdsView.as_view(), name='user-campaign-ads'),
    path('users/<int:user_id>/token/status', TokenStatusView.as_view(), name='user-token-status'),
    path('users/<int:user_id>/token/refresh', RefreshTokenView.as_view(), name='user-token-refresh'),
    
    # Utilitários
    path('debug/env', DebugEnvView.as_view(), name='debug-env'),
]
