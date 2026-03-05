from django.db import models
from django.db.models import Sum
from decimal import Decimal
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255)
    monthly_income = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    account_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def __str__(self):
        return self.full_name

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