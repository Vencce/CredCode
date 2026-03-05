from django.contrib import admin
from .models import Profile, Wallet, Expense

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'monthly_income', 'account_balance')
    search_fields = ('full_name', 'user__username')

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'balance')
    search_fields = ('name', 'user__username')

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('description', 'amount', 'date', 'wallet')
    search_fields = ('description',)
    list_filter = ('date',)