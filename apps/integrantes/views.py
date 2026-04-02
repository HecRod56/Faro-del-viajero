from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseForbidden

# Create your views here.
def integrantes_viaje(request, id_viaje):

    return render(request, 'integrantes/revisar_lista.html')

def integrantes_viaje_mock(request, id_viaje):
    
    integrantes = [
        {"nombre": "Juan Pérez", "rol": "Organizador", "es_organizador": True, "es_actual": False},
        {"nombre": "Ana García", "rol": "Integrante", "es_organizador": False, "es_actual": True},
        {"nombre": "Carlos Lopez", "rol": "Integrante", "es_organizador": False, "es_actual": False},
        {"nombre": "María Torres", "rol": "Integrante", "es_organizador": False, "es_actual": False},
        {"nombre": "Pedro Ruiz", "rol": "Integrante", "es_organizador": False, "es_actual": False},
        {"nombre": "Sofía Mendez", "rol": "Integrante", "es_organizador": False, "es_actual": False},
    ]

    viaje = {
        "id": id_viaje,
        "nombre": "Viaje a Cancún",
        "estado": "Planeado",
        "cupos_ocupados": 6,
        "cupos_totales": 10,
        "imagen": "https://images.unsplash.com/photo-1582719508461-905c673771fd"
    }

    return render(request, "viajes/revisar_lista.html", {
        "viaje": viaje,
        "integrantes": integrantes
    })