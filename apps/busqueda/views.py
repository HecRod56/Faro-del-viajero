#view.py busqueda
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from apps.gestion_viajes.models import Viaje
from apps.core.services.destinos_service import buscar_lugares, obtener_foto_destino, obtener_coordenadas, obtener_detalle_lugar
from django.contrib import messages
import requests

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
    precio_min     = int(request.GET.get('precio_min', 0))
    precio_max     = int(request.GET.get('precio_max', 10000))
    num_integrantes = viaje.participantes.count() or 1   # participantes reales del viaje
    cupos          = max(1, min(int(request.GET.get('cupos', num_integrantes)), num_integrantes))
    subcategorias  = request.GET.getlist('subcategoria')   # lista, ej: ['cultura', 'deportes']
    popularidades  = request.GET.getlist('popularidad')    # lista, ej: ['En Tendencia 🔥']
    
    # Filtros para Hoteles
    estrellas_str  = request.GET.getlist('estrellas')
    estrellas      = [int(e) for e in estrellas_str if e.isdigit()]
    servicios      = request.GET.getlist('servicios')

    termino = busqueda if busqueda else viaje.destino

    LIMITE_DISPLAY = 12   # tarjetas a mostrar siempre

    lugares = buscar_lugares(
        termino,
        categoria=categoria,
        limite=LIMITE_DISPLAY * 3 if subcategorias else LIMITE_DISPLAY,
        precio_min=precio_min,
        precio_max=precio_max,
        subcategorias=subcategorias if subcategorias else None,
        popularidades=popularidades if popularidades else None,
        estrellas=estrellas if estrellas else None,
        servicios=servicios if servicios else None,
    )
    lugares = lugares[:LIMITE_DISPLAY]   # mostrar máximo 12 tarjetas

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
        'precio_min':       precio_min,
        'precio_max':       precio_max,
        'cupos':            cupos,
        'num_integrantes':  num_integrantes,
        'subcategorias':    subcategorias,
        'popularidades':    popularidades,
        'estrellas':        estrellas,
        'servicios':        servicios,
    }
    return render(request, "busqueda/destinos.html", context)

def obtener_descripcion_wikipedia(nombre_lugar, ciudad):
    try:
        # Buscamos en Wikipedia en español usando el nombre y la ciudad
        query = f"{nombre_lugar} {ciudad}"
        url = f"https://es.wikipedia.org/api/rest_v1/page/summary/{query.replace(' ', '_')}"
        
        # El User-Agent es buena práctica para APIs de Wikimedia
        headers = {"User-Agent": "FaroDelViajero/1.0 (farodelviajero@gmail.com)"}
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('extract', '')
        
        # Si no encuentra con ciudad, intentamos solo con el nombre
        url_solo_nombre = f"https://es.wikipedia.org/api/rest_v1/page/summary/{nombre_lugar.replace(' ', '_')}"
        response = requests.get(url_solo_nombre, headers=headers, timeout=5)
        if response.status_code == 200:
            return response.json().get('extract', '')

    except Exception as e:
        print(f"Error Wikipedia: {e}")
    
    return "No hay una descripción disponible para este lugar, ¡pero seguro te encantará visitarlo!"

@login_required
def detalle_lugar_view(request, viaje_id):
    nombre    = request.GET.get('nombre', '')
    ciudad    = request.GET.get('ciudad', '')
    categoria = request.GET.get('categoria', 'atracciones')

    viaje = get_object_or_404(Viaje, id=viaje_id)
    lugar = obtener_detalle_lugar(nombre, ciudad, categoria)
    
    # --- NUEVA LÓGICA ---
    if lugar:
        lugar['descripcion'] = obtener_descripcion_wikipedia(nombre, ciudad)
    # ---------------------

    return render(request, 'busqueda/detalle_lugar.html', {
        'viaje': viaje,
        'lugar': lugar,
    })
