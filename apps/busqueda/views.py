from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from apps.gestion_viajes.models import Viaje
from apps.core.services.destinos_service import buscar_lugares, obtener_foto_destino, obtener_coordenadas
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

    categoria      = request.GET.get('categoria', 'atracciones')
    busqueda       = request.GET.get('q', '')
    precio_max     = int(request.GET.get('precio_max', 10000))
    num_integrantes = viaje.participantes.count() or 1   # participantes reales del viaje
    cupos          = max(1, min(int(request.GET.get('cupos', num_integrantes)), num_integrantes))
    subcategorias  = request.GET.getlist('subcategoria')   # lista, ej: ['cultura', 'deportes']
    popularidades  = request.GET.getlist('popularidad')    # lista, ej: ['En Tendencia 🔥']

    termino = busqueda if busqueda else viaje.destino

    lugares = buscar_lugares(
        termino,
        categoria=categoria,
        limite=min(cupos * 2, 30),   # pedir el doble para compensar filtrados
        precio_max=precio_max,
        subcategorias=subcategorias if subcategorias else None,
        popularidades=popularidades if popularidades else None,
    )
    lugares = lugares[:cupos]        # recortar al número de cupos solicitado

    foto_hero = obtener_foto_destino(viaje.destino)
    coords    = obtener_coordenadas(viaje.destino)

    context = {
        'viaje':         viaje,
        'viaje_actual':  viaje,
        'lugares':       lugares,
        'categoria':     categoria,
        'busqueda':      busqueda,
        'foto_hero':     foto_hero,
        'coords':        coords,
        'precio_max':       precio_max,
        'cupos':            cupos,
        'num_integrantes':  num_integrantes,
        'subcategorias':    subcategorias,
        'popularidades':    popularidades,
    }
    return render(request, "busqueda/destinos.html", context)
