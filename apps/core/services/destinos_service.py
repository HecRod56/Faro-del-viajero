#destinos_service.py core
import re
import requests
import unicodedata
from django.conf import settings


# ─── Diccionarios de precios por nombre de lugar ─────────────────────────────
# Detecta por palabras clave en el NOMBRE del lugar (en español)
# Se usa como fallback cuando OSM no tiene precio real

# ── ATRACCIONES ───────────────────────────────────────────────────────────────
ATRACCIONES_GRATIS = [
    # Monumentos y estatuas
    "monumento", "estatua", "obelisco", "columna", "fuente", "memorial",
    "cenotafio", "mural", "placa", "busto",
    # Plazas y espacios públicos
    "plaza", "zócalo", "jardín", "jardin", "parque", "alameda", "paseo",
    "boulevard", "malecón", "malecon", "explanada", "glorieta",
    # Miradores
    "mirador", "mirador", "punto panorámico", "panoramico", "viewpoint",
    # Iglesias y templos (entrada libre generalmente)
    "iglesia", "catedral", "templo", "parroquia", "capilla", "santuario",
    "basílica", "basilica", "convento", "ex convento",
    # Naturaleza gratuita
    "cerro", "volcán", "volcan", "laguna", "lago", "rio", "río",
    "cascada", "playa", "reserva", "bosque", "selva",
    # Mercados y espacios culturales gratuitos
    "mercado", "tianguis", "corredor", "andador",
]

ATRACCIONES_BAJO = [  # $50 - $150 MXN
    "museo", "galeria", "galería", "pinacoteca", "exposición", "exposicion",
    "centro cultural", "casa de la cultura", "archivo", "biblioteca",
    "planetario", "observatorio", "acuario pequeño",
    "zona arqueológica", "zona arqueologica", "ruinas", "pirámide", "piramide",
    "hacienda", "ex hacienda", "palacio", "casa museo",
]

ATRACCIONES_MEDIO = [  # $150 - $500 MXN
    "zoológico", "zoologico", "zoo", "acuario", "vivarium",
    "jardín botánico", "jardin botanico", "mariposario",
    "museo interactivo", "museo de ciencias", "papalote",
    "parque ecológico", "parque ecologico", "ecoparque",
    "temazcal", "granja", "rancho",
    "teatro", "auditorio", "foro", "sala de conciertos",
    "cinema", "cine",
]

ATRACCIONES_ALTO = [  # $400 - $1,500 MXN
    "parque acuático", "parque acuatico", "parque de diversiones",
    "parque temático", "parque tematico", "parque de atracciones",
    "xcaret", "xel-ha", "xplor", "xenses", "xenotes",
    "six flags", "reino aventura", "kidzania",
    "tour", "excursión", "excursion", "recorrido", "aventura",
    "tirolesa", "zip line", "rapel", "escalada",
    "cenote", "snorkel", "buceo", "kayak", "rafting",
    "catamaran", "catamarán", "yate", "lancha", "barco",
    "globo", "vuelo",
]

# ── GASTRONOMÍA ───────────────────────────────────────────────────────────────
GASTRO_MUY_BAJO = [  # $50 - $150 MXN
    # Antojitos y comida rápida
    "taqueria", "taquería", "tacos", "taco", "antojitos",
    "tortas", "torta", "sandwiches", "loncheria", "lonchería",
    "quesadillas", "quesadilla", "sopes", "gorditas", "gordita",
    "tamales", "tamal", "elotes", "tlayuda",
    "hot dog", "hot dogs", "hamburguesa", "hamburguesería", "hamburguesas",
    "pizza", "pizzeria", "pizzería",
    "helados", "heladería", "neveria", "nevería", "nieve", "paletas",
    "jugos", "jugería", "jugeria", "licuados", "smoothie",
    "café de olla", "atole", "champurrado",
    # Mercados y fondas
    "fonda", "comedor", "cocina económica", "cocina economica",
    "comida corrida", "menú del día", "menu del dia",
    "puesto", "mercado", "tianguis",
]

GASTRO_BAJO = [  # $150 - $350 MXN
    "cafe", "café", "cafetería", "cafeteria", "coffee",
    "pastelería", "pasteleria", "repostería", "reposteria", "panadería", "panaderia",
    "crepas", "crepes", "waffles",
    "sushi", "ramen", "pho", "thai", "chino", "chifa",
    "mariscos", "ceviche", "tostadas",
    "vegetariano", "vegano", "organico", "orgánico",
    "buffet", "smorgasbord",
    "cantina", "pulquería", "pulqueria",
    "cervecería", "cerveceria", "brewery",
]

GASTRO_MEDIO = [  # $350 - $700 MXN
    "restaurante", "restaurant", "cocina", "cuisine",
    "bar", "bar restaurante", "gastropub",
    "marisquería", "marisqueria", "pescados",
    "parrilla", "asador", "bbq", "barbacoa", "carnitas",
    "italiano", "pasta", "trattoria",
    "francés", "frances", "bistro", "brasserie",
    "japonés", "japones", "teppanyaki", "tempura",
    "tapas", "español", "espanol",
    "libanés", "libanes", "árabe", "arabe", "shawarma",
    "indio", "hindú", "hindu", "thai", "vietnamita",
]

GASTRO_ALTO = [  # $700 - $2,000 MXN
    "grill", "steakhouse", "cortes", "carne premium",
    "roof", "rooftop", "sky", "terraza panorámica", "terraza panoramica",
    "fine dining", "alta cocina", "gastronomía", "gastronomia",
    "chef", "gran chef", "michelin",
    "vino", "wine bar", "bodega", "cava",
    "mariscos finos", "langosta", "langostinos", "ostiones",
    "hotel restaurante", "boutique",
    "gran", "grand", "palacio", "real", "imperial",
]

# ── HOTELES ───────────────────────────────────────────────────────────────────
HOTEL_MUY_BAJO = [  # $300 - $700 MXN/noche
    "hostal", "hostel", "backpacker", "mochilero",
    "albergue", "dormitorio", "posada económica", "posada economica",
    "cuarto", "habitación", "habitacion", "casa de huéspedes", "casa de huespedes",
    "pensión", "pension",
]

HOTEL_BAJO = [  # $700 - $1,500 MXN/noche
    "posada", "motel", "auto hotel", "autohotel",
    "inn", "bed and breakfast", "b&b",
    "bungalow", "cabaña", "cabana", "cabañas",
    "villa", "casita",
]

HOTEL_MEDIO = [  # $1,500 - $3,000 MXN/noche
    "hotel", "suites", "aparthotel",
    "holiday", "express", "select",
    "fiesta", "camino real", "misión", "mission",
    "best western", "comfort", "quality",
]

HOTEL_ALTO = [  # $3,000 - $6,000 MXN/noche
    "grand", "gran", "real", "royal",
    "marriott", "hilton", "hyatt", "sheraton", "westin",
    "crowne", "intercontinental", "four points",
    "presidente", "reforma",
    "boutique", "design hotel",
]

HOTEL_LUJO = [  # $6,000+ MXN/noche
    "palace", "palacio", "five star", "cinco estrellas",
    "ritz", "waldorf", "st regis", "four seasons",
    "live aqua", "paradisus", "excellence",
    "presidential", "penthouse", "resort & spa",
    "grand velas", "vidanta", "banyan tree",
]


def obtener_rango_precio_atraccion(precio):
    """
    Retorna la categoría de precio basada en el valor numérico para atracciones.
    Función de compatibilidad que reutiliza los umbrales de extraer_precio_real().
    """
    if precio is None:
        return "No disponible"
    if precio == 0:
        return "Gratuito"
    if precio <= 150:
        return "Económico"
    if precio <= 500:
        return "Moderado"
    return "Premium"


def obtener_rango_precio_gastronomia(precio_promedio):
    """
    Retorna la categoría de precio para establecimientos gastronómicos.
    Función de compatibilidad que reutiliza los umbrales de extraer_precio_real().
    """
    if precio_promedio is None:
        return "No disponible"
    if precio_promedio <= 150:
        return "Económico"
    if precio_promedio <= 700:
        return "Moderado"
    return "Premium"


def inferir_nivel_hotel(nombre: str, precio_max_num: int) -> str:
    """
    Infiere el nivel del hotel usando las palabras clave de los diccionarios HOTEL_*
    y como fallback el precio numérico estimado.
    Devuelve: 'hotel_muy_bajo', 'hotel_bajo', 'hotel_medio', 'hotel_alto' o 'hotel_lujo'.
    Esto reemplaza el filtro por estrellas OSM, que rara vez está disponible en Geoapify.
    """
    nombre_lower = nombre.lower()
    if any(k in nombre_lower for k in HOTEL_LUJO):
        return "hotel_lujo"
    if any(k in nombre_lower for k in HOTEL_ALTO):
        return "hotel_alto"
    if any(k in nombre_lower for k in HOTEL_MUY_BAJO):
        return "hotel_muy_bajo"
    if any(k in nombre_lower for k in HOTEL_BAJO):
        return "hotel_bajo"
    # Fallback por rango de precio numérico estimado
    if precio_max_num >= 6000:
        return "hotel_lujo"
    if precio_max_num >= 3000:
        return "hotel_alto"
    if precio_max_num >= 1500:
        return "hotel_medio"
    if precio_max_num >= 700:
        return "hotel_bajo"
    return "hotel_muy_bajo"


GEOAPIFY_BASE     = "https://api.geoapify.com/v1"
GEOAPIFY_PLACES   = "https://api.geoapify.com/v2/places"
FOURSQUARE_PLACES = "https://api.foursquare.com/v3/places/search"
PEXELS_BASE       = "https://api.pexels.com/v1"
WIKIMEDIA_BASE    = "https://commons.wikimedia.org/w/api.php"
WIKIMEDIA_HEADERS = {"User-Agent": "FaroDelViajero/1.0 (farodelviajero@gmail.com)"}

CATEGORY_MAP = {
    "atracciones": "tourism,entertainment,leisure",
    "gastronomia": "catering.restaurant,catering.cafe,catering.bar,catering.fast_food,catering.pub,catering.food_court,catering.ice_cream",
    "hoteles":     "accommodation",
}

SUBCATEGORY_MAP = {
    'cultura':       'tourism.museum,tourism.historic,tourism.monument,tourism.archaeological,tourism.castle,tourism.sights',
    'naturaleza':    'leisure.park,leisure.beach,leisure.nature_reserve,leisure.garden,leisure.picnic_site',
    'aventura':      'sport,leisure.sports_centre,leisure.stadium,leisure.fitness,leisure.golf_course,leisure.ski,leisure.water_park',
    'entretenimiento': 'entertainment.cinema,entertainment.theatre,entertainment.concert_hall,entertainment.music_venue,entertainment.nightclub,entertainment.casino',
    'restaurantes':  'catering.restaurant',
    'cafes':         'catering.cafe,catering.ice_cream',
    'bares':         'catering.bar,catering.pub,catering.biergarten',
    'comida_rapida': 'catering.fast_food,catering.food_court',
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
    'catering.restaurant': 'restaurantes',
    'catering.cafe': 'cafes',
    'catering.ice_cream': 'cafes',
    'catering.bar': 'bares',
    'catering.pub': 'bares',
    'catering.biergarten': 'bares',
    'catering.fast_food': 'comida_rapida',
    'catering.food_court': 'comida_rapida',
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


# ─── Foursquare: popularidad real ─────────────────────────────────────────────

def obtener_popularidad_lugar_foursquare(lat: float, lon: float, nombre: str) -> tuple:
    """
    Busca la popularidad de un lugar específico en Foursquare usando sus coordenadas y nombre.
    Devuelve (label, color) o None si no se encuentra o no hay datos.
    """
    key = getattr(settings, 'FOURSQUARE_API_KEY', '')
    if not key or not lat or not lon:
        return None

    headers = {"Authorization": key, "Accept": "application/json"}
    # Usamos un radio de 500m y el nombre para encontrar exactamente este lugar
    params = {
        "ll": f"{lat},{lon}",
        "radius": 500,
        "query": nombre,
        "limit": 1,
        "fields": "name,popularity,stats"
    }

    try:
        # Timeout más corto para no demorar mucho la carga total si hay varios lugares
        resp = requests.get(FOURSQUARE_PLACES, headers=headers, params=params, timeout=3)
        resp.raise_for_status()
        results = resp.json().get("results", [])
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response is not None else "unknown"
        # Foursquare v3 está devolviendo 410 Gone de forma permanente para este endpoint
        if status != 410:
            print(f"[Foursquare] HTTP {status} al buscar '{nombre}': {e}")
        return None
    except Exception as e:
        print(f"[Foursquare] Error al buscar '{nombre}': {e}")
        return None

    if not results:
        return None

    place = results[0]
    pop = place.get("popularity")
    
    if pop is None:
        checkins = place.get("stats", {}).get("totalCheckins", 0)
        pop = min(checkins / 10_000, 1.0)

    if pop >= 0.70:
        return "Muy popular", "#0E9E8E"
    elif pop >= 0.35:
        return "Popular", "#F59E0B"
    else:
        return "Poco concurrido", "#6B7280"


def _popularidad_fallback(categorias: list) -> tuple:
    """
    Estima el nivel de afluencia esperado basándose en las categorías de Geoapify.
    Usado cuando Foursquare no devuelve dato para ese lugar.

    Muy popular  → entretenimiento de pago, parques temáticos, estadios,
                    zoológicos, cines, teatros, discotecas, casinos.
    Popular → museos, sitios históricos, restaurantes, bares,
                    deportes, atracciones turísticas generales.
    Poco concurrido     → parques, jardines, naturaleza, monumentos, miradores.
    """
    cats = " ".join(categorias).lower()

    MUY_POPULAR = (
        "entertainment",   # cubre entertainment.cinema, .theatre, .nightclub, etc.
        "theme_park",
        "water_park",
        "amusement",
        "zoo", "aquarium",
        "stadium",
        "concert",
        "nightclub", "casino",
        "leisure.ski",
        "bar", "pub", "fast_food", "food_court",  # <--- Bares y comida rápida suelen estar llenos
    )
    POPULAR = (
        "museum", "historic", "castle", "archaeological",
        "sights", "attraction",
        "restaurant", "cafe",  # <--- Restaurantes formales y cafés
        "sport", "fitness", "golf",
        "tourism",
    )

    for kw in MUY_POPULAR:
        if kw in cats:
            return "Muy popular", "#0E9E8E"
    for kw in POPULAR:
        if kw in cats:
            return "Popular", "#F59E0B"
    return "Poco concurrido", "#6B7280"


# ─── Rangos estimados por categoría (fallback) ───────────────────────────────
_PRECIO_FALLBACK = {
    "hoteles":    {1: ("$500 - $1,000",   1000),
                   2: ("$1,000 - $2,000", 2000),
                   3: ("$2,000 - $4,000", 4000),
                   4: ("$4,000 - $7,000", 7000),
                   5: ("$7,000+",         15000)},
    "gastronomia": {
        "$":    ("$50 - $150 MXN",      150),
        "$$":   ("$150 - $300 MXN",     300),
        "$$$":  ("$300 - $600 MXN",     600),
        "$$$$": ("$600+ MXN",           1500),
    },
}


def extraer_precio_real(raw: dict, acc: dict, categoria: str, categorias_geo: list = None):
    """
    Intenta obtener un precio real del campo OSM `raw`.
    Devuelve (precio_str, precio_max_num).
    """
    cats_str = " ".join(categorias_geo or []).lower()

    # 1. Entrada gratuita explícita
    if str(raw.get("fee", "")).lower() == "no":
        return "Gratis", 0

    # 2. Campo `charge` con precio real
    charge = str(raw.get("charge", "") or raw.get("entrance_fee", "")).strip()
    if charge:
        nums = re.findall(r'[\d,\.]+', charge.replace(",", ""))
        if nums:
            try:
                valor = float(nums[0])
                return f"${valor:,.0f} MXN", int(valor)
            except ValueError:
                pass
# 3. Restaurantes
    if categoria == "gastronomia":
        pr = str(raw.get("price_range","") or raw.get("price_level","")).strip()
        if pr in _PRECIO_FALLBACK["gastronomia"]:
            txt, num = _PRECIO_FALLBACK["gastronomia"][pr]
            return txt + " por persona", num
        nombre_lower = str(raw.get("name","")).lower()
        if any(k in nombre_lower for k in GASTRO_MUY_BAJO) or any(k in cats_str for k in ["fast_food","food_court","ice_cream"]):
            return "$50 - $150 MXN por persona", 150
        elif any(k in nombre_lower for k in GASTRO_BAJO) or "cafe" in cats_str:
            return "$150 - $350 MXN por persona", 350
        elif any(k in nombre_lower for k in GASTRO_ALTO):
            return "$700 - $2,000 MXN por persona", 2000
        elif any(k in nombre_lower for k in GASTRO_MEDIO) or "restaurant" in cats_str:
            return "$350 - $700 MXN por persona", 700
        else:
            return "$150 - $500 MXN por persona", 500

    # 4. Hoteles
    if categoria == "hoteles":
        estrellas_val = acc.get("stars") or raw.get("stars")
        if estrellas_val:
            estrellas = max(1, min(int(estrellas_val), 5))
            txt, num = _PRECIO_FALLBACK["hoteles"].get(estrellas, ("$2,000 - $4,000", 4000))
            return txt + " MXN/noche", num
        nombre_lower = str(raw.get("name","")).lower()
        if any(k in nombre_lower for k in HOTEL_MUY_BAJO):
            return "$300 - $700 MXN/noche", 700
        elif any(k in nombre_lower for k in HOTEL_BAJO):
            return "$700 - $1,500 MXN/noche", 1500
        elif any(k in nombre_lower for k in HOTEL_ALTO):
            return "$3,000 - $6,000 MXN/noche", 6000
        elif any(k in nombre_lower for k in HOTEL_LUJO):
            return "$6,000+ MXN/noche", 15000
        else:
            return "$500 - $4,000 MXN/noche", 4000

    # 5. Atracciones
    if categoria == 'atracciones':
        nombre_lower = str(raw.get("name", "")).lower()
        if any(k in nombre_lower for k in ATRACCIONES_GRATIS) or any(k in cats_str for k in ["monument","artwork","viewpoint","historic","memorial","park","garden","beach"]):
            return "Gratis", 0
        elif any(k in nombre_lower for k in ATRACCIONES_BAJO):
            return "$50 - $150 MXN por persona", 150
        elif any(k in nombre_lower for k in ATRACCIONES_MEDIO):
            return "$150 - $500 MXN por persona", 500
        elif any(k in nombre_lower for k in ATRACCIONES_ALTO):
            return "$400 - $1,500 MXN por persona", 1500
        else:
            return "$300 - $1,000 MXN por persona", 500
    return "$0 - $500 MXN", 500

def buscar_lugares(destino: str, categoria: str = "atracciones", limite: int = 12,
                   precio_min: int = 0, precio_max: int = 10000, subcategorias: list = None, 
                   popularidades: list = None, estrellas: list = None, servicios: list = None):
    coords = obtener_coordenadas(destino)
    if not coords["lat"]:
        return []

    # Siempre consultar con categorías amplias para maximizar resultados.
    # El filtro por subcategoría (cultura/naturaleza/aventura/entretenimiento)
    # se aplica post-fetch sobre `categoria_filtro`, evitando que Geoapify
    # devuelva lista vacía con categorías muy específicas.
    cat = CATEGORY_MAP.get(categoria, "tourism,entertainment,leisure")

    # Pedir más resultados cuando hay filtros para compensar el descarte post-fetch
    hay_filtros = bool(subcategorias or estrellas or servicios or popularidades)
    api_limite = 100 if hay_filtros else limite

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

        # Precio real desde OSM / fallback por categoría
        precio_str, precio_max_num = extraer_precio_real(raw, acc, categoria, p.get("categories", []))

        # ── Popularidad: Foursquare (real) con fallback inteligente por categoría ────────
        # Foursquare Places API v3 /search está deprecado (devuelve 410 Gone).
        # Pasamos directamente al fallback usando la metadata de Geoapify, lo cual es más rápido.
        label, color = _popularidad_fallback(p.get("categories", []))

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
        # Subcategoría: para hoteles se filtra por nivel (hotel_lujo/alto/medio/bajo/muy_bajo)
        # inferido por palabras clave del nombre, ya que OSM raramente provee `stars`.
        # Para atracciones y gastronomía se usa categoria_filtro derivada de Geoapify.
        if categoria == "hoteles":
            nivel_hotel = inferir_nivel_hotel(nombre, precio_max_num)
            if subcategorias and nivel_hotel not in subcategorias:
                continue
        else:
            if subcategorias and categoria_filtro not in subcategorias:
                continue

        # Precio: aplicar filtro de rango (precio_min y precio_max)
        if precio_max_num < precio_min or precio_max_num > precio_max:
            continue

        # Popularidad: filtrar si se seleccionó al menos una opción
        if popularidades and label not in popularidades:
            continue

        # Filtros exclusivos de Hoteles
        if categoria == "hoteles":
            
            # Filtrar por servicios
            if servicios:
                facilities = p.get("facilities", {})
                raw_facilities = raw.get("facilities", {})
                cumple_todos = True
                
                # Checkeamos si tiene alberca o mascotas según facilities o categories
                categorias_str = " ".join(p.get("categories", []))
                
                if "alberca" in servicios:
                    has_pool = ("swimming_pool" in facilities or "swimming_pool" in raw_facilities or 
                                "swimming_pool" in categorias_str)
                    if not has_pool:
                        cumple_todos = False
                        
                if "mascotas" in servicios:
                    has_pets = ("pets_allowed" in facilities or "dogs" in raw_facilities or 
                                "pet" in categorias_str or "dogs" in categorias_str)
                    if not has_pets:
                        cumple_todos = False

                if "wifi" in servicios:
                    has_wifi = ("internet_access" in facilities or "internet_access" in raw_facilities or
                                "internet_access" in categorias_str)
                    if not has_wifi:
                        cumple_todos = False

                if "estacionamiento" in servicios:
                    has_parking = ("parking" in facilities or "parking" in raw_facilities or
                                   "parking" in categorias_str)
                    if not has_parking:
                        cumple_todos = False

                if "accesibilidad" in servicios:
                    has_wheelchair = ("wheelchair" in facilities or "wheelchair" in raw_facilities or
                                      "wheelchair" in categorias_str)
                    if not has_wheelchair:
                        cumple_todos = False
                        
                if not cumple_todos:
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
            "nivel_hotel":     inferir_nivel_hotel(nombre, precio_max_num) if categoria == "hoteles" else None,
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
    """
    Obtiene múltiples fotos en calidad Full HD para la galería.
    Intenta primero Wikimedia Commons, luego completa con Pexels si es necesario.
    Omite la primera imagen de Wikimedia para evitar redundancia con la portada de grid.
    """
    fotos = []
    primera_consulta = True
    
    # 1. Intentar con Wikimedia Commons primero (Full HD: 1920px)
    queries = [nombre, f"{nombre} {ciudad}", f"{ciudad} Mexico"]
    for query in queries:
        if len(fotos) >= cantidad:
            break
            
        params = {
            "action": "query",
            "generator": "search",
            "gsrsearch": query,
            "gsrnamespace": 6,
            "gsrlimit": 10,
            "prop": "imageinfo",
            "iiprop": "url|size|mime",
            "iiurlwidth": 1920,  # Full HD quality
            "format": "json",
        }
        try:
            resp = requests.get(WIKIMEDIA_BASE, headers=WIKIMEDIA_HEADERS, params=params, timeout=6)
            resp.raise_for_status()
            pages = resp.json().get("query", {}).get("pages", {})
            primera_foto_consulta = True  # Flag para omitir la primera foto de la primera consulta
            for p in pages.values():
                if len(fotos) >= cantidad:
                    break
                # Omitir la primera foto de la primera consulta (es la portada)
                if primera_consulta and primera_foto_consulta:
                    primera_foto_consulta = False
                    continue
                ii = p.get("imageinfo", [{}])[0]
                mime = ii.get("mime", "")
                url = ii.get("thumburl", "")
                # Solo fotos, no logos ni SVGs
                if url and ("image/jpeg" in mime or "image/png" in mime):
                    fotos.append(url)
        except Exception as e:
            print(f"Error Wikimedia: {e}")
        
        primera_consulta = False
    
    # 2. Completar con Pexels si no hay suficientes fotos (original quality)
    if len(fotos) < cantidad:
        headers = {"Authorization": settings.PEXELS_API_KEY}
        params = {
            "query": f"{nombre} {ciudad} Mexico",
            "per_page": cantidad - len(fotos),
            "orientation": "landscape",
        }
        try:
            resp = requests.get(f"{PEXELS_BASE}/search", headers=headers, params=params, timeout=5)
            resp.raise_for_status()
            fotos_pexels = resp.json().get("photos", [])
            fotos.extend([f["src"]["original"] for f in fotos_pexels])
        except Exception as e:
            print(f"Error Pexels en obtener_fotos_lugar: {e}")
    
    return fotos[:cantidad]

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
        popularidad = 'Popular'
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