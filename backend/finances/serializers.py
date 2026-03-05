from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Wallet, Expense, Profile

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = ('username', 'email', 'password')
    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = ['id', 'wallet', 'description', 'amount', 'date', 'category']

class WalletSerializer(serializers.ModelSerializer):
    expenses = ExpenseSerializer(many=True, read_only=True)
    current_balance = serializers.ReadOnlyField()
    class Meta:
        model = Wallet
        fields = ['id', 'user', 'monthly_income', 'current_balance', 'expenses']

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['full_name', 'monthly_income', 'account_balance']

    def create(self, validated_data):
        user = self.context['request'].user
        profile, created = Profile.objects.update_or_create(
            user=user,
            defaults=validated_data
        )
        return profile