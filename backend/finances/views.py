from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, viewsets, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count
from .serializers import (
    RegisterSerializer, WalletSerializer, ExpenseSerializer, 
    ProfileSerializer, BudgetSerializer, CategorySerializer, 
    GoalSerializer, InvestmentSerializer, LoanSerializer
)
from .models import Wallet, Expense, Profile, Budget, Category, Goal, Investment, Loan

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

class WalletViewSet(viewsets.ModelViewSet):
    serializer_class = WalletSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Wallet.objects.filter(user=self.request.user)
        
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)
        
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ExpenseViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Expense.objects.filter(wallet__user=self.request.user)

class BudgetViewSet(viewsets.ModelViewSet):
    serializer_class = BudgetSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Budget.objects.filter(wallet__user=self.request.user)

class GoalViewSet(viewsets.ModelViewSet):
    serializer_class = GoalSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Goal.objects.filter(user=self.request.user)
        
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class InvestmentViewSet(viewsets.ModelViewSet):
    serializer_class = InvestmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Investment.objects.filter(user=self.request.user)
        
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class LoanViewSet(viewsets.ModelViewSet):
    serializer_class = LoanSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Loan.objects.filter(user=self.request.user)
        
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile_exists = Profile.objects.filter(user=request.user).exists()
        if profile_exists:
            profile = Profile.objects.get(user=request.user)
            return Response({
                "full_name": profile.full_name,
                "account_balance": getattr(profile, 'account_balance', 0),
                "monthly_income": getattr(profile, 'monthly_income', 0),
                "has_profile": True
            }, status=status.HTTP_200_OK)
        return Response({"has_profile": False}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request):
        serializer = ProfileSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Perfil atualizado com sucesso!", "has_profile": True}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CashFlowView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        today = timezone.now().date()
        end_date = today + timedelta(days=30)
        
        profile = Profile.objects.get(user=user)
        base_balance = float(profile.account_balance)
        
        expenses_past = Expense.objects.filter(wallet__user=user, date__lte=today)
        current_balance = base_balance + sum(float(e.amount) for e in expenses_past)

        future_expenses = Expense.objects.filter(
            wallet__user=user, 
            date__gt=today, 
            date__lte=end_date
        )

        future_loans = Loan.objects.filter(
            user=user, 
            is_paid=False, 
            due_date__gt=today, 
            due_date__lte=end_date
        )

        timeline = []
        running_balance = current_balance
        
        for i in range(31):
            day = today + timedelta(days=i)
            day_expenses = sum(float(e.amount) for e in future_expenses if e.date == day)
            day_loans = sum(float(l.amount) for l in future_loans if l.due_date == day)
            
            running_balance += (day_expenses + day_loans)
            
            timeline.append({
                "date": day.strftime("%d/%m"),
                "balance": round(running_balance, 2)
            })

        return Response({
            "current_balance": round(current_balance, 2),
            "projected_balance_30d": round(running_balance, 2),
            "timeline": timeline
        })

class SuggestCategoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        description = request.query_params.get('description', '').strip().lower()
        if not description or len(description) < 3:
            return Response({"category": None})

        smart_keywords = {
            'mercado': 'Alimentação',
            'supermercado': 'Alimentação',
            'ifood': 'Alimentação',
            'padaria': 'Alimentação',
            'restaurante': 'Alimentação',
            'luz': 'Moradia',
            'energia': 'Moradia',
            'água': 'Moradia',
            'agua': 'Moradia',
            'aluguel': 'Moradia',
            'internet': 'Despesas Fixas',
            'telefone': 'Despesas Fixas',
            'celular': 'Despesas Fixas',
            'netflix': 'Lazer',
            'spotify': 'Lazer',
            'cinema': 'Lazer',
            'uber': 'Transporte',
            '99': 'Transporte',
            'gasolina': 'Transporte',
            'posto': 'Transporte',
            'farmácia': 'Saúde',
            'farmacia': 'Saúde',
            'médico': 'Saúde',
            'medico': 'Saúde',
            'salário': 'Salário',
            'salario': 'Salário',
            'pix': 'Transferência'
        }

        for keyword, category in smart_keywords.items():
            if keyword in description:
                return Response({"category": category})
        
        suggestion = Expense.objects.filter(
            wallet__user=request.user,
            description__icontains=description
        ).values('category').annotate(count=Count('category')).order_by('-count').first()

        if suggestion and suggestion['category']:
            return Response({"category": suggestion['category']})
            
        return Response({"category": None})

class CustomTokenSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data['has_profile'] = Profile.objects.filter(user=self.user).exists()
        return data

class CustomLoginView(TokenObtainPairView):
    serializer_class = CustomTokenSerializer