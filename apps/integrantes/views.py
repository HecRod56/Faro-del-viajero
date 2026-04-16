from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect
from .services import lista_integrantes

from apps.gestion_viajes.models import Viaje, Participante
from apps.autenticado.models import CustomUser
from apps.integrantes.services import lista_integrantes, viaje_data

# Create your views here.
def integrantes_viaje(request, id_viaje, id_usuario=1):
    viaje = get_object_or_404(Viaje, id=id_viaje)

    integrantes = lista_integrantes.lista_integrantes_viaje(
        viaje=viaje,
        usuario_id=id_usuario
    )

    es_organizador_actual = lista_integrantes.usuario_es_organizador(
        viaje=viaje,
        id_usuario=id_usuario
    )

    viaje_info = viaje_data.datos_viaje(viaje)

    return render(request, "integrantes/revisar_lista.html", {
        "viaje": viaje_info,
        "integrantes": integrantes,
        "usuario_actual_id": id_usuario,
        "es_organizador_actual": es_organizador_actual,
    })

def informacion_integrante(request, id_viaje, id_usuario):
    # 🔹 obtener viaje
    viaje = get_object_or_404(Viaje, id=id_viaje)

    # 🔹 obtener usuario
    usuario = get_object_or_404(CustomUser, id=id_usuario)

    # 🔹 obtener relación participante (usuario dentro del viaje)
    participante = get_object_or_404(
        Participante,
        viaje=viaje,
        usuario=usuario
    )

    # 🔹 verificar si es organizador en este viaje
    es_organizador = participante.rol == "organizador"

    # 🔹 viajes del usuario (para la sección "viajes compartidos")
    viajes_usuario = (
        Participante.objects
        .filter(usuario=usuario)
        .select_related("viaje")
    )

    return render(request, "integrantes/visualizar_perfil.html", {
        "usuario": usuario,
        "viaje_actual": viaje,
        "participante": participante,
        "es_organizador": es_organizador,
        "viajes": viajes_usuario,
    })

def integrantes_viaje_mock(request, id_viaje, usuario_id=1):
    """
    Para probar como organizador: /mock/viaje/1/integrantes/como/1/
    Para probar como integrante:  /mock/viaje/1/integrantes/como/2/
    """

    todos_los_integrantes = [
        {"id": 1, "nombre": "Juan Pérez",   "rol": "Organizador", "es_organizador": True,  "telefono": "+52 55 1234 5678"},
        {"id": 2, "nombre": "Ana García",   "rol": "Integrante",  "es_organizador": False, "telefono": "+52 55 2345 6789"},
        {"id": 3, "nombre": "Carlos Lopez", "rol": "Integrante",  "es_organizador": False, "telefono": "+52 55 3456 7890"},
        {"id": 4, "nombre": "María Torres", "rol": "Integrante",  "es_organizador": False, "telefono": "+52 55 4567 8901"},
        {"id": 5, "nombre": "Pedro Ruiz",   "rol": "Integrante",  "es_organizador": False, "telefono": "+52 55 5678 9012"},
        {"id": 6, "nombre": "Sofía Mendez", "rol": "Integrante",  "es_organizador": False, "telefono": "+52 55 6789 0123"},
    ]

    # Marcamos quién es el usuario actual según el parámetro de la URL
    for integrante in todos_los_integrantes:
        integrante["es_actual"] = (integrante["id"] == usuario_id)

    es_organizador_actual = (usuario_id == 1)

    viaje = {
    "id": id_viaje,
    "nombre": "Viaje a Cancún",
    "estado": "Planeado",
    "cupos_ocupados": 6,
    "cupos_totales": 10,
    "cupos_disponibles": 10 - 6, 
    "imagen": "https://images.unsplash.com/photo-1582719508461-905c673771fd"
}

    return render(request, "integrantes/revisar_lista.html", {
        "viaje": viaje,
        "integrantes": todos_los_integrantes,
        "usuario_actual_id": usuario_id,
        "es_organizador_actual": es_organizador_actual,
    })


def eliminar_integrante_mock(request, id_integrante):
    if request.method != "POST":
        return redirect("integrantes:mock_integrantes", id_viaje=1)

    id_viaje       = request.POST.get("id_viaje", 1)
    usuario_actual_id = int(request.POST.get("usuario_actual_id", 1))
    organizador_id = 1

    print(f"[MOCK] Integrante {id_integrante} eliminado del viaje {id_viaje}")
    return redirect("integrantes:mock_integrantes_como", id_viaje=id_viaje, usuario_id=usuario_actual_id)

def anadir_integrante_mock(request, id_viaje):
    if request.method != "POST":
        return redirect("integrantes:mock_integrantes", id_viaje=id_viaje)

    correo = request.POST.get("correo", "").strip()
    usuario_actual_id = int(request.POST.get("usuario_actual_id", 1))

    # Mock de usuarios registrados en la plataforma
    usuarios_registrados = [
        {"id": 7, "correo": "lucia@correo.com",   "nombre": "Lucía Ramos"},
        {"id": 8, "correo": "marcos@correo.com",  "nombre": "Marcos Díaz"},
        {"id": 9, "correo": "elena@correo.com",   "nombre": "Elena Vega"},
    ]

    # Mock de cupos
    cupos_ocupados = 6
    cupos_totales  = 10


    # RF-18: verificar capacidad
    if cupos_ocupados >= cupos_totales:
        print("[MOCK] No hay cupos disponibles")
        return redirect("integrantes:mock_integrantes_como", id_viaje=id_viaje, usuario_id=usuario_actual_id)

    # Verificar que el correo existe en la plataforma
    usuario_nuevo = next((u for u in usuarios_registrados if u["correo"] == correo), None)
    if not usuario_nuevo:
        print(f"[MOCK] Correo {correo} no encontrado en la plataforma")
        return redirect("integrantes:mock_integrantes_como", id_viaje=id_viaje, usuario_id=usuario_actual_id)

    print(f"[MOCK] {usuario_nuevo['nombre']} añadido al viaje {id_viaje}")
    return redirect("integrantes:mock_integrantes_como", id_viaje=id_viaje, usuario_id=usuario_actual_id)

# RF-24: Abandonar viaje
def abandonar_viaje_mock(request, id_viaje):
    if request.method != "POST":
        return redirect("integrantes:mock_integrantes", id_viaje=id_viaje)
    usuario_actual_id = int(request.POST.get("usuario_actual_id", 1))
    print(f"[MOCK] Usuario {usuario_actual_id} abandonó el viaje {id_viaje}")
    return redirect("integrantes:mock_integrantes", id_viaje=id_viaje)

# RF-23: Asignar organizador
def asignar_organizador_mock(request, id_integrante):
    if request.method != "POST":
        return redirect("integrantes:mock_integrantes", id_viaje=1)
    id_viaje = request.POST.get("id_viaje", 1)
    usuario_actual_id = int(request.POST.get("usuario_actual_id", 1))
    print(f"[MOCK] Integrante {id_integrante} es ahora organizador del viaje {id_viaje}")
    return redirect("integrantes:mock_integrantes_como", id_viaje=id_viaje, usuario_id=usuario_actual_id)