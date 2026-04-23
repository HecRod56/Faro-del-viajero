from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from collections import defaultdict
 
from apps.gestion_viajes.models import Viaje, Participante
from apps.galeria.models import ImagenGaleria

def _get_participante_o_403(viaje, usuario):
    """
    Devuelve el Participante si el usuario pertenece al viaje.
    Lanza 403 si no es integrante (RNF-27).
    """
    try:
        return Participante.objects.get(viaje=viaje, usuario=usuario)
    except Participante.DoesNotExist:
        return None
 
 
# ── RF-66: Ver galería agrupada por fecha ───────────────────
@login_required
def ver_galeria(request, id_viaje):
    viaje = get_object_or_404(Viaje, id=id_viaje)
 
    # RNF-27: solo integrantes del viaje
    participante = _get_participante_o_403(viaje, request.user)
    if not participante:
        return HttpResponseForbidden("No eres integrante de este viaje.")
 
    # Traer todas las imágenes ordenadas
    imagenes = (
        ImagenGaleria.objects
        .filter(viaje=viaje)
        .select_related("subida_por__usuario")
        .order_by("-fecha_tomada", "-fecha_subida")
    )
 
    # Anotar puede_eliminar en cada imagen para usarlo en el template
    for img in imagenes:
        img.puede_eliminar = img.puede_eliminar(request.user)
 
    # Agrupar por fecha_tomada (si es None, usar la fecha_subida)
    grupos = defaultdict(list)
    for img in imagenes:
        clave = img.fecha_tomada or img.fecha_subida.date()
        grupos[clave].append(img)
 
    # Ordenar las claves de más reciente a más antigua
    grupos_por_fecha = dict(sorted(grupos.items(), reverse=True))
 
    return render(request, "galeria/galeria.html", {
        "viaje": viaje,
        "grupos_por_fecha": grupos_por_fecha,
        "es_organizador": participante.rol == "organizador",
    })
 
 
# ── RF-65: Subir imagen ─────────────────────────────────────
@login_required
def subir_imagen(request, id_viaje):
    viaje = get_object_or_404(Viaje, id=id_viaje)
 
    # RNF-27
    participante = _get_participante_o_403(viaje, request.user)
    if not participante:
        return HttpResponseForbidden("No eres integrante de este viaje.")
 
    if request.method != "POST":
        return redirect("galeria:ver_galeria", id_viaje=id_viaje)
 
    archivo     = request.FILES.get("imagen")
    fecha_tomada = request.POST.get("fecha_tomada") or None
    descripcion  = request.POST.get("descripcion", "").strip()
 
    if not archivo:
        # Podrías agregar un mensaje con django.contrib.messages aquí
        return redirect("galeria:ver_galeria", id_viaje=id_viaje)
 
    ImagenGaleria.objects.create(
        viaje=viaje,
        subida_por=participante,
        imagen=archivo,          # Cloudinary lo sube automáticamente
        fecha_tomada=fecha_tomada or None,
        descripcion=descripcion,
    )
 
    return redirect("galeria:ver_galeria", id_viaje=id_viaje)
 
 
# ── RF-68: Eliminar imagen ──────────────────────────────────
@login_required
def eliminar_imagen(request, id_imagen):
    imagen = get_object_or_404(
        ImagenGaleria.objects.select_related("viaje", "subida_por__usuario"),
        id=id_imagen,
    )
 
    # RF-68: solo el autor o el organizador pueden eliminar
    if not imagen.puede_eliminar(request.user):
        return HttpResponseForbidden("No tienes permiso para eliminar esta imagen.")
 
    if request.method != "POST":
        return redirect("galeria:ver_galeria", id_viaje=imagen.viaje.id)
 
    id_viaje = imagen.viaje.id
    imagen.delete()   # Cloudinary borra el archivo automáticamente con django-cloudinary-storage
 
    return redirect("galeria:ver_galeria", id_viaje=id_viaje)

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