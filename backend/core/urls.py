from django.urls import path
from .views import listar_itens

urlpatterns = [
    path('', listar_itens, name='listar_itens'),
]