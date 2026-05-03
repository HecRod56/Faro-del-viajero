#view.py busqueda
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from apps.gestion_viajes.models import Viaje
from apps.core.services.destinos_service import buscar_lugares, obtener_foto_destino, obtener_coordenadas, obtener_detalle_lugar
from django.contrib import messages


@login_required
def agregar_actividad(request, viaje_id):
    if request.method == "POST":
        from datetime import date, time
        viaje     = get_object_or_404(Viaje, id=viaje_id)
        nombre    = request.POST.get("nombre", "")
        direccion = request.POST.get("direccion", "")
        precio    = request.POST.get("precio", "")
        website   = request.POST.get("website", "")

        try:
            from apps.actividades.models import Actividad
            Actividad.objects.create(
                viaje=viaje,
                creador=request.user,
                titulo=nombre,
                descripcion=f"Dirección: {direccion}\nSitio web: {website}\nPrecio estimado: {precio}",
                ubicacion=direccion,
                fecha=date.today(),
                hora=time(12, 0),
                estado="VOTACION",
            )
            messages.success(request, f'"{nombre}" agregado a tus actividades ✅')
        except Exception as e:
            messages.error(request, f"No se pudo agregar: {e}")

        return redirect(request.META.get("HTTP_REFERER", f"/busqueda/viaje/{viaje_id}/destinos/"))

    return redirect(f"/busqueda/viaje/{viaje_id}/destinos/")

@login_required
def p_destinos(request, viaje_id):
    viaje = get_object_or_404(Viaje, id=viaje_id)

    categoria  = request.GET.get("categoria", "atracciones")
    busqueda   = request.GET.get("q", "")
    precio_min = request.GET.get("precio_min", 0)
    precio_max = request.GET.get("precio_max", 10000)

    # Término de búsqueda: lo que escribió el usuario o el destino del viaje
    termino = busqueda if busqueda else viaje.destino

    lugares   = buscar_lugares(termino, categoria=categoria, limite=12)
    foto_hero = obtener_foto_destino(viaje.destino)
    coords    = obtener_coordenadas(viaje.destino)

    context = {
        "viaje":      viaje,
        "viaje_actual": viaje,  # ←     NUEVA  LINEA
        "lugares":    lugares,
        "categoria":  categoria,
        "busqueda":   busqueda,
        "foto_hero":  foto_hero,
        "coords":     coords,
        "precio_min": precio_min,
        "precio_max": precio_max,
    }
    return render(request, "busqueda/destinos.html", context)

def detalle_lugar_view(request, viaje_id):
    nombre    = request.GET.get('nombre', '')
    ciudad    = request.GET.get('ciudad', '')
    categoria = request.GET.get('categoria', 'atracciones')

    viaje = get_object_or_404(Viaje, id=viaje_id)
    lugar = obtener_detalle_lugar(nombre, ciudad, categoria)
    return render(request, 'busqueda/detalle_lugar.html', {
        'viaje': viaje,
        'lugar': lugar,
    })
