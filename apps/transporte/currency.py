# apps/transporte/currency.py
# ==========================================
# Servicio de conversión de moneda (RF-75)
# Tasas de cambio aproximadas desde USD
# ==========================================

# Tasas de cambio base: 1 USD = X moneda
TASAS_CAMBIO = {
    'USD': 1.00,
    'MXN': 17.50,
    'EUR': 0.92,
    'COP': 4150.00,
}

# Símbolos de moneda
SIMBOLOS = {
    'USD': 'US$',
    'MXN': '$',
    'EUR': '€',
    'COP': 'COL$',
}


def convertir_precio(precio, moneda_origen, moneda_destino):
    """
    Convierte un precio de una moneda a otra.
    
    Parámetros:
        precio (float/str): Precio a convertir
        moneda_origen (str): Código de moneda origen (ej: 'USD')
        moneda_destino (str): Código de moneda destino (ej: 'MXN')
    
    Retorna:
        float: Precio convertido, redondeado a 2 decimales
    """
    precio = float(precio)

    # Si son la misma moneda, no convertir
    if moneda_origen == moneda_destino:
        return round(precio, 2)

    # Convertir a USD primero (moneda base)
    tasa_origen = TASAS_CAMBIO.get(moneda_origen, 1.0)
    precio_usd = precio / tasa_origen

    # Convertir de USD a moneda destino
    tasa_destino = TASAS_CAMBIO.get(moneda_destino, 1.0)
    precio_convertido = precio_usd * tasa_destino

    return round(precio_convertido, 2)


def obtener_simbolo(moneda):
    """Retorna el símbolo de la moneda"""
    return SIMBOLOS.get(moneda, '$')


def formatear_precio(precio, moneda):
    """
    Formatea un precio con su símbolo de moneda.
    Ejemplo: formatear_precio(1500.50, 'MXN') → '$1,500.50 MXN'
    """
    simbolo = obtener_simbolo(moneda)
    precio_formateado = f"{float(precio):,.2f}"
    return f"{simbolo}{precio_formateado} {moneda}"