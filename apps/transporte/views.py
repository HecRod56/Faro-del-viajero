# apps/transporte/views.py
# ==========================================
# Vistas del módulo de transporte
# ==========================================

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse

from .services import buscar_vuelos
from .models import Trayecto


@login_required
def transporte_principal(request):
    """
    Vista principal del dashboard de transporte (RF-70, RF-75)
    """
    from .currency import convertir_precio, formatear_precio

    moneda_usuario = request.user.currency
    costo_total = 0

    # ==========================================
    # Obtener trayectos y convertir precios
    # ==========================================
    trayectos_ida = list(Trayecto.objects.filter(registrado_por=request.user, tipo='IDA'))
    trayectos_regreso = list(Trayecto.objects.filter(registrado_por=request.user, tipo='REGRESO'))

    # Asignar precio convertido a cada trayecto
    for trayecto in trayectos_ida + trayectos_regreso:
        precio_convertido = convertir_precio(
            trayecto.precio_total,
            trayecto.moneda,
            moneda_usuario
        )
        trayecto.precio_display = formatear_precio(precio_convertido, moneda_usuario)
        costo_total += precio_convertido

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
    
    GET: Muestra el formulario de búsqueda
    POST: Consulta la API de Duffel y retorna los resultados
    """
    context = {
        'vuelos': [],
        'busqueda_realizada': False,
    }

    if request.method == 'POST':

        # ==========================================
        # Caso 1: Confirmar y registrar un vuelo
        # ==========================================
        if 'confirmar_vuelo' in request.POST:
            try:
                trayecto = Trayecto(
                    viaje_id=request.POST.get('viaje_id', 1),  # TODO: pasar viaje real
                    registrado_por=request.user,
                    tipo=request.POST.get('tipo_trayecto', 'IDA'),
                    aerolinea=request.POST.get('aerolinea', ''),
                    numero_vuelo=request.POST.get('numero_vuelo', ''),
                    origen_codigo=request.POST.get('origen_codigo', ''),
                    destino_codigo=request.POST.get('destino_codigo', ''),
                    fecha_salida=request.POST.get('fecha_salida', ''),
                    fecha_llegada=request.POST.get('fecha_llegada', ''),
                    duracion=request.POST.get('duracion', ''),
                    escalas=int(request.POST.get('escalas_num', 0)),
                    escalas_texto=request.POST.get('escalas_texto', 'Directo'),
                    precio_total=request.POST.get('precio_total', 0),
                    moneda=request.POST.get('moneda', 'USD'),
                    pasajeros=int(request.POST.get('pasajeros', 1)),
                    offer_id=request.POST.get('offer_id', ''),
                )
                trayecto.save()
                messages.success(request, f"✈️ Trayecto {trayecto.origen_codigo} → {trayecto.destino_codigo} registrado correctamente.")
                return redirect('transporte:principal')

            except Exception as e:
                print(f"[ERROR] No se pudo guardar el trayecto: {e}")
                messages.error(request, "⚠️ Error al registrar el trayecto. Inténtalo de nuevo.")

        # ==========================================
        # Caso 2: Buscar vuelos con Duffel
        # ==========================================
        else:
            origen = request.POST.get('origen', '').strip().upper()
            destino = request.POST.get('destino', '').strip().upper()
            fecha_ida = request.POST.get('fecha_ida', '')
            fecha_regreso = request.POST.get('fecha_regreso', '')
            pasajeros = int(request.POST.get('pasajeros', 1))

            vuelos = buscar_vuelos(
                origen=origen,
                destino=destino,
                fecha_ida=fecha_ida,
                fecha_regreso=fecha_regreso if fecha_regreso else None,
                pasajeros=pasajeros,
                moneda_usuario=request.user.currency, 
            )

            context = {
                'vuelos': vuelos,
                'busqueda_realizada': True,
                'total_resultados': len(vuelos),
                'origen': origen,
                'destino': destino,
                'fecha_ida': fecha_ida,
                'fecha_regreso': fecha_regreso,
                'pasajeros': pasajeros,
                'moneda_usuario': request.user.currency,
                
            }

    return render(request, 'transporte/registrar_trayecto.html', context)


@login_required
def buscar_ruta_interna(request):
    """Vista para buscar rutas de transporte interno (RF-72)"""
    return render(request, 'transporte/buscar_ruta_interna.html')

@login_required
def eliminar_trayecto(request, trayecto_id):
    """Eliminar un trayecto registrado"""
    trayecto = Trayecto.objects.get(id=trayecto_id, registrado_por=request.user)
    if request.method == 'POST':
        trayecto.delete()
        messages.success(request, "🗑️ Trayecto eliminado correctamente.")
    return redirect('transporte:principal')