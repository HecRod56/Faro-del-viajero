# apps/transporte/services.py
# ==========================================
# Servicio de búsqueda de vuelos con Duffel API (RF-71)
# Usa requests directamente porque la librería duffel-api
# envía una versión de header obsoleta.
# ==========================================

import requests
from django.conf import settings
from .currency import convertir_precio, formatear_precio

# ==========================================
# URL base y versión actual de la API de Duffel
# ==========================================
DUFFEL_API_URL = "https://api.duffel.com/air/offer_requests"
DUFFEL_VERSION = "v2"


def buscar_vuelos(origen, destino, fecha_ida, fecha_regreso=None, pasajeros=1, moneda_usuario='USD'):
    """
    Consulta la API de Duffel para buscar ofertas de vuelos.

    Parámetros:
        origen (str): Código IATA del aeropuerto de salida (ej: 'MEX')
        destino (str): Código IATA del aeropuerto de llegada (ej: 'CUN')
        fecha_ida (str): Fecha de ida en formato 'YYYY-MM-DD'
        fecha_regreso (str, opcional): Fecha de regreso en formato 'YYYY-MM-DD'
        pasajeros (int): Número de pasajeros adultos
        moneda_usuario (str): Código de la moneda del usuario

    Retorna:
        list: Lista de diccionarios con la información de cada vuelo
    """

    # ==========================================
    # 1. Preparar los headers de autenticación
    # ==========================================
    headers = {
        "Authorization": f"Bearer {settings.DUFFEL_ACCESS_TOKEN}",
        "Duffel-Version": DUFFEL_VERSION,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    # ==========================================
    # 2. Definir los tramos del viaje (slices)
    # ==========================================
    slices = [
        {
            "origin": origen,
            "destination": destino,
            "departure_date": fecha_ida,
        }
    ]

    # Si hay fecha de regreso, agregar el tramo de vuelta
    if fecha_regreso:
        slices.append({
            "origin": destino,
            "destination": origen,
            "departure_date": fecha_regreso,
        })

    # ==========================================
    # 3. Definir los pasajeros
    # ==========================================
    passengers = [{"type": "adult"} for _ in range(pasajeros)]

    # ==========================================
    # 4. Construir el body de la petición
    # ==========================================
    payload = {
        "data": {
            "slices": slices,
            "passengers": passengers,
            "cabin_class": "economy",
        }
    }

    # ==========================================
    # 5. Hacer la petición a Duffel 
    # ==========================================
    try:
        response = requests.post(
            DUFFEL_API_URL,
            json=payload,
            headers=headers,
            params={"return_offers": "true"},
            timeout=15,  # Duffel puede tardar un poco en test mode
        )

        # Si hay error HTTP, mostrarlo
        if response.status_code not in [200, 201]:
            print(f"[Duffel ERROR] Status {response.status_code}: {response.text[:500]}")
            return []

        data = response.json()

    except requests.exceptions.Timeout:
        print("[Duffel ERROR] Timeout: La API tardó más de 15 segundos")
        return []
    except Exception as e:
        print(f"[Duffel ERROR] No se pudo conectar con la API: {e}")
        return []

    # ==========================================
    # 6. Procesar y formatear los resultados
    # ==========================================
    vuelos = []
    offers = data.get("data", {}).get("offers", [])

    for offer in offers:
        # Información del primer tramo (ida)
        primer_slice = offer["slices"][0]
        segmentos = primer_slice["segments"]
        primer_segmento = segmentos[0]
        ultimo_segmento = segmentos[-1]

        # Número de escalas
        num_escalas = len(segmentos) - 1

        # Duración del tramo
        duracion = primer_slice.get("duration", "")
        # Formatear duración ISO 8601 (PT2H15M → 2h 15m)
        duracion_formateada = formatear_duracion(duracion)

        vuelo = {
            # Identificador de la oferta
            "offer_id": offer["id"],

            # Aerolínea
            "aerolinea": offer.get("owner", {}).get("name", "Desconocida"),

            # Origen
            "origen_codigo": primer_segmento["origin"]["iata_code"],
            "origen_ciudad": primer_segmento["origin"].get("city_name", primer_segmento["origin"].get("name", "")),
            "hora_salida": primer_segmento["departing_at"],

            # Destino
            "destino_codigo": ultimo_segmento["destination"]["iata_code"],
            "destino_ciudad": ultimo_segmento["destination"].get("city_name", ultimo_segmento["destination"].get("name", "")),
            "hora_llegada": ultimo_segmento["arriving_at"],

            # Detalles del vuelo
            "duracion": duracion_formateada,
            "escalas": num_escalas,
            "escalas_texto": "Directo" if num_escalas == 0 else f"{num_escalas} escala(s)",
            "numero_vuelo": f"{primer_segmento.get('marketing_carrier', {}).get('iata_code', '')}-{primer_segmento.get('marketing_carrier_flight_number', '')}",

            # Precio
            "precio": offer["total_amount"],
            "moneda": offer["total_currency"],

            # Precio convertido a la moneda del usuario
            "precio_original": offer["total_amount"],
            "moneda_original": offer["total_currency"],
        }

        vuelos.append(vuelo)

   # ==========================================
    # 7. Convertir precios a la moneda del usuario
    # ==========================================
    from .currency import convertir_precio, formatear_precio

    for vuelo in vuelos:
        precio_convertido = convertir_precio(
            vuelo["precio"],
            vuelo["moneda"],
            moneda_usuario
        )
        vuelo["precio_convertido"] = precio_convertido
        vuelo["precio_formateado"] = formatear_precio(precio_convertido, moneda_usuario)
        vuelo["moneda_usuario"] = moneda_usuario

    # ==========================================
    # 8. Ordenar por precio convertido (más barato primero)
    # ==========================================
    vuelos.sort(key=lambda v: v["precio_convertido"])

    return vuelos


def formatear_duracion(duracion_iso):
    """
    Convierte duración ISO 8601 a formato legible.
    Ejemplo: 'PT2H15M' → '2h 15m'
             'PT13H30M' → '13h 30m'
    """
    if not duracion_iso:
        return ""

    duracion_iso = duracion_iso.replace("PT", "")
    horas = ""
    minutos = ""

    if "H" in duracion_iso:
        partes = duracion_iso.split("H")
        horas = partes[0] + "h"
        duracion_iso = partes[1] if len(partes) > 1 else ""

    if "M" in duracion_iso:
        minutos = duracion_iso.replace("M", "") + "m"

    return f"{horas} {minutos}".strip()