from django.urls import path

from .views import (
    MeView, TokenStatusView, RefreshTokenView,
    MyProductsView, SyncProductsView, MyOrdersView,
    ProductAdsView, DebugEnvView,
)
from .docs_view import docs_view

urlpatterns = [
    path('docs', docs_view, name='docs'),
    path('me', MeView.as_view(), name='mercadolivre-me'),
    path('myproducts', MyProductsView.as_view(), name='myproducts'),
    path('myproducts/sync', SyncProductsView.as_view(), name='myproducts-sync'),
    path('myorders', MyOrdersView.as_view(), name='myorders'),
    path('productads', ProductAdsView.as_view(), name='productads'),
    path('token/status', TokenStatusView.as_view(), name='token-status'),
    path('token/refresh', RefreshTokenView.as_view(), name='token-refresh'),
    path('debug/env', DebugEnvView.as_view(), name='debug-env'),
]
