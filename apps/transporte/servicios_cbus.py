import time

def buscar_autobuses_cbus(origen_codigo, destino_codigo, fecha_ida, pasajeros_num):
    # Asegurarnos de que pasajeros_num sea un entero
    try:
        n = int(pasajeros_num)
    except:
        n = 1

    mapa_ids = {
        'MEX': '5', 'GPE': '1', 'OAX': '3', 'PUE': '4', 'TPQ': '2'
    }
    
    nombres_bonitos = {
        'MEX': 'Ciudad de México', 'GPE': 'Guadalupe',
        'OAX': 'Oaxaca', 'PUE': 'Puebla', 'TPQ': 'Tepic'
    }

    origen_id = mapa_ids.get(origen_codigo)
    destino_id = mapa_ids.get(destino_codigo)

    if not origen_id or not destino_id:
        return []

    origen_display = nombres_bonitos.get(origen_codigo)
    destino_display = nombres_bonitos.get(destino_codigo)

    # Precios base unitarios
    PRECIO_ETN = 850.00
    PRECIO_PP = 680.00

    time.sleep(1)
    
    # Calculamos el total dinámicamente
    viajes_mock = [
        {
            'offer_id': 'cbus-mock-001', 
            'aerolinea': 'ETN Turistar', 
            'numero_vuelo': 'Servicio Lujo', 
            'origen_codigo': origen_display,
            'destino_codigo': destino_display,
            'hora_salida': f"{fecha_ida}T08:00:00",
            'hora_llegada': f"{fecha_ida}T12:30:00",
            'duracion': "4h 30m", 
            'escalas_texto': "Directo",
            'escalas': 0,
            'precio_convertido': PRECIO_ETN * n, # <--- Multiplicación aquí
            'precio_formateado': f"${(PRECIO_ETN * n):,.2f}",
            'moneda_usuario': 'MXN' 
        },
        {
            'offer_id': 'cbus-mock-002', 
            'aerolinea': 'Primera Plus', 
            'numero_vuelo': 'Servicio Ejecutivo', 
            'origen_codigo': origen_display,
            'destino_codigo': destino_display,
            'hora_salida': f"{fecha_ida}T10:15:00",
            'hora_llegada': f"{fecha_ida}T14:45:00",
            'duracion': "4h 30m", 
            'escalas_texto': "Directo",
            'escalas': 0,
            'precio_convertido': PRECIO_PP * n, # <--- Multiplicación aquí
            'precio_formateado': f"${(PRECIO_PP * n):,.2f}",
            'moneda_usuario': 'MXN' 
        }
    ]
    
    return viajes_mock