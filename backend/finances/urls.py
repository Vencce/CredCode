from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WalletViewSet, ExpenseViewSet

router = DefaultRouter()
router.register(r'wallets', WalletViewSet, basename='wallet')
router.register(r'expenses', ExpenseViewSet, basename='expense')

urlpatterns = [
    path('', include(router.urls)),
]