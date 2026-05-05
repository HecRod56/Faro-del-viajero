from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from decimal import Decimal, InvalidOperation

from apps.gestion_viajes.models import Viaje, Participante
from apps.control_gastos.models import GastoParticipante, PresupuestoPersonal
from apps.control_gastos.models import Gasto
from apps.control_gastos.services import (
    crear_gasto,
    modificar_gasto,
    eliminar_gasto,
    calcular_resumen_grupal,
    calcular_mi_billetera,
    marcar_liquidacion_pagada,
)


# ─── Helper: verificar que el usuario es integrante del viaje (RNF-23) ────────

def _get_viaje_y_participante(request, viaje_id):
    """
    Devuelve (viaje, participante) si el usuario pertenece al viaje.
    Lanza Http404 si el viaje no existe o PermissionError si no es integrante.
    """
    viaje = get_object_or_404(Viaje, pk=viaje_id)
    try:
        participante = Participante.objects.get(viaje=viaje, usuario=request.user)
    except Participante.DoesNotExist:
        raise PermissionError("No tienes acceso a este viaje.")
    return viaje, participante


# ─── Vista principal: Resumen Grupal (RF-42) ──────────────────────────────────

@login_required
def resumen_grupal(request, viaje_id):
    """
    Renderiza la página principal con las pestañas:
      - Resumen grupal  (RF-42)
      - Mi Billetera    (RF-44)
      - Liquidación     (RF-43)
      - Historial       (RNF-24)
    """
    try:
        viaje, participante = _get_viaje_y_participante(request, viaje_id)
    except PermissionError:
        messages.error(request, "No tienes acceso a este viaje.")
        return redirect('inicio')

    resumen       = calcular_resumen_grupal(viaje)
    mi_billetera  = calcular_mi_billetera(viaje, participante)

    # Lista de gastos activos para el log (tabla derecha)
    gastos = (
        Gasto.objects
        .filter(viaje=viaje)          # SoftDeleteManager filtra eliminados
        .select_related('pagado_por__usuario')
        .order_by('-fecha', '-creado_en')
    )

    # Categorías disponibles para el formulario de nuevo/editar gasto
    categorias = Gasto.CATEGORIAS
    metodos    = Gasto.METODOS_DIVISION

    # Todos los participantes del viaje (para el selector "entre quiénes")
    participantes_viaje = Participante.objects.filter(viaje=viaje).select_related('usuario')

    # Historial de auditoría
    from apps.control_gastos.models import AuditoriaGasto
    historial = AuditoriaGasto.objects.filter(
        gasto_id__in=gastos.values_list('id', flat=True)
    ).select_related('realizado_por')[:50]

    context = {
        'viaje':               viaje,
        'participante':        participante,
        'resumen':             resumen,
        'mi_billetera':        mi_billetera,
        'gastos':              gastos,
        'categorias':          categorias,
        'metodos_division':    metodos,
        'participantes_viaje': participantes_viaje,
        'historial':           historial,
        'es_organizador':      participante.rol == 'organizador',
    }
    return render(request, 'control_gastos/resumen_grupal.html', context)


# ─── Crear gasto (RF-38, RF-39, RF-40) ───────────────────────────────────────

@login_required
def crear_gasto_view(request, viaje_id):
    if request.method != 'POST':
        return redirect('gastos:resumen', viaje_id=viaje_id)

    try:
        viaje, participante_actual = _get_viaje_y_participante(request, viaje_id)
    except PermissionError:
        messages.error(request, "No tienes acceso a este viaje.")
        return redirect('inicio')

    POST = request.POST

    # Validar monto (RNF-17)
    try:
        monto = Decimal(POST.get('monto', '0'))
        if monto <= 0:
            raise ValueError("El monto debe ser mayor a cero.")
    except (InvalidOperation, ValueError) as e:
        messages.error(request, f"Monto inválido: {e}")
        return redirect('gastos:resumen', viaje_id=viaje_id)

    # Validar campos obligatorios (RNF-20)
    concepto  = POST.get('concepto', '').strip()
    categoria = POST.get('categoria', '').strip()
    fecha     = POST.get('fecha', '').strip()
    metodo    = POST.get('metodo_division', 'equitativo')
    pagador_id = POST.get('pagado_por_id')

    errores = []
    if not concepto:   errores.append("La descripción es obligatoria.")
    if not categoria:  errores.append("Debes seleccionar una categoría.")
    if not fecha:      errores.append("La fecha es obligatoria.")
    if not pagador_id: errores.append("Debes indicar quién pagó.")

    if errores:
        for e in errores:
            messages.error(request, e)
        return redirect('gastos:resumen', viaje_id=viaje_id)

    try:
        pagado_por = Participante.objects.get(id=pagador_id, viaje=viaje)
    except Participante.DoesNotExist:
        messages.error(request, "El participante que pagó no pertenece a este viaje.")
        return redirect('gastos:resumen', viaje_id=viaje_id)

    # Participantes seleccionados para dividir
    ids_seleccionados = POST.getlist('participantes_ids')
    if not ids_seleccionados:
        messages.error(request, "Debes seleccionar al menos un participante para dividir el gasto.")
        return redirect('gastos:resumen', viaje_id=viaje_id)

    participantes = list(
        Participante.objects.filter(id__in=ids_seleccionados, viaje=viaje)
    )

    # Datos de división según método
    datos_division = {}
    if metodo == 'porcentaje':
        datos_division['porcentajes'] = {
            int(pid): Decimal(POST.get(f'porcentaje_{pid}', '0'))
            for pid in ids_seleccionados
        }
    elif metodo == 'monto_fijo':
        datos_division['montos_fijos'] = {
            int(pid): Decimal(POST.get(f'monto_fijo_{pid}', '0'))
            for pid in ids_seleccionados
        }

    # Crear el Gasto base
    gasto = Gasto(
        viaje=viaje,
        pagado_por=pagado_por,
        concepto=concepto,
        monto=monto,
        categoria=categoria,
        fecha=fecha,
        metodo_division=metodo,
        creado_por=request.user,
        modificado_por=request.user,
    )
    gasto.save()

    try:
        crear_gasto(
            gasto=gasto,
            participantes=participantes,
            usuario=request.user,
            datos_division=datos_division,
        )
        messages.success(request, f"Gasto '{concepto}' registrado correctamente.")
    except (ValueError, Exception) as e:
        gasto.delete()  # revertir creación del Gasto base si el service falla
        messages.error(request, str(e))

    return redirect('gastos:resumen', viaje_id=viaje_id)


# ─── Modificar gasto (RF-46) ──────────────────────────────────────────────────

@login_required
def modificar_gasto_view(request, viaje_id, gasto_id):
    if request.method != 'POST':
        return redirect('gastos:resumen', viaje_id=viaje_id)

    try:
        viaje, _ = _get_viaje_y_participante(request, viaje_id)
    except PermissionError:
        messages.error(request, "No tienes acceso a este viaje.")
        return redirect('inicio')

    gasto = get_object_or_404(Gasto, pk=gasto_id, viaje=viaje)
    POST  = request.POST

    try:
        monto = Decimal(POST.get('monto', '0'))
        if monto <= 0:
            raise ValueError("El monto debe ser mayor a cero.")
    except (InvalidOperation, ValueError) as e:
        messages.error(request, f"Monto inválido: {e}")
        return redirect('gastos:resumen', viaje_id=viaje_id)

    pagador_id = POST.get('pagado_por_id')
    try:
        pagado_por = Participante.objects.get(id=pagador_id, viaje=viaje)
    except Participante.DoesNotExist:
        messages.error(request, "El participante que pagó no pertenece a este viaje.")
        return redirect('gastos:resumen', viaje_id=viaje_id)

    ids_seleccionados = POST.getlist('participantes_ids')
    participantes = list(
        Participante.objects.filter(id__in=ids_seleccionados, viaje=viaje)
    )

    metodo = POST.get('metodo_division', 'equitativo')
    datos_division = {}
    if metodo == 'porcentaje':
        datos_division['porcentajes'] = {
            int(pid): Decimal(POST.get(f'porcentaje_{pid}', '0'))
            for pid in ids_seleccionados
        }
    elif metodo == 'monto_fijo':
        datos_division['montos_fijos'] = {
            int(pid): Decimal(POST.get(f'monto_fijo_{pid}', '0'))
            for pid in ids_seleccionados
        }

    nuevos_datos = {
        'concepto':        POST.get('concepto', gasto.concepto).strip(),
        'monto':           monto,
        'categoria':       POST.get('categoria', gasto.categoria),
        'fecha':           POST.get('fecha', str(gasto.fecha)),
        'metodo_division': metodo,
        'pagado_por':      pagado_por,
    }

    try:
        modificar_gasto(
            gasto=gasto,
            nuevos_datos=nuevos_datos,
            participantes=participantes,
            usuario=request.user,
            datos_division=datos_division,
        )
        messages.success(request, "Gasto actualizado correctamente.")
    except (ValueError, Exception) as e:
        messages.error(request, str(e))

    return redirect('gastos:resumen', viaje_id=viaje_id)


# ─── Eliminar gasto (RF-47) ───────────────────────────────────────────────────

@login_required
def eliminar_gasto_view(request, viaje_id, gasto_id):
    if request.method != 'POST':
        return redirect('gastos:resumen', viaje_id=viaje_id)

    try:
        viaje, _ = _get_viaje_y_participante(request, viaje_id)
    except PermissionError:
        messages.error(request, "No tienes acceso a este viaje.")
        return redirect('inicio')

    gasto = get_object_or_404(Gasto, pk=gasto_id, viaje=viaje)

    try:
        eliminar_gasto(gasto, usuario=request.user)
        messages.success(request, f"Gasto '{gasto.concepto}' eliminado.")
    except Exception as e:
        messages.error(request, str(e))

    return redirect('gastos:resumen', viaje_id=viaje_id)


# ─── Marcar liquidación como pagada (RF-43) ───────────────────────────────────

@login_required
def marcar_pagada_view(request, viaje_id, liquidacion_id):
    if request.method != 'POST':
        return redirect('gastos:resumen', viaje_id=viaje_id)

    try:
        viaje, _ = _get_viaje_y_participante(request, viaje_id)
    except PermissionError:
        messages.error(request, "No tienes acceso a este viaje.")
        return redirect('inicio')

    from apps.control_gastos.models import Liquidacion
    liquidacion = get_object_or_404(Liquidacion, pk=liquidacion_id, viaje=viaje)

    # NUEVO: leer monto del form; si viene vacío se paga todo
    monto_abono = None
    monto_str = request.POST.get('monto_abono', '').strip()
    if monto_str:
        try:
            from decimal import Decimal, InvalidOperation
            monto_abono = Decimal(monto_str)
        except InvalidOperation:
            messages.error(request, "Monto inválido.")
            return redirect('gastos:resumen', viaje_id=viaje_id)

    try:
        marcar_liquidacion_pagada(liquidacion, usuario=request.user, monto_abono=monto_abono)
        if liquidacion.pagado:
            messages.success(request, "Deuda saldada completamente.")
        else:
            messages.success(request, f"Abono de ${monto_abono} registrado.")
    except (PermissionError, ValueError) as e:
        messages.error(request, str(e))

    return redirect('gastos:resumen', viaje_id=viaje_id)