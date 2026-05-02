from django.shortcuts import render

# Create your views here.


def transporte_principal(request):
    return render(request, 'transporte/transporte_principal.html')

def registrar_trayecto(request):
    return render(request, 'transporte/registrar_trayecto.html')

def buscar_ruta_interna(request):
    return render(request, 'transporte/buscar_ruta_interna.html')