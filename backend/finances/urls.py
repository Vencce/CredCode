from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WalletViewSet, ExpenseViewSet, ProfileView, BudgetViewSet, CategoryViewSet, GoalViewSet, InvestmentViewSet, LoanViewSet, ProfileView, CashFlowView, SuggestCategoryView, CreditCardViewSet, CardExpenseViewSet, RegisterView

router = DefaultRouter()
router.register(r'wallets', WalletViewSet, basename='wallet')
router.register(r'expenses', ExpenseViewSet, basename='expense')
router.register(r'budgets', BudgetViewSet, basename='budget')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'goals', GoalViewSet, basename='goal')
router.register(r'investments', InvestmentViewSet, basename='investment')
router.register(r'loans', LoanViewSet, basename='loan')
router.register(r'cards', CreditCardViewSet, basename='cards')
router.register(r'card-expenses', CardExpenseViewSet, basename='card-expenses')

urlpatterns = [
    path('', include(router.urls)),
    path('profile/', ProfileView.as_view(), name='profile_update'),
    path('cash-flow/', CashFlowView.as_view(), name='cash_flow'),
    path('suggest-category/', SuggestCategoryView.as_view(), name='suggest_category'),
]