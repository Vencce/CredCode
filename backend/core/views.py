from django.shortcuts import render
from .models import Item

def listar_itens(request):
    itens = Item.objects.all()
    return render(request, 'itens.html', {'itens': itens})