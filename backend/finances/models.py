from django.db import models
from django.db.models import Sum
from decimal import Decimal
from django.contrib.auth.models import User

class Wallet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wallets')
    monthly_income = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def current_balance(self):
        result = self.expenses.aggregate(total=Sum('amount'))
        expenses_sum = result['total'] or Decimal('0.00')
        return self.monthly_income - expenses_sum

class Expense(models.Model):
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='expenses')
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(auto_now_add=True)
    category = models.CharField(max_length=100, blank=True, null=True)