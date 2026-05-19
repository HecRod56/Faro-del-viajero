from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from apps.gestion_viajes.models import Viaje
from apps.core.services.destinos_service import buscar_lugares, obtener_foto_destino, obtener_coordenadas
from .models import DestinoCache


@login_required
def p_destinos(request, viaje_id):
    viaje     = get_object_or_404(Viaje, id=viaje_id)
    categoria = request.GET.get("categoria", "atracciones")
    busqueda  = request.GET.get("q", "")
    termino   = busqueda if busqueda else viaje.destino

    # ── Leer filtros del GET ───────────────────────────────────────────────────
    subcategorias = request.GET.getlist("subcategoria")   # lista de strings
    popularidades = request.GET.getlist("popularidad")    # lista de strings
    precio_min    = int(request.GET.get("precio_min", 0) or 0)
    precio_max    = int(request.GET.get("precio_max", 10000) or 10000)
    estrellas_raw = request.GET.getlist("estrellas")
    estrellas     = [int(e) for e in estrellas_raw if e.isdigit()]
    servicios     = request.GET.getlist("servicios")

    # Número de integrantes del viaje (para información de contexto, sin cupos)
    num_integrantes = viaje.participantes.count() or 1

    # Hay filtros activos si algo difiere del estado "vacío / por defecto"
    hay_filtros = bool(
        subcategorias or popularidades or estrellas or servicios
        or precio_min > 0 or precio_max < 10000
    )

    desde_cache = False
    lugares     = None

    # Usar caché solo cuando NO hay filtros activos
    if not hay_filtros:
        try:
            cache_obj   = DestinoCache.objects.get(destino__iexact=termino, categoria=categoria)
            lugares     = cache_obj.datos
            desde_cache = True
        except DestinoCache.DoesNotExist:
            pass

    if lugares is None:
        lugares = buscar_lugares(
            termino,
            categoria=categoria,
            limite=18,
            precio_min=precio_min,
            precio_max=precio_max,
            subcategorias=subcategorias or None,
            popularidades=popularidades or None,
            estrellas=estrellas or None,
            servicios=servicios or None,
        )
        # Guardar en caché solo cuando no hay filtros activos
        if not hay_filtros:
            DestinoCache.objects.update_or_create(
                destino=termino,
                categoria=categoria,
                defaults={"datos": lugares}
            )

    foto_hero = obtener_foto_destino(viaje.destino)
    coords    = obtener_coordenadas(viaje.destino)

    context = {
        "viaje":           viaje,
        "viaje_actual":    viaje,
        "lugares":         lugares,
        "categoria":       categoria,
        "busqueda":        busqueda,
        "foto_hero":       foto_hero,
        "coords":          coords,
        "desde_cache":     desde_cache,
        # Filtros: estado actual para que los parciales los muestren seleccionados
        "precio_min":      precio_min,
        "precio_max":      precio_max,
        "subcategorias":   subcategorias,
        "popularidades":   popularidades,
        "estrellas":       [str(e) for e in estrellas],   # strings para comparar con template
        "servicios":       servicios,
        "num_integrantes": num_integrantes,
    }
    return render(request, "busqueda/destinos.html", context)


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
def detalle_lugar_view(request, viaje_id):
    viaje     = get_object_or_404(Viaje, id=viaje_id)
    nombre    = request.GET.get("nombre", "")
    ciudad    = request.GET.get("ciudad", "")
    categoria = request.GET.get("categoria", "atracciones")

    # Buscar el lugar en el caché de BD
    lugar = None
    try:
        cache_obj = DestinoCache.objects.get(
            destino__iexact=ciudad,
            categoria=categoria
        )
        for l in cache_obj.datos:
            if l.get("nombre", "").lower() == nombre.lower():
                lugar = l
                break
    except DestinoCache.DoesNotExist:
        pass

    # Si no está en caché usar obtener_detalle_lugar
    if not lugar:
        from apps.core.services.destinos_service import obtener_detalle_lugar
        lugar = obtener_detalle_lugar(nombre, ciudad, categoria)

    # Si no tiene descripción buscar en Wikipedia
    if lugar and not lugar.get("descripcion"):
        try:
            import requests as req
            wiki_headers = {"User-Agent": "FaroDelViajero/1.0 (farodelviajero@gmail.com)"}
            # Intentar primero en español, luego en inglés
            for lang in ["es", "en"]:
                params = {
                    "action": "query",
                    "titles": nombre,
                    "prop": "extracts",
                    "exintro": True,
                    "explaintext": True,
                    "format": "json",
                    "redirects": 1,
                }
                r = req.get(f"https://{lang}.wikipedia.org/w/api.php",
                            headers=wiki_headers, params=params, timeout=5)
                pages = r.json().get("query", {}).get("pages", {})
                page  = list(pages.values())[0]
                extract = page.get("extract", "")
                if extract and len(extract) > 50:
                    lugar["descripcion"] = extract[:600]
                    break
        except Exception:
            pass

    # Agregar fotos del detalle si no las tiene
    if lugar and not lugar.get("fotos"):
        from apps.core.services.destinos_service import obtener_fotos_lugar
        lugar["fotos"] = obtener_fotos_lugar(nombre, ciudad, cantidad=5)

    context = {
        "viaje":        viaje,
        "viaje_actual": viaje,
        "lugar":        lugar,
        "categoria":    categoria,
    }
    return render(request, "busqueda/detalle_lugar.html", context)


@login_required
def lugares_json(request, viaje_id):
    viaje     = get_object_or_404(Viaje, id=viaje_id)
    categoria = request.GET.get("categoria", "atracciones")
    busqueda  = request.GET.get("q", "")
    termino   = busqueda if busqueda else viaje.destino

    # ── Leer filtros del GET ───────────────────────────────────────────────────
    subcategorias = request.GET.getlist("subcategoria")
    popularidades = request.GET.getlist("popularidad")
    precio_min    = int(request.GET.get("precio_min", 0) or 0)
    precio_max    = int(request.GET.get("precio_max", 10000) or 10000)
    estrellas_raw = request.GET.getlist("estrellas")
    estrellas     = [int(e) for e in estrellas_raw if e.isdigit()]
    servicios     = request.GET.getlist("servicios")

    # Hay filtros activos
    hay_filtros = bool(
        subcategorias or popularidades or estrellas or servicios
        or precio_min > 0 or precio_max < 10000
    )

    desde_cache = False
    lugares     = None

    # Usar caché solo cuando NO hay filtros activos
    if not hay_filtros:
        try:
            cache_obj   = DestinoCache.objects.get(destino__iexact=termino, categoria=categoria)
            lugares     = cache_obj.datos
            desde_cache = True
        except DestinoCache.DoesNotExist:
            pass

    if lugares is None:
        lugares = buscar_lugares(
            termino,
            categoria=categoria,
            limite=18,
            precio_min=precio_min,
            precio_max=precio_max,
            subcategorias=subcategorias or None,
            popularidades=popularidades or None,
            estrellas=estrellas or None,
            servicios=servicios or None,
        )
        # Guardar en caché solo cuando no hay filtros activos
        if not hay_filtros:
            DestinoCache.objects.update_or_create(
                destino=termino,
                categoria=categoria,
                defaults={"datos": lugares}
            )

    return JsonResponse({
        "lugares": lugares,
        "categoria": categoria,
        "desde_cache": desde_cache,
    })