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


def buscar_lugares(destino: str, categoria: str = "atracciones", limite: int = 18,
                   precio_min: int = 0, precio_max: int = 99999):
    coords = obtener_coordenadas(destino)
    if not coords["lat"]:
        return []

    cat = CATEGORY_MAP.get(categoria, "tourism,entertainment,leisure")
    params = {
        "apiKey": settings.GEOAPIFY_API_KEY,
        "categories": cat,
        "filter": f"circle:{coords['lon']},{coords['lat']},20000",
        "limit": limite,
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

        # Popularidad
        cats_str = str(p.get("categories", []))
        if "tourism" in cats_str or "attraction" in cats_str or "sights" in cats_str:
            label, color = "En Tendencia 🔥", "#0E9E8E"
        elif "catering" in cats_str or "restaurant" in cats_str:
            label, color = "Ambiente Vivo 🎉", "#F59E0B"
        else:
            label, color = "Sin filas", "#6B7280"

        cat_display = []
        for c in p.get("categories", []):
            if "." in c:
                parte = c.split(".")[-1].replace("_", " ").title()
                if parte.lower() not in ["yes", "no"] and parte not in cat_display:
                    cat_display.append(parte)
        cat_display = cat_display[:2]

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