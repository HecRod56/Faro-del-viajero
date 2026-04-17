from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .models import FotoGaleria


def galeria_mock(request, id_viaje, usuario_id=1):
    """
    Pantalla 08-A: Vista principal de la galería del viaje.

    Args:
        request: Solicitud HTTP.
        id_viaje (int): ID del viaje.
        usuario_id (int): ID del usuario actual.

    Returns:
        HttpResponse: Renderiza la galería con sus fotos agrupadas por fecha.
    """
    fotos = [
        {"id": 1, "nombre_usuario": "Juan P.",   "archivo": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e", "fecha_subida": "15/03/2026", "usuario_id": 1},
        {"id": 2, "nombre_usuario": "Carlos L.", "archivo": "https://images.unsplash.com/photo-1414235077428-338989a2e8c0", "fecha_subida": "15/03/2026", "usuario_id": 2},
        {"id": 3, "nombre_usuario": "Carlos L.", "archivo": "https://images.unsplash.com/photo-1544551763-46a013bb70d5", "fecha_subida": "15/03/2026", "usuario_id": 2},
        {"id": 4, "nombre_usuario": "Maria T.",  "archivo": "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7", "fecha_subida": "15/03/2026", "usuario_id": 3},
    ]

    viaje = {
        "id": id_viaje,
        "nombre": "Viaje a Cancún",
        "estado": "Planeado",
        "imagen": "https://images.unsplash.com/photo-1582719508461-905c673771fd"
    }

    return render(request, "galeria/galeria.html", {
        "viaje": viaje,
        "fotos": fotos,
        "usuario_actual_id": usuario_id,
        "es_organizador": usuario_id == 1,
    })


def subir_foto_mock(request, id_viaje):
    """
    Pantalla 08-E/F: Recibe y procesa la subida de una imagen a la galería.

    Valida formato (JPG, PNG, WEBP) y tamaño máximo (5 MB).

    Args:
        request: Solicitud HTTP con el archivo en request.FILES.
        id_viaje (int): ID del viaje al que se sube la foto.

    Returns:
        HttpResponseRedirect: Redirige a la galería tras subir correctamente.
    """
    if request.method != "POST":
        return redirect("galeria:galeria_mock", id_viaje=id_viaje)

    archivo = request.FILES.get("archivo")
    usuario_id = int(request.POST.get("usuario_id", 1))
    nombre_usuario = request.POST.get("nombre_usuario", "Usuario")

    # Validar formato
    formatos_permitidos = ["image/jpeg", "image/png", "image/webp"]
    if archivo and archivo.content_type not in formatos_permitidos:
        print(f"[MOCK] Formato no válido: {archivo.content_type}")
        return redirect("galeria:galeria_mock", id_viaje=id_viaje)

    # Validar tamaño (5 MB)
    if archivo and archivo.size > 5 * 1024 * 1024:
        print(f"[MOCK] Archivo muy grande: {archivo.size} bytes")
        return redirect("galeria:galeria_mock", id_viaje=id_viaje)

    print(f"[MOCK] Foto '{archivo.name}' subida al viaje {id_viaje} por {nombre_usuario}")
    return redirect("galeria:galeria_mock", id_viaje=id_viaje)


def eliminar_foto_mock(request, id_foto):
    """
    Pantalla 08-C: Elimina una foto de la galería.

    Solo puede eliminar el dueño de la foto o el organizador del viaje.

    Args:
        request: Solicitud HTTP con id_viaje y usuario_id en POST.
        id_foto (int): ID de la foto a eliminar.

    Returns:
        HttpResponseRedirect: Redirige a la galería tras eliminar.
    """
    if request.method != "POST":
        return redirect("galeria:galeria_mock", id_viaje=1)

    id_viaje   = request.POST.get("id_viaje", 1)
    usuario_id = int(request.POST.get("usuario_id", 1))

    print(f"[MOCK] Foto {id_foto} eliminada del viaje {id_viaje} por usuario {usuario_id}")
    return redirect("galeria:galeria_mock", id_viaje=id_viaje)