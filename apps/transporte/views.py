# apps/transporte/views.py
# ==========================================
# Vistas del módulo de transporte
# ==========================================
from datetime import datetime
from django.utils.timezone import make_aware
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse

from .servicios_cbus import buscar_autobuses_cbus
from .services import buscar_vuelos
from .models import Trayecto, TrayectoAutobus


@login_required
def transporte_principal(request):
    """
    Vista principal del dashboard de transporte (RF-70, RF-75)
    """
    from .currency import convertir_precio, formatear_precio

    moneda_usuario = request.user.currency
    costo_total = 0

    trayectos_ida = []
    trayectos_regreso = []

    # ==========================================
    # 1. Obtener y procesar VUELOS
    # ==========================================
    vuelos_ida = list(Trayecto.objects.filter(registrado_por=request.user, tipo='IDA'))
    vuelos_regreso = list(Trayecto.objects.filter(registrado_por=request.user, tipo='REGRESO'))

    for v in vuelos_ida + vuelos_regreso:
        v.es_autobus = False  # Bandera clave para el icono en el HTML
        
        precio_convertido = convertir_precio(v.precio_total, v.moneda, moneda_usuario)
        v.precio_display = formatear_precio(precio_convertido, moneda_usuario)
        costo_total += float(precio_convertido)
        
        if v.tipo == 'IDA':
            trayectos_ida.append(v)
        else:
            trayectos_regreso.append(v)

    # ==========================================
    # 2. Obtener y procesar AUTOBUSES
    # ==========================================
    buses_ida = list(TrayectoAutobus.objects.filter(registrado_por=request.user, tipo='IDA'))
    buses_regreso = list(TrayectoAutobus.objects.filter(registrado_por=request.user, tipo='REGRESO'))

    for b in buses_ida + buses_regreso:
        b.es_autobus = True   # Bandera clave para el icono en el HTML
        
        # Mapeamos los campos para que el HTML los entienda como si fueran vuelos
        b.aerolinea = b.linea_autobus
        b.numero_vuelo = b.servicio
        b.origen_codigo = b.origen_nombre
        b.destino_codigo = b.destino_nombre
        
        precio_convertido = convertir_precio(b.precio_total, b.moneda, moneda_usuario)
        b.precio_display = formatear_precio(precio_convertido, moneda_usuario)
        costo_total += float(precio_convertido)
        
        if b.tipo == 'IDA':
            trayectos_ida.append(b)
        else:
            trayectos_regreso.append(b)

    # ==========================================
    # 3. Ordenar listas por fecha y preparar contexto
    # ==========================================
    # Ordenamos ambas listas para que salgan cronológicamente mezclados (buses y aviones)
    trayectos_ida.sort(key=lambda x: x.fecha_salida)
    trayectos_regreso.sort(key=lambda x: x.fecha_salida)

    costo_total_formateado = formatear_precio(costo_total, moneda_usuario)

    context = {
        'trayectos_ida': trayectos_ida,
        'trayectos_regreso': trayectos_regreso,
        'tiene_trayectos': len(trayectos_ida) + len(trayectos_regreso) > 0,
        'costo_total': costo_total_formateado,
        'moneda_usuario': moneda_usuario,
    }
    return render(request, 'transporte/transporte_principal.html', context)


@login_required
def registrar_trayecto(request):
    """
    Vista para buscar y registrar trayectos principales (RF-70, RF-71)
    """
    context = {
        'vuelos': [],
        'busqueda_realizada': False,
    }

    if request.method == 'POST':

        # ==========================================
        # Caso 1: Confirmar y registrar un vuelo/autobús
        # ==========================================
        if 'confirmar_vuelo' in request.POST:
            modo = request.POST.get('modo_transporte', 'vuelo')
            
            try:
                # 1. Convertir fechas de string a objetos datetime con zona horaria
                dt_salida = datetime.strptime(request.POST.get('fecha_salida'), '%Y-%m-%dT%H:%M:%S')
                dt_llegada = datetime.strptime(request.POST.get('fecha_llegada'), '%Y-%m-%dT%H:%M:%S')
                
                fecha_salida_aware = make_aware(dt_salida)
                fecha_llegada_aware = make_aware(dt_llegada)

                if modo == 'vuelo':
                    Trayecto.objects.create(
                        viaje_id=request.POST.get('viaje_id', 1), # TODO: Pasar ID real
                        registrado_por=request.user,
                        tipo=request.POST.get('tipo_trayecto', 'IDA'),
                        aerolinea=request.POST.get('aerolinea', ''),
                        numero_vuelo=request.POST.get('numero_vuelo', ''),
                        origen_codigo=request.POST.get('origen_codigo', ''),
                        destino_codigo=request.POST.get('destino_codigo', ''),
                        fecha_salida=fecha_salida_aware,
                        fecha_llegada=fecha_llegada_aware,
                        duracion=request.POST.get('duracion', ''),
                        escalas=int(request.POST.get('escalas_num', 0)),
                        escalas_texto=request.POST.get('escalas_texto', 'Directo'),
                        precio_total=request.POST.get('precio_total', 0),
                        moneda=request.POST.get('moneda', 'USD'),
                        pasajeros=int(request.POST.get('pasajeros', 1)),
                        offer_id=request.POST.get('offer_id', '')
                    )
                    emoji = "✈️"
                else:
                    TrayectoAutobus.objects.create(
                        viaje_id=request.POST.get('viaje_id', 1), # TODO: Pasar ID real
                        registrado_por=request.user,
                        tipo=request.POST.get('tipo_trayecto', 'IDA'),
                        linea_autobus=request.POST.get('aerolinea', ''), 
                        servicio=request.POST.get('numero_vuelo', ''),   
                        origen_nombre=request.POST.get('origen_codigo', ''),
                        destino_nombre=request.POST.get('destino_codigo', ''),
                        fecha_salida=fecha_salida_aware,
                        fecha_llegada=fecha_llegada_aware,
                        duracion=request.POST.get('duracion', ''),
                        precio_total=request.POST.get('precio_total', 0),
                        moneda=request.POST.get('moneda', 'MXN'),
                        pasajeros=int(request.POST.get('pasajeros', 1)),
                        cbus_id=request.POST.get('offer_id', '') 
                    )
                    emoji = "🚌"

                messages.success(request, f"{emoji} Trayecto registrado correctamente en el itinerario.")
                return redirect('transporte:principal')

            except Exception as e:
                print(f"[ERROR] Error al guardar trayecto: {e}")
                messages.error(request, "⚠️ No se pudo registrar el trayecto. Verifica los datos.")

        # ==========================================
        # Caso 2: Buscar transporte (Duffel o CBus)
        # ==========================================
        else:
            modo_transporte = request.POST.get('modo_transporte', 'vuelo')
            
            origen = request.POST.get('origen', '').strip().upper()
            destino = request.POST.get('destino', '').strip().upper()
            fecha_ida = request.POST.get('fecha_ida', '')
            fecha_regreso = request.POST.get('fecha_regreso', '')
            pasajeros = int(request.POST.get('pasajeros', 1))

            resultados = []

            if modo_transporte == 'vuelo':
                resultados = buscar_vuelos(
                    origen=origen,
                    destino=destino,
                    fecha_ida=fecha_ida,
                    fecha_regreso=fecha_regreso if fecha_regreso else None,
                    pasajeros=pasajeros,
                    moneda_usuario=request.user.currency,
                )
                
            elif modo_transporte == 'autobus':
                resultados = buscar_autobuses_cbus(
                    origen_codigo=origen,
                    destino_codigo=destino,
                    fecha_ida=fecha_ida,
                    pasajeros_num=pasajeros,
                )

            context = {
                'vuelos': resultados,
                'busqueda_realizada': True,
                'total_resultados': len(resultados),
                'origen': origen,
                'destino': destino,
                'fecha_ida': fecha_ida,
                'fecha_regreso': fecha_regreso,
                'pasajeros': pasajeros,
                'moneda_usuario': request.user.currency,
                'modo_transporte': modo_transporte,
            }

    return render(request, 'transporte/registrar_trayecto.html', context)


@login_required
def buscar_ruta_interna(request):
    """Vista para buscar rutas de transporte interno (RF-72)"""
    return render(request, 'transporte/buscar_ruta_interna.html')


@login_required
def eliminar_trayecto(request, trayecto_id):
    """Eliminar un trayecto registrado (Verificando en ambas tablas)"""
    if request.method == 'POST':
        # Buscamos primero si es un vuelo
        vuelo = Trayecto.objects.filter(id=trayecto_id, registrado_por=request.user).first()
        if vuelo:
            vuelo.delete()
            messages.success(request, "✈️ Vuelo eliminado correctamente.")
        else:
            # Si no fue vuelo, buscamos en la tabla de autobuses
            autobus = TrayectoAutobus.objects.filter(id=trayecto_id, registrado_por=request.user).first()
            if autobus:
                autobus.delete()
                messages.success(request, "🚌 Autobús eliminado correctamente.")
            else:
                messages.error(request, "⚠️ No se encontró el trayecto a eliminar.")
                
    return redirect('transporte:principal')