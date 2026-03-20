from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, viewsets, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.models import User
from .serializers import RegisterSerializer, WalletSerializer, ExpenseSerializer, ProfileSerializer, BudgetSerializer, CategorySerializer, GoalSerializer, InvestmentSerializer
from .models import Wallet, Expense, Profile, Budget, Category, Goal, Investment

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

class CustomTokenSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data['has_profile'] = Profile.objects.filter(user=self.user).exists()
        return data

class CustomLoginView(TokenObtainPairView):
    serializer_class = CustomTokenSerializer