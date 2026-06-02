# apps/transporte/servicios_cbus.py
# ==========================================
# Mock de búsqueda de autobuses (RF-71)
# Para futuro: integrar con API real cuando esté disponible
# ==========================================

import time
import random
from datetime import datetime, timedelta
from .currency import convertir_precio, formatear_precio


# ==========================================
# Catálogo de ciudades con códigos
# ==========================================
CIUDADES = {
    'MEX': {'nombre': 'Ciudad de México', 'terminal': 'TAPO'},
    'GDL': {'nombre': 'Guadalajara', 'terminal': 'Central Nueva'},
    'MTY': {'nombre': 'Monterrey', 'terminal': 'Central de Autobuses'},
    'PUE': {'nombre': 'Puebla', 'terminal': 'CAPU'},
    'OAX': {'nombre': 'Oaxaca', 'terminal': 'Central ADO'},
    'QRO': {'nombre': 'Querétaro', 'terminal': 'Central de Autobuses'},
    'CUN': {'nombre': 'Cancún', 'terminal': 'Terminal ADO'},
    'VER': {'nombre': 'Veracruz', 'terminal': 'Central de Autobuses'},
    'MID': {'nombre': 'Mérida', 'terminal': 'CAME'},
    'TIJ': {'nombre': 'Tijuana', 'terminal': 'Central de Autobuses'},
    'ACA': {'nombre': 'Acapulco', 'terminal': 'Central Ejido'},
    'TPQ': {'nombre': 'Tepic', 'terminal': 'Central de Autobuses'},
    'GPE': {'nombre': 'Guadalupe', 'terminal': 'Central'},
    'SLP': {'nombre': 'San Luis Potosí', 'terminal': 'Terminal Terrestre'},
    'AGS': {'nombre': 'Aguascalientes', 'terminal': 'Central Camionera'},
}


# ==========================================
# Catálogo de empresas con sus servicios
# ==========================================
EMPRESAS = [
    {
        'nombre': 'ETN Turistar',
        'servicio': 'Servicio Lujo',
        'precio_base': 850.00,
        'factor_velocidad': 1.0,  # ruta directa
        'prefijo_corrida': 'ETN',
    },
    {
        'nombre': 'Primera Plus',
        'servicio': 'Servicio Ejecutivo',
        'precio_base': 680.00,
        'factor_velocidad': 1.0,
        'prefijo_corrida': 'PP',
    },
    {
        'nombre': 'ADO',
        'servicio': 'Servicio GL',
        'precio_base': 720.00,
        'factor_velocidad': 1.0,
        'prefijo_corrida': 'ADO',
    },
    {
        'nombre': 'ADO Platino',
        'servicio': 'Servicio Premium',
        'precio_base': 980.00,
        'factor_velocidad': 1.0,
        'prefijo_corrida': 'ADOP',
    },
    {
        'nombre': 'Estrella Blanca',
        'servicio': 'Económico',
        'precio_base': 520.00,
        'factor_velocidad': 1.3,  # más lento por más paradas
        'prefijo_corrida': 'EB',
    },
    {
        'nombre': 'OCC (Cristóbal Colón)',
        'servicio': 'Servicio Ejecutivo',
        'precio_base': 640.00,
        'factor_velocidad': 1.0,
        'prefijo_corrida': 'OCC',
    },
    {
        'nombre': 'Futura',
        'servicio': 'Económico',
        'precio_base': 580.00,
        'factor_velocidad': 1.2,
        'prefijo_corrida': 'FUT',
    },
]


# ==========================================
# Duraciones aproximadas entre ciudades (en horas)
# ==========================================
DURACIONES_BASE = {
    # Si la ruta no está aquí, se calcula aleatoriamente entre 4-8 horas
    ('MEX', 'GDL'): 7,
    ('MEX', 'MTY'): 12,
    ('MEX', 'PUE'): 2,
    ('MEX', 'OAX'): 6.5,
    ('MEX', 'QRO'): 3,
    ('MEX', 'CUN'): 24,
    ('MEX', 'VER'): 5,
    ('MEX', 'ACA'): 4.5,
    ('MEX', 'TPQ'): 9,
    ('GDL', 'TPQ'): 3.5,
    ('GDL', 'MTY'): 11,
    ('GDL', 'AGS'): 3,
    ('MTY', 'SLP'): 6,
    ('PUE', 'OAX'): 4,
    ('PUE', 'VER'): 3.5,
    ('CUN', 'MID'): 4,
    ('CUN', 'VER'): 16,
}


def obtener_duracion_base(origen, destino):
    """Obtiene la duración base entre dos ciudades, o la calcula si no existe."""
    if (origen, destino) in DURACIONES_BASE:
        return DURACIONES_BASE[(origen, destino)]
    if (destino, origen) in DURACIONES_BASE:
        return DURACIONES_BASE[(destino, origen)]
    return random.uniform(4, 8)  # Default 4-8 horas


def formatear_duracion(horas_decimales):
    """Convierte 4.5 → '4h 30m'"""
    horas = int(horas_decimales)
    minutos = int((horas_decimales - horas) * 60)
    if minutos == 0:
        return f"{horas}h"
    return f"{horas}h {minutos}m"


def buscar_autobuses_cbus(origen_codigo, destino_codigo, fecha_ida, pasajeros_num, moneda_usuario='MXN'):
    """
    Mock de búsqueda de autobuses con datos realistas.
    
    Parámetros:
        origen_codigo (str): Código de ciudad origen (ej: 'MEX')
        destino_codigo (str): Código de ciudad destino (ej: 'GDL')
        fecha_ida (str): Fecha en formato 'YYYY-MM-DD'
        pasajeros_num (int): Número de pasajeros
        moneda_usuario (str): Moneda del usuario para conversión
    
    Retorna:
        list: Lista de viajes disponibles
    """
    try:
        n = int(pasajeros_num)
    except (ValueError, TypeError):
        n = 1

    # ==========================================
    # Validar que existan las ciudades
    # ==========================================
    if origen_codigo not in CIUDADES or destino_codigo not in CIUDADES:
        return []

    origen_info = CIUDADES[origen_codigo]
    destino_info = CIUDADES[destino_codigo]

    # ==========================================
    # Calcular duración base de la ruta
    # ==========================================
    duracion_base_horas = obtener_duracion_base(origen_codigo, destino_codigo)

    # ==========================================
    # Simular latencia de API
    # ==========================================
    time.sleep(0.5)

    # ==========================================
    # Generar horarios de salida (cada 2-3 horas)
    # ==========================================
    horarios_salida = ['06:00', '08:30', '11:00', '14:00', '16:30', '19:00', '22:00']

    viajes_mock = []
    contador = 1

    # ==========================================
    # Generar viajes combinando empresas y horarios
    # ==========================================
    empresas_seleccionadas = random.sample(EMPRESAS, min(5, len(EMPRESAS)))

    for empresa in empresas_seleccionadas:
        # Cada empresa tiene 1-2 horarios
        num_horarios = random.randint(1, 2)
        horarios_empresa = random.sample(horarios_salida, num_horarios)

        for hora_salida_str in horarios_empresa:
            # Calcular hora de llegada con factor de velocidad
            duracion_real = duracion_base_horas * empresa['factor_velocidad']
            hora_salida_dt = datetime.strptime(f"{fecha_ida}T{hora_salida_str}:00", "%Y-%m-%dT%H:%M:%S")
            hora_llegada_dt = hora_salida_dt + timedelta(hours=duracion_real)

            # Determinar escalas (servicios económicos tienen escalas)
            tiene_escala = empresa['factor_velocidad'] > 1.1
            num_escalas = 1 if tiene_escala else 0
            escalas_texto = "1 parada" if tiene_escala else "Directo"

            # Calcular precio (con variación aleatoria pequeña)
            variacion = random.uniform(0.95, 1.10)
            precio_unitario = empresa['precio_base'] * variacion
            precio_total_mxn = round(precio_unitario * n, 2)

            # Convertir a la moneda del usuario
            precio_convertido = convertir_precio(precio_total_mxn, 'MXN', moneda_usuario)
            precio_formateado = formatear_precio(precio_convertido, moneda_usuario)

            viaje = {
                'offer_id': f"bus-mock-{contador:03d}",
                'aerolinea': empresa['nombre'],  # Mantenemos el nombre para compatibilidad
                'numero_vuelo': f"{empresa['prefijo_corrida']}-{random.randint(100, 999)}",
                'servicio': empresa['servicio'],
                'origen_codigo': origen_codigo,
                'origen_ciudad': origen_info['nombre'],
                'origen_terminal': origen_info['terminal'],
                'destino_codigo': destino_codigo,
                'destino_ciudad': destino_info['nombre'],
                'destino_terminal': destino_info['terminal'],
                'hora_salida': hora_salida_dt.strftime("%Y-%m-%dT%H:%M:%S"),
                'hora_llegada': hora_llegada_dt.strftime("%Y-%m-%dT%H:%M:%S"),
                'duracion': formatear_duracion(duracion_real),
                'escalas': num_escalas,
                'escalas_texto': escalas_texto,
                'precio': precio_total_mxn,
                'moneda': 'MXN',
                'precio_convertido': precio_convertido,
                'precio_formateado': precio_formateado,
                'moneda_usuario': moneda_usuario,
            }
            viajes_mock.append(viaje)
            contador += 1

    # ==========================================
    # Ordenar por hora de salida
    # ==========================================
    viajes_mock.sort(key=lambda v: v['hora_salida'])

    return viajes_mock