# apps/transporte/views.py
# ==========================================
# Vistas del módulo de transporte
# ==========================================
from datetime import datetime
from django.utils.timezone import make_aware
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from apps.gestion_viajes.models import Viaje
from .servicios_cbus import buscar_autobuses_cbus
from .services import buscar_vuelos
from .models import Trayecto, TrayectoAutobus
import io
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors


@login_required
def transporte_principal(request, viaje_id):
    """
    Vista principal del dashboard de transporte (RF-70, RF-75)
    """
    viaje = get_object_or_404(Viaje, id=viaje_id, participantes__usuario=request.user)

    from .currency import convertir_precio, formatear_precio

    moneda_usuario = request.user.currency
    costo_total = 0

    trayectos_ida = []
    trayectos_regreso = []

    
    # 1. Obtener y procesar VUELOS
    # ==========================================
    # Ya no filtramos por tipo aquí, traemos todos los del usuario
    vuelos = list(Trayecto.objects.filter(viaje_id=viaje.id, registrado_por=request.user))

    for v in vuelos:
        v.es_autobus = False  
        precio_convertido = convertir_precio(v.precio_total, v.moneda, moneda_usuario)
        v.precio_display = formatear_precio(precio_convertido, moneda_usuario)
        costo_total += float(precio_convertido)
        
        # Si es IDA o IDA_VUELTA lo ponemos en la primera lista
        if v.tipo in ['IDA', 'IDA_VUELTA']:
            trayectos_ida.append(v)
        else:
            trayectos_regreso.append(v)

    # ==========================================
    # 2. Obtener y procesar AUTOBUSES
    # ==========================================
    buses = list(TrayectoAutobus.objects.filter(viaje_id=viaje.id, registrado_por=request.user))

    for b in buses:
        b.es_autobus = True   
        b.aerolinea = b.linea_autobus
        b.numero_vuelo = b.servicio
        b.origen_codigo = b.origen_nombre
        b.destino_codigo = b.destino_nombre
        
        precio_convertido = convertir_precio(b.precio_total, b.moneda, moneda_usuario)
        b.precio_display = formatear_precio(precio_convertido, moneda_usuario)
        costo_total += float(precio_convertido)
        
        # Si es IDA o IDA_VUELTA lo ponemos en la primera lista
        if b.tipo in ['IDA', 'IDA_VUELTA']:
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
 
    # Construir concepto legible para el gasto
    origenes  = [t.origen_codigo  for t in trayectos_ida[:1]]
    destinos  = [t.destino_codigo for t in trayectos_ida[:1]]
    concepto_transporte = (
        f"Transporte — {origenes[0]} → {destinos[0]}"
        if origenes and destinos
        else "Transporte del viaje"
    )
 
    from django.utils import timezone
    context = {
        'viaje': viaje,
        'trayectos_ida': trayectos_ida,
        'trayectos_regreso': trayectos_regreso,
        'tiene_trayectos': len(trayectos_ida) + len(trayectos_regreso) > 0,
        'costo_total': costo_total_formateado,
        'costo_total_raw': round(costo_total, 2),        # ← número crudo para el form
        'concepto_transporte': concepto_transporte,       # ← descripción para el gasto
        'fecha_hoy': timezone.now().date().isoformat(),   # ← fecha por defecto
        'moneda_usuario': moneda_usuario,
    }
    
    return render(request, 'transporte/transporte_principal.html', context)


@login_required
def registrar_trayecto(request, viaje_id):
    """
    Vista para buscar y registrar trayectos principales (RF-70, RF-71)
    """
    viaje = get_object_or_404(Viaje, id=viaje_id, participantes__usuario=request.user)
    context = {
        'vuelos': [],
        'busqueda_realizada': False,
        'viaje': viaje,
    }

    if request.method == 'POST':

        # ==========================================
        # Caso 1: Confirmar y registrar un vuelo/autobús
        # ==========================================
        if 'confirmar_vuelo' in request.POST:
            modo = request.POST.get('modo_transporte', 'vuelo')
            
            try:
                dt_salida = datetime.strptime(request.POST.get('fecha_salida'), '%Y-%m-%dT%H:%M:%S')
                dt_llegada = datetime.strptime(request.POST.get('fecha_llegada'), '%Y-%m-%dT%H:%M:%S')
                
                fecha_salida_aware = make_aware(dt_salida)
                fecha_llegada_aware = make_aware(dt_llegada)

                if modo == 'vuelo':
                    Trayecto.objects.create(
                        viaje_id=viaje.id,
                        registrado_por=request.user,
                        # Usamos 'IDA_VUELTA' como salvavidas por defecto
                        tipo=request.POST.get('tipo_trayecto', 'IDA_VUELTA'), 
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
                        viaje_id=viaje.id,
                        registrado_por=request.user,
                        tipo=request.POST.get('tipo_trayecto', 'IDA_VUELTA'), 
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
                return redirect('transporte:principal', viaje_id=viaje.id)

            except Exception as e:
                print(f"[ERROR] Error al guardar trayecto: {e}")
                messages.error(request, "⚠️ No se pudo registrar el trayecto. Verifica los datos.")

        # ==========================================
        # Caso 2: Buscar transporte (Duffel o CBus)
        # ==========================================
        else:
            modo_transporte = request.POST.get('modo_transporte', 'vuelo')
            
            # ¡NUEVO! Capturar el tipo de viaje (la pestaña que seleccionó el usuario)
            tipo_viaje = request.POST.get('tipo_viaje_busqueda', 'ida_vuelta')
            
            # Traducimos la pestaña al valor exacto que espera la Base de Datos
            if tipo_viaje == 'ida_vuelta':
                tipo_trayecto_val = 'IDA_VUELTA'
            elif tipo_viaje == 'regreso':
                tipo_trayecto_val = 'REGRESO'
            else:
                tipo_trayecto_val = 'IDA'
            
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
                    moneda_usuario=request.user.currency,
                )

            context = {
                'viaje': viaje,
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
                
                'tipo_viaje': tipo_viaje,               
                'tipo_trayecto_val': tipo_trayecto_val, 
            }

    return render(request, 'transporte/registrar_trayecto.html', context)


@login_required
def buscar_ruta_interna(request, viaje_id):
    """Vista para buscar rutas de transporte interno (RF-72)"""
    # ¡AQUÍ ESTABA EL FANTASMA! Ya lo cambiamos a participantes__usuario
    viaje = get_object_or_404(Viaje, id=viaje_id, participantes__usuario=request.user)
    return render(request, 'transporte/buscar_ruta_interna.html', {'viaje': viaje})


@login_required
def eliminar_trayecto(request, viaje_id, trayecto_id): # <-- Corregido el orden: viaje_id, trayecto_id
    """Eliminar un trayecto registrado (Verificando en ambas tablas)"""
    # Validamos primero que el usuario tenga acceso a este viaje
    viaje = get_object_or_404(Viaje, id=viaje_id, participantes__usuario=request.user)
    
    if request.method == 'POST':
        # Buscamos primero si es un vuelo del viaje actual
        vuelo = Trayecto.objects.filter(id=trayecto_id, viaje_id=viaje.id, registrado_por=request.user).first()
        if vuelo:
            vuelo.delete()
            messages.success(request, "✈️ Vuelo eliminado correctamente.")
        else:
            # Si no fue vuelo, buscamos en la tabla de autobuses
            autobus = TrayectoAutobus.objects.filter(id=trayecto_id, viaje_id=viaje.id, registrado_por=request.user).first()
            if autobus:
                autobus.delete()
                messages.success(request, "🚌 Autobús eliminado correctamente.")
            else:
                messages.error(request, "⚠️ No se encontró el trayecto a eliminar.")
                
    return redirect('transporte:principal', viaje_id=viaje.id)


@login_required
def descargar_ticket(request, viaje_id, trayecto_id):
    if request.method == 'POST':
        
        # 1. BUSCADOR INTELIGENTE (¿Es vuelo o autobús?)
        es_autobus = False
        # Primero buscamos en la tabla de Vuelos
        trayecto = Trayecto.objects.filter(id=trayecto_id, viaje_id=viaje_id).first()
        
        if not trayecto:
            # Si no existe como vuelo, obligatoriamente lo buscamos como Autobús
            trayecto = get_object_or_404(TrayectoAutobus, id=trayecto_id, viaje_id=viaje_id)
            es_autobus = True

        # 2. EXTRAER LOS DATOS CORRECTOS SEGÚN EL MODELO
        if es_autobus:
            tipo_txt = "Autobús"
            operador = trayecto.linea_autobus
            numero = trayecto.servicio
            origen = trayecto.origen_nombre
            destino = trayecto.destino_nombre
        else:
            tipo_txt = "Vuelo"
            operador = trayecto.aerolinea
            numero = trayecto.numero_vuelo
            origen = trayecto.origen_codigo
            destino = trayecto.destino_codigo

        # 3. ACTUALIZAR EL ESTADO EN LA BD
        if trayecto.estado != 'CONFIRMADO':
            trayecto.estado = 'CONFIRMADO'
            trayecto.save()
            messages.success(request, f"✅ ¡Ticket descargado! El trayecto a {destino} ahora está Confirmado.")

        # 4. GENERAR EL PDF EN MEMORIA
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        
        # --- Diseño del Ticket ---
        p.setFont("Helvetica-Bold", 24)
        p.setFillColor(colors.HexColor("#0D47A1")) 
        p.drawString(50, 750, "Faro del Viajero - E-Ticket")
        
        p.setFont("Helvetica", 14)
        p.setFillColor(colors.gray)
        p.drawString(50, 725, f"Reserva de {tipo_txt} - Confirmada")

        p.line(50, 710, 550, 710)

        # Ruta
        p.setFillColor(colors.black)
        p.setFont("Helvetica-Bold", 18)
        p.drawString(50, 670, f"{origen}  ---->  {destino}")

        # Info del Pasajero y Transporte
        p.setFont("Helvetica", 12)
        nombre_pasajero = trayecto.registrado_por.get_full_name() or trayecto.registrado_por.username
        p.drawString(50, 630, f"Pasajero Titular: {nombre_pasajero}")
        p.drawString(50, 605, f"Operador: {operador}")
        p.drawString(50, 580, f"Identificador: {numero}")
        
        fecha_str = trayecto.fecha_salida.strftime("%d de %b %Y, %I:%M %p")
        p.drawString(50, 555, f"Fecha de Salida: {fecha_str}")
        
        # Costo (Usando los campos exactos de tu modelo)
        p.setFont("Helvetica-Bold", 14)
        p.setFillColor(colors.HexColor("#198754"))
        p.drawString(50, 515, f"Total Abonado: {trayecto.precio_total} {trayecto.moneda}")

        # Pie de página
        p.setFont("Helvetica-Oblique", 10)
        p.setFillColor(colors.gray)
        p.drawString(50, 100, "Este es un documento generado automáticamente por Faro del Viajero.")

        p.showPage()
        p.save()
        buffer.seek(0)

        # 5. ENVIAR EL ARCHIVO AL NAVEGADOR
        response = HttpResponse(buffer, content_type='application/pdf')
        nombre_archivo = f"Ticket_{operador}_{numero}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
        
        return response

    return redirect('transporte:principal', viaje_id=viaje_id)