#destinos_service.py core
import requests
import unicodedata
from django.conf import settings

GEOAPIFY_BASE   = "https://api.geoapify.com/v1"
GEOAPIFY_PLACES = "https://api.geoapify.com/v2/places"
PEXELS_BASE     = "https://api.pexels.com/v1"
WIKIMEDIA_BASE = "https://commons.wikimedia.org/w/api.php"
WIKIMEDIA_HEADERS = {"User-Agent": "FaroDelViajero/1.0 (farodelviajero@gmail.com)"}

CATEGORY_MAP = {
    "atracciones": "tourism,entertainment,leisure",
    "gastronomia": "catering.restaurant,catering.cafe,catering.bar",
    "hoteles":     "accommodation",
}

SUBCATEGORY_MAP = {
    'cultura':       'tourism.museum,tourism.historic,tourism.monument,tourism.archaeological,tourism.castle,tourism.sights',
    'naturaleza':    'leisure.park,leisure.beach,leisure.nature_reserve,leisure.garden,leisure.picnic_site',
    'aventura':      'sport,leisure.sports_centre,leisure.stadium,leisure.fitness,leisure.golf_course,leisure.ski,leisure.water_park',
    'entretenimiento': 'entertainment.cinema,entertainment.theatre,entertainment.concert_hall,entertainment.music_venue,entertainment.nightclub,entertainment.casino',
}

# Mapa inverso para determinar la categoría de filtro de una categoría de Geoapify
CATEGORY_TO_FILTER = {
    'tourism.museum': 'cultura',
    'tourism.historic': 'cultura',
    'tourism.monument': 'cultura',
    'tourism.archaeological': 'cultura',
    'tourism.castle': 'cultura',
    'tourism.sights': 'cultura',
    'leisure.park': 'naturaleza',
    'leisure.beach': 'naturaleza',
    'leisure.nature_reserve': 'naturaleza',
    'leisure.garden': 'naturaleza',
    'leisure.picnic_site': 'naturaleza',
    'sport': 'aventura',
    'leisure.sports_centre': 'aventura',
    'leisure.stadium': 'aventura',
    'leisure.fitness': 'aventura',
    'leisure.golf_course': 'aventura',
    'leisure.ski': 'aventura',
    'leisure.water_park': 'aventura',
    'entertainment.cinema': 'entretenimiento',
    'entertainment.theatre': 'entretenimiento',
    'entertainment.concert_hall': 'entretenimiento',
    'entertainment.music_venue': 'entretenimiento',
    'entertainment.nightclub': 'entretenimiento',
    'entertainment.casino': 'entretenimiento',
}


def obtener_categoria_filtro(categorias_geoapify):
    """
    Determina la categoría de filtro (cultura, naturaleza, aventura, entretenimiento)
    basándose en las categorías de Geoapify.
    Usa coincidencia por prefijo para cubrir subcategorías anidadas como
    'tourism.sights.viewpoint', 'entertainment.culture', etc.
    """
    # Ordenar las claves de mayor a menor longitud para preferir el match más específico
    claves_ordenadas = sorted(CATEGORY_TO_FILTER.keys(), key=len, reverse=True)

    for cat in categorias_geoapify:
        # Coincidencia exacta primero
        if cat in CATEGORY_TO_FILTER:
            return CATEGORY_TO_FILTER[cat]
        # Coincidencia por prefijo: 'tourism.sights.viewpoint' empieza con 'tourism.sights'
        for clave in claves_ordenadas:
            if cat.startswith(clave):
                return CATEGORY_TO_FILTER[clave]

    # Fallback por categoría padre cuando Geoapify devuelve solo el nivel raíz
    PARENT_FALLBACK = {
        'tourism':       'cultura',
        'entertainment': 'entretenimiento',
        'leisure':       'naturaleza',
        'sport':         'aventura',
    }
    for cat in categorias_geoapify:
        raiz = cat.split('.')[0]
        if raiz in PARENT_FALLBACK:
            return PARENT_FALLBACK[raiz]

    return None


def normalizar(s):
    return unicodedata.normalize('NFD', s.lower()).encode('ascii', 'ignore').decode('utf-8')

def obtener_coordenadas(destino: str):
    params = {
        "text": f"{destino} Mexico",
        "apiKey": settings.GEOAPIFY_API_KEY,
        "limit": 1,
        "lang": "es",
    }
    try:
        resp = requests.get(f"{GEOAPIFY_BASE}/geocode/search", params=params, timeout=6)
        resp.raise_for_status()
        features = resp.json().get("features", [])
        if features:
            geo = features[0]["geometry"]["coordinates"]
            props = features[0]["properties"]
            return {"lat": geo[1], "lon": geo[0], "nombre": props.get("city", destino)}
    except Exception as e:
        print(f"Error Geoapify geocode: {e}")
    return {"lat": None, "lon": None, "nombre": destino}

def obtener_foto_lugar(nombre: str, ciudad: str, indice: int = 0):
    # Intentar con Wikimedia Commons primero
    queries = [nombre, f"{nombre} {ciudad}", f"{ciudad} Mexico"]
    for query in queries:
        params = {
            "action": "query",
            "generator": "search",
            "gsrsearch": query,
            "gsrnamespace": 6,
            "gsrlimit": 10,
            "prop": "imageinfo",
            "iiprop": "url|size|mime",
            "iiurlwidth": 800,
            "format": "json",
        }
        try:
            resp = requests.get(WIKIMEDIA_BASE, headers=WIKIMEDIA_HEADERS, params=params, timeout=6)
            resp.raise_for_status()
            pages = resp.json().get("query", {}).get("pages", {})
            fotos = []
            for p in pages.values():
                ii = p.get("imageinfo", [{}])[0]
                mime = ii.get("mime", "")
                url = ii.get("thumburl", "")
                # Solo fotos, no logos ni SVGs
                if url and "image/jpeg" in mime or "image/png" in mime:
                    fotos.append(url)
            if fotos:
                return fotos[indice % len(fotos)]
        except Exception as e:
            print(f"Error Wikimedia: {e}")

    # Fallback a Pexels si Wikimedia no da resultado
    headers = {"Authorization": settings.PEXELS_API_KEY}
    params = {
        "query": f"{nombre} {ciudad} Mexico",
        "per_page": 10,
        "orientation": "landscape",
    }
    try:
        resp = requests.get(f"{PEXELS_BASE}/search", headers=headers, params=params, timeout=5)
        resp.raise_for_status()
        fotos = resp.json().get("photos", [])
        if fotos:
            return fotos[indice % len(fotos)]["src"]["medium"]
    except Exception:
        pass

    return None


def buscar_lugares(destino: str, categoria: str = "atracciones", limite: int = 12,
                   precio_min: int = 0, precio_max: int = 10000, subcategorias: list = None, popularidades: list = None):
    coords = obtener_coordenadas(destino)
    if not coords["lat"]:
        return []

    # Siempre consultar con categorías amplias para maximizar resultados.
    # El filtro por subcategoría (cultura/naturaleza/aventura/entretenimiento)
    # se aplica post-fetch sobre `categoria_filtro`, evitando que Geoapify
    # devuelva lista vacía con categorías muy específicas.
    cat = CATEGORY_MAP.get(categoria, "tourism,entertainment,leisure")

    # Pedir más resultados cuando hay filtros para compensar el descarte post-fetch
    api_limite = min(limite * 3, 100) if subcategorias else limite

    params = {
        "apiKey": settings.GEOAPIFY_API_KEY,
        "categories": cat,
        "filter": f"circle:{coords['lon']},{coords['lat']},20000",
        "limit": api_limite,
        "lang": "es",
        "conditions": "named",
        "country": "mx",  # ← solo México
    }
    try:
        resp = requests.get(GEOAPIFY_PLACES, params=params, timeout=10)
        resp.raise_for_status()
        features = resp.json().get("features", [])
    except Exception as e:
        print(f"Error Geoapify places: {e}")
        return []

    lugares = []
    for f in features:
        p   = f.get("properties", {})
        raw = p.get("datasource", {}).get("raw", {})

        nombre = p.get("name", "")
        if not nombre or nombre.lower() in ["yes", "no"]:
            continue

        ciudad = p.get("city", destino)


         # Filtrar solo lugares de México
        country = p.get("country_code", "")
        if country and country.lower() != "mx":
            continue

        # Foto
        foto = None
        wm = p.get("wiki_and_media", {})
        if wm.get("image"):
            foto = wm["image"]
        elif raw.get("image"):
            foto = raw["image"]
        else:
            foto = obtener_foto_lugar(nombre, ciudad, indice=len(lugares))

        # Rating
        rating = None
        acc = p.get("accommodation", {})
        if acc.get("stars"):
            rating = float(acc["stars"])

        # Precio estimado por categoría
        if categoria == "hoteles":
            estrellas = int(acc.get("stars", 3))
            precios_hotel = {1: "$500 - $1,000", 2: "$1,000 - $2,000",
                             3: "$2,000 - $4,000", 4: "$4,000 - $7,000", 5: "$7,000+"}
            precio_str = precios_hotel.get(estrellas, "$2,000 - $4,000") + " MXN/noche"
        elif categoria == "gastronomia":
            precio_str = "$150 - $500 MXN por persona"
        elif categoria == "atracciones":
            precio_str = "$200 - $1,500 MXN por persona"
        else:
            precio_str = None

        # Valor numérico del límite superior del precio para el filtro del slider
        if categoria == "hoteles":
            _estrellas_precio = {1: 1000, 2: 2000, 3: 4000, 4: 7000, 5: 15000}
            precio_max_num = _estrellas_precio.get(int(acc.get("stars", 3)), 4000)
        elif categoria == "gastronomia":
            precio_max_num = 500
        else:
            precio_max_num = 1500

        # Popularidad
        cats_str = str(p.get("categories", []))
        if "tourism" in cats_str or "attraction" in cats_str or "sights" in cats_str:
            label, color = "En Tendencia 🔥", "#0E9E8E"
        elif "catering" in cats_str or "restaurant" in cats_str:
            label, color = "Ambiente Vivo 🍽️", "#F59E0B"
        else:
            label, color = "Sin filas", "#6B7280"

        cat_display = []
        for c in p.get("categories", []):
            if "." in c:
                parte = c.split(".")[-1].replace("_", " ").title()
                if parte.lower() not in ["yes", "no"] and parte not in cat_display:
                    cat_display.append(parte)
        cat_display = cat_display[:2]

        # Determinar categoría de filtro
        categoria_filtro = obtener_categoria_filtro(p.get("categories", []))

        # ── Filtros post-fetch ─────────────────────────────
        # Subcategoría: descartar si el lugar no pertenece a ninguna de las seleccionadas
        if subcategorias and categoria_filtro not in subcategorias:
            continue

        # Precio: aplicar solo si el usuario bajó el slider (precio_max < 10000)
        if precio_max < 10000 and precio_max_num > precio_max:
            continue

        # Popularidad: filtrar si se seleccionó al menos una opción
        if popularidades and label not in popularidades:
            continue
        # ───────────────────────────────────────────────────

        lugares.append({
            "nombre":      nombre,
            "ciudad":      ciudad,
            "direccion":   p.get("address_line2", p.get("formatted", "")),
            "rating":      rating,
            "precio":      precio_str,
            "popularidad": label,
            "pop_color":   color,
            "foto":        foto,
            "categorias":  cat_display,
            "website":     p.get("website") or raw.get("website"),
            "telefono":    p.get("contact", {}).get("phone") or raw.get("phone"),
            "descripcion": p.get("description") or raw.get("description", ""),
            "lat":         p.get("lat"),
            "lon":         p.get("lon"),
            "precio_max_num": precio_max_num,
            "categoria_filtro": categoria_filtro,
        })

    return lugares

def obtener_foto_destino(destino: str):
    headers = {"Authorization": settings.PEXELS_API_KEY}
    params = {"query": f"{destino} Mexico travel", "per_page": 1, "orientation": "landscape"}
    try:
        resp = requests.get(f"{PEXELS_BASE}/search", headers=headers, params=params, timeout=6)
        resp.raise_for_status()
        fotos = resp.json().get("photos", [])
        if fotos:
            return fotos[0]["src"]["large"]
    except Exception as e:
        print(f"Error Pexels: {e}")
    return None

def obtener_fotos_lugar(nombre: str, ciudad: str, cantidad: int = 5):
    """Obtiene múltiples fotos landscape de Pexels para la galería."""
    headers = {'Authorization': settings.PEXELS_API_KEY}
    params = {
        'query': f'{nombre} {ciudad} Mexico',
        'per_page': cantidad,
        'orientation': 'landscape'
    }
    try:
        resp = requests.get(f'{PEXELS_BASE}/search', headers=headers,
                            params=params, timeout=5)
        resp.raise_for_status()
        fotos = resp.json().get('photos', [])
        return [f['src']['large'] for f in fotos]
    except Exception:
        return []

def obtener_detalle_lugar(nombre: str, ciudad: str, categoria: str):
    """
    Consolida datos para la pantalla Detalle de Atracción.
    Combina Geoapify (metadatos) + Pexels (galería).
    """
    # 1. Geocodificar para obtener coordenadas del lugar
    coords = obtener_coordenadas(f'{nombre} {ciudad}')

    # 2. Galería: 5 fotos de Pexels
    fotos = obtener_fotos_lugar(nombre, ciudad, cantidad=5)

    # 3. Precio estimado según categoría
    precio_map = {
        'atracciones': '$200 - $1,500 MXN por persona',
        'gastronomia':  '$150 - $500 MXN por persona',
        'hoteles':      '$2,000 - $4,000 MXN/noche',
    }
    precio = precio_map.get(categoria, 'Precio no disponible')

    # 4. Popularidad (inferida de categoría)
    if categoria == 'atracciones':
        popularidad = 'Lugar con popularidad alta'
    elif categoria == 'gastronomia':
        popularidad = 'Ambiente Vivo'
    else:
        popularidad = 'Disponible'

    return {
        'nombre':      nombre,
        'ciudad':      ciudad,
        'fotos':       fotos,          # lista de URLs para galería
        'descripcion': '',             # completar con IA si se desea
        'precio':      precio,
        'popularidad': popularidad,
        'lat':         coords['lat'],
        'lon':         coords['lon'],
    }