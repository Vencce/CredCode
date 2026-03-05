from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from finances.views import RegisterView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Autenticação (Global)
    path('api/auth/register/', RegisterView.as_view(), name='auth_register'),
    path('api/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Endpoints dos Apps
    path('api/finances/', include('finances.urls')),
]