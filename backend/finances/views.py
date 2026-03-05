from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, viewsets, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth.models import User
from .serializers import RegisterSerializer, WalletSerializer, ExpenseSerializer, ProfileSerializer
from .models import Wallet, Expense

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

class WalletViewSet(viewsets.ModelViewSet):
    serializer_class = WalletSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return Wallet.objects.filter(user=self.request.user)

class ExpenseViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return Expense.objects.filter(wallet__user=self.request.user)

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ProfileSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Perfil atualizado com sucesso!", "has_profile": True}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)