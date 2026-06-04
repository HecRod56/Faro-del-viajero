# apps/control_gastos/services.py

from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction, models
from django.utils import timezone

from .models import GastoParticipante, Liquidacion, AuditoriaGasto


# ═══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 1 — HELPERS INTERNOS
# ═══════════════════════════════════════════════════════════════════════════════

CENTAVO = Decimal('0.01')

def _nombre_usuario(user):
    return (
        user.get_full_name()
        or user.get_short_name()
        or user.username
    )

def _redondear(valor: Decimal) -> Decimal:
    return valor.quantize(CENTAVO, rounding=ROUND_HALF_UP)


def _snapshot(gasto) -> dict:
    """
    Serializa el estado actual de un gasto a dict para auditoría.
    Se llama ANTES de modificar y DESPUÉS para guardar el par antes/después.
    """
    return {
        'concepto':         gasto.concepto,
        'monto':            str(gasto.monto),
        'categoria':        gasto.categoria,
        'fecha':            str(gasto.fecha),
        'metodo_division':  gasto.metodo_division,
        'pagado_por_id':    gasto.pagado_por_id,
        'pagado_por':       str(gasto.pagado_por) if gasto.pagado_por else None,
    }


def _registrar_auditoria(gasto_id: int, accion: str, usuario, antes=None, despues=None):
    AuditoriaGasto.objects.create(
        gasto_id=gasto_id,
        accion=accion,
        realizado_por=usuario,
        detalle_antes=antes,
        detalle_despues=despues,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 2 — DIVISIÓN DEL MONTO (RF-40, RNF-19)
# ═══════════════════════════════════════════════════════════════════════════════

def _dividir_equitativo(monto: Decimal, participantes: list) -> list[Decimal]:
    """
    Divide el monto en partes iguales.
    El centavo excedente va al primer participante (RNF-19).

    Ejemplo: $100 entre 3 → [33.34, 33.33, 33.33]
    """
    n = len(participantes)
    parte = _redondear(monto / n)
    partes = [parte] * n

    # Ajuste de centavos: la suma puede diferir por redondeo
    residuo = monto - sum(partes)
    partes[0] += residuo  # siempre se lo lleva el primero (RNF-19)

    return partes


def _dividir_por_porcentaje(monto: Decimal, participantes: list, porcentajes: dict) -> list[Decimal]:
    """
    Divide según porcentajes indicados por participante.
    porcentajes = {participante_id: Decimal('porcentaje')}

    Valida que los porcentajes sumen 100 antes de llamar esta función.
    El centavo excedente va al primer participante (RNF-19).

    Ejemplo: $200, [60%, 40%] → [120.00, 80.00]
    """
    partes = []
    for p in participantes:
        pct = porcentajes.get(p.id, Decimal('0'))
        partes.append(_redondear(monto * pct / Decimal('100')))

    residuo = monto - sum(partes)
    partes[0] += residuo

    return partes


def _dividir_por_monto_fijo(monto: Decimal, participantes: list, montos_fijos: dict) -> list[Decimal]:
    """
    Usa montos específicos indicados por participante.
    montos_fijos = {participante_id: Decimal('monto')}

    Valida que la suma coincida con el monto total antes de llamar esta función.
    """
    return [
        _redondear(montos_fijos.get(p.id, Decimal('0')))
        for p in participantes
    ]


def _calcular_deudas(gasto, participantes: list, datos_division: dict) -> list[dict]:
    """
    Orquesta el método de división correcto y devuelve una lista de dicts:
    [{'participante': obj, 'monto_pagado': Decimal, 'monto_deuda': Decimal, 'porcentaje': Decimal|None}]
    """
    monto = gasto.monto
    metodo = gasto.metodo_division

    if metodo == 'equitativo':
        partes = _dividir_equitativo(monto, participantes)
        porcentajes_guardados = [None] * len(participantes)

    elif metodo == 'porcentaje':
        porcentajes_input = datos_division.get('porcentajes', {})
        partes = _dividir_por_porcentaje(monto, participantes, porcentajes_input)
        porcentajes_guardados = [
            porcentajes_input.get(p.id, Decimal('0'))
            for p in participantes
        ]

    elif metodo == 'monto_fijo':
        montos_fijos = datos_division.get('montos_fijos', {})
        partes = _dividir_por_monto_fijo(monto, participantes, montos_fijos)
        porcentajes_guardados = [None] * len(participantes)

    else:
        raise ValueError(f"Método de división no reconocido: '{metodo}'")

    resultado = []
    for i, participante in enumerate(participantes):
        es_pagador = (gasto.pagado_por_id == participante.id)
        resultado.append({
            'participante':  participante,
            'monto_pagado':  monto if es_pagador else Decimal('0.0000'),
            'monto_deuda':   partes[i],
            'porcentaje':    porcentajes_guardados[i],
        })

    return resultado


# ═══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 3 — RECÁLCULO DE LIQUIDACIONES (RF-41, RNF-16, RNF-21)
# ═══════════════════════════════════════════════════════════════════════════════

def _calcular_balances(viaje) -> dict:
    """
    Suma todos los GastoParticipante activos del viaje y devuelve el balance
    neto de cada participante.

    Retorna: {participante_id: {'usuario': str, 'balance': Decimal}}
    """
    participaciones = (
        GastoParticipante.objects
        .filter(gasto__viaje=viaje, gasto__eliminado=False)
        .select_related('participante__usuario')
    )

    balances = {}
    for gp in participaciones:
        pid = gp.participante_id
        if pid not in balances:
            balances[pid] = {
                'usuario':      str(gp.participante.usuario),
                'participante': gp.participante,
                'balance':      Decimal('0.00'),
            }
        balances[pid]['balance'] += gp.balance  # property del modelo

    return balances


def _recalcular_liquidaciones(viaje):
    """
    Algoritmo greedy para minimizar el número de transferencias necesarias.
    Borra las liquidaciones pendientes anteriores y escribe las nuevas.
    Las liquidaciones ya marcadas como 'pagado' NO se tocan (RF-43).

    Complejidad: O(n log n) donde n = número de participantes.
    """
    balances = _calcular_balances(viaje)

    # Separar en deudores (balance < 0) y acreedores (balance > 0)
    deudores = sorted(
        [(pid, data) for pid, data in balances.items() if data['balance'] < 0],
        key=lambda x: x[1]['balance']           # más negativo primero
    )
    acreedores = sorted(
        [(pid, data) for pid, data in balances.items() if data['balance'] > 0],
        key=lambda x: x[1]['balance'],
        reverse=True                             # más positivo primero
    )

    nuevas_liquidaciones = []
    i, j = 0, 0

    while i < len(deudores) and j < len(acreedores):
        pid_d, deudor   = deudores[i]
        pid_a, acreedor = acreedores[j]

        monto = min(-deudor['balance'], acreedor['balance'])
        monto = _redondear(monto)

        if monto > 0:
            nuevas_liquidaciones.append({
                'deudor':   deudor['participante'],
                'acreedor': acreedor['participante'],
                'monto':    monto,
            })

        deudor['balance']   += monto
        acreedor['balance'] -= monto

        if abs(deudor['balance'])   < CENTAVO: i += 1
        if abs(acreedor['balance']) < CENTAVO: j += 1

    # Borrar solo las pendientes (no tocar las ya pagadas)
    Liquidacion.objects.filter(viaje=viaje, pagado=False).delete()

    # Insertar las nuevas en bloque
    Liquidacion.objects.bulk_create([
        Liquidacion(
            viaje=viaje,
            deudor=liq['deudor'],
            acreedor=liq['acreedor'],
            monto=liq['monto'],
        )
        for liq in nuevas_liquidaciones
    ])


# ═══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 4 — API PÚBLICA (lo que llaman las vistas)
# ═══════════════════════════════════════════════════════════════════════════════

@transaction.atomic
def crear_gasto(gasto, participantes: list, usuario, datos_division: dict = None):
    """
    Registra un gasto nuevo con su división entre participantes y
    recalcula las liquidaciones del viaje.

    Parámetros:
        gasto           — instancia de Gasto ya guardada en BD
        participantes   — lista de instancias de Participante
        usuario         — request.user (para auditoría)
        datos_division  — dict con claves según el método:
                            equitativo  → {} (o None)
                            porcentaje  → {'porcentajes': {pid: Decimal}}
                            monto_fijo  → {'montos_fijos': {pid: Decimal}}

    Lanza ValueError si:
        - No hay participantes
        - Los porcentajes no suman 100
        - Los montos fijos no coinciden con el total
    """
    if not participantes:
        raise ValueError("Debe haber al menos un participante.")

    datos_division = datos_division or {}
    _validar_division(gasto, participantes, datos_division)

    deudas = _calcular_deudas(gasto, participantes, datos_division)

    GastoParticipante.objects.bulk_create([
        GastoParticipante(
            gasto=gasto,
            participante=d['participante'],
            monto_pagado=d['monto_pagado'],
            monto_deuda=d['monto_deuda'],
            porcentaje=d['porcentaje'],
            creado_por=usuario,
            modificado_por=usuario,
        )
        for d in deudas
    ])

    _recalcular_liquidaciones(gasto.viaje)

    _registrar_auditoria(
        gasto_id=gasto.id,
        accion='creado',
        usuario=usuario,
        antes=None,
        despues=_snapshot(gasto),
    )


@transaction.atomic
def modificar_gasto(gasto, nuevos_datos: dict, participantes: list, usuario, datos_division: dict = None):
    """
    Modifica los campos de un gasto, recalcula su división y
    actualiza las liquidaciones del viaje.

    nuevos_datos — dict con los campos a actualizar, p. ej.:
        {'concepto': 'Cena', 'monto': Decimal('450.00'), 'categoria': 'alimentacion'}
    """
    if not participantes:
        raise ValueError("Debe haber al menos un participante.")

    datos_division = datos_division or {}
    snapshot_antes = _snapshot(gasto)

    # Actualizar campos del gasto
    campos_permitidos = {'concepto', 'monto', 'categoria', 'fecha', 'metodo_division', 'pagado_por'}
    for campo, valor in nuevos_datos.items():
        if campo in campos_permitidos:
            setattr(gasto, campo, valor)
    gasto.modificado_por = usuario
    gasto.save()

    _validar_division(gasto, participantes, datos_division)

    GastoParticipante.objects.filter(gasto=gasto).delete()


    deudas = _calcular_deudas(gasto, participantes, datos_division)

    GastoParticipante.objects.bulk_create([
        GastoParticipante(
            gasto=gasto,
            participante=d['participante'],
            monto_pagado=d['monto_pagado'],
            monto_deuda=d['monto_deuda'],
            porcentaje=d['porcentaje'],
            creado_por=usuario,
            modificado_por=usuario,
        )
        for d in deudas
    ])

    _recalcular_liquidaciones(gasto.viaje)

    _registrar_auditoria(
        gasto_id=gasto.id,
        accion='modificado',
        usuario=usuario,
        antes=snapshot_antes,
        despues=_snapshot(gasto),
    )


@transaction.atomic
def eliminar_gasto(gasto, usuario):
    """
    Soft-delete de un gasto y todas sus participaciones.
    Recalcula liquidaciones automáticamente (RF-47, RNF-21).
    """
    snapshot_antes = _snapshot(gasto)

    for gp in GastoParticipante.objects.filter(gasto=gasto):
        gp.delete(usuario=usuario)

    gasto.delete(usuario=usuario)

    _recalcular_liquidaciones(gasto.viaje)

    _registrar_auditoria(
        gasto_id=gasto.id,
        accion='eliminado',
        usuario=usuario,
        antes=snapshot_antes,
        despues=None,
    )


def calcular_resumen_grupal(viaje) -> dict:
    """
    Datos para la vista de Resumen Grupal (RF-42).

    Retorna:
    {
        'presupuesto_total':    Decimal,
        'total_gastado':        Decimal,
        'saldo_disponible':     Decimal,
        'porcentaje_uso':       Decimal,   # 0-100
        'aportaciones':         [
            {
                'participante': str,
                'total_pagado': Decimal,   # lo que puso de su bolsillo
                'total_deuda':  Decimal,   # lo que le corresponde pagar
                'balance':      Decimal,   # positivo = le deben, negativo = debe
            }
        ],
        'liquidaciones_pendientes': [
            {'de': str, 'a': str, 'monto': Decimal}
        ],
    }
    """
    presupuesto = viaje.presupuesto_estimado or Decimal('0.00')

    participaciones = (
        GastoParticipante.objects
        .filter(gasto__viaje=viaje, gasto__eliminado=False)
        .select_related('participante__usuario')
    )

    aportaciones = {}
    total_gastado = Decimal('0.00')

    for gp in participaciones:
        pid = gp.participante_id

        user = gp.participante.usuario

        nombre = (
            user.get_full_name()
            or user.get_short_name()
            or user.username
        )

        if pid not in aportaciones:
            aportaciones[pid] = {
                #'participante': gp.participante.usuario,
                'participante': nombre,
                'total_pagado': Decimal('0.00'),
                'total_deuda':  Decimal('0.00'),
            }
        aportaciones[pid]['total_pagado'] += gp.monto_pagado
        aportaciones[pid]['total_deuda']  += gp.monto_deuda
        total_gastado += gp.monto_deuda   # cada deuda suma una vez al total

    # Evitar doble conteo: total_gastado = suma de monto_deuda / participantes
    # pero la deuda de cada uno ya suma el monto completo entre todos,
    # así que dividimos por el promedio implícito usando un gasto por viaje.
    # Más simple: sumamos monto de cada Gasto directamente.
    from apps.control_gastos.models import Gasto as GastoModel
    total_gastado = (
        GastoModel.objects
        .filter(viaje=viaje)       # SoftDeleteManager filtra eliminados
        .aggregate(total=models.Sum('monto'))['total']
        or Decimal('0.00')
    )

    saldo = presupuesto - total_gastado
    porcentaje = (
        _redondear(total_gastado / presupuesto * 100)
        if presupuesto > 0 else Decimal('0.00')
    )

    lista_aportaciones = []
    for data in aportaciones.values():
        balance = _redondear(data['total_pagado'] - data['total_deuda'])
        lista_aportaciones.append({
            'participante': data['participante'],
            'total_pagado': _redondear(data['total_pagado']),
            'total_deuda':  _redondear(data['total_deuda']),
            'balance':      balance,
        })

    liquidaciones = Liquidacion.objects.filter(viaje=viaje, pagado=False).select_related(
        'deudor__usuario', 'acreedor__usuario'
    )

    return {
        'presupuesto_total':        presupuesto,
        'total_gastado':            total_gastado,
        'saldo_disponible':         saldo,
        'porcentaje_uso':           porcentaje,
        'aportaciones':             lista_aportaciones,
        'liquidaciones_pendientes': [
            {
                'id':    liq.id,
                'de':    _nombre_usuario(liq.deudor.usuario),
                'a':     _nombre_usuario(liq.acreedor.usuario),
                'monto': liq.monto,
                'monto_pagado':    liq.monto_pagado,       # NUEVO
                'monto_pendiente': liq.monto_pendiente, 
            }
            for liq in liquidaciones
        ],
    }


def calcular_mi_billetera(viaje, participante) -> dict:
    """
    Datos para la vista personal Mi Billetera (RF-44).

    Retorna:
    {
        'presupuesto_personal': Decimal | None,
        'total_gastado_personal': Decimal,   # lo que le corresponde pagar
        'saldo_personal': Decimal | None,
        'deudas_que_tengo': [...],            # yo le debo a alguien
        'deudas_hacia_mi': [...],             # alguien me debe a mí
    }
    """
    from apps.control_gastos.models import PresupuestoPersonal

    try:
        pp = PresupuestoPersonal.objects.get(viaje=viaje, participante=participante)
        presupuesto_personal = pp.monto
    except PresupuestoPersonal.DoesNotExist:
        presupuesto_personal = None

    total_deuda_personal = (
        GastoParticipante.objects
        .filter(gasto__viaje=viaje, participante=participante, gasto__eliminado=False)
        .aggregate(total=models.Sum('monto_deuda'))['total']
        or Decimal('0.00')
    )

    saldo_personal = (
        _redondear(presupuesto_personal - total_deuda_personal)
        if presupuesto_personal is not None else None
    )

    deudas_que_tengo = Liquidacion.objects.filter(
        viaje=viaje, deudor=participante, pagado=False
    ).select_related('acreedor__usuario')

    deudas_hacia_mi = Liquidacion.objects.filter(
        viaje=viaje, acreedor=participante, pagado=False
    ).select_related('deudor__usuario')

    return {
        'presupuesto_personal':   presupuesto_personal,
        'total_gastado_personal': _redondear(total_deuda_personal),
        'saldo_personal':         saldo_personal,
        'deudas_que_tengo': [
    {
        'a':               _nombre_usuario(liq.acreedor.usuario),
        'monto':           liq.monto,
        'monto_pagado':    liq.monto_pagado,       # NUEVO
        'monto_pendiente': liq.monto_pendiente,    # NUEVO
    }
    for liq in deudas_que_tengo
],
'deudas_hacia_mi': [
    {
        'de':              _nombre_usuario(liq.deudor.usuario),
        'monto':           liq.monto,
        'monto_pagado':    liq.monto_pagado,       # NUEVO
        'monto_pendiente': liq.monto_pendiente,    # NUEVO
    }
    for liq in deudas_hacia_mi
],
    }


@transaction.atomic
def marcar_liquidacion_pagada(liquidacion, usuario, monto_abono=None):
    """
    El acreedor puede abonar parcial o totalmente una deuda (RF-43).
    Si monto_abono es None, paga el total pendiente.
    """
    if liquidacion.acreedor.usuario != usuario:
        raise PermissionError("Solo el acreedor puede marcar esta deuda como pagada.")

    if monto_abono is None:
        # Pago total: comportamiento anterior
        monto_abono = liquidacion.monto_pendiente

    liquidacion.abonar(monto_abono)


# ═══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 5 — VALIDACIONES (RNF-17, RNF-20)
# ═══════════════════════════════════════════════════════════════════════════════

def _validar_division(gasto, participantes: list, datos_division: dict):
    """
    Valida la coherencia de los datos de división antes de ejecutar cualquier
    operación de escritura. Lanza ValueError con mensajes claros (RNF-20).
    """
    metodo = gasto.metodo_division

    if metodo == 'porcentaje':
        porcentajes = datos_division.get('porcentajes', {})
        if not porcentajes:
            raise ValueError("Debes indicar el porcentaje de cada participante.")

        suma = sum(porcentajes.get(p.id, Decimal('0')) for p in participantes)
        if abs(suma - Decimal('100')) > Decimal('0.01'):
            raise ValueError(
                f"Los porcentajes deben sumar 100%. Suma actual: {suma}%."
            )

    elif metodo == 'monto_fijo':
        montos_fijos = datos_division.get('montos_fijos', {})
        if not montos_fijos:
            raise ValueError("Debes indicar el monto fijo de cada participante.")

        suma = sum(montos_fijos.get(p.id, Decimal('0')) for p in participantes)
        if abs(suma - gasto.monto) > CENTAVO:
            raise ValueError(
                f"La suma de montos fijos (${suma}) no coincide con el total del gasto (${gasto.monto})."
            )
        
# ═══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 6 — VALIDACIONES PARA EXPULSIÓN DE PARTICIPANTE
# ═══════════════════════════════════════════════════════════════════════════════

def puede_abandonar_viaje(participante) -> tuple[bool, str]:
    """
    Verifica si un participante puede abandonar el viaje.
    Retorna (puede: bool, razon: str)
    """
    from decimal import Decimal
    balances = _calcular_balances(participante.viaje)
    data = balances.get(participante.id)

    if data is None:
        return True, ""  # nunca tuvo gastos, puede salir

    balance = data['balance']

    if balance > Decimal('0.01'):
        return False, (
            f"Tienes un saldo a favor de ${balance:.2f}. "
            "Debes cobrar lo que te deben antes de salir."
        )
    if balance < Decimal('-0.01'):
        return False, (
            f"Tienes una deuda pendiente de ${abs(balance):.2f}. "
            "Debes liquidarla antes de salir."
        )

    return True, ""

@transaction.atomic
def abandonar_participante(participante):
    """
    El usuario abandona el viaje.
    Si su balance es cero, sus participaciones en gastos se eliminan y se
    reasignan los pagos necesarios para permitir borrar el participante.
    """
    from apps.gestion_viajes.models import Participante as ParticipanteModel

    viaje = participante.viaje
    participantes_restantes = list(
        ParticipanteModel.objects.filter(viaje=viaje)
        .exclude(id=participante.id)
    )

    if not participantes_restantes:
        raise ValueError("No puedes abandonar el último integrante del viaje.")

    organizador = ParticipanteModel.objects.filter(
        viaje=viaje, rol='organizador'
    ).exclude(id=participante.id).first() or participantes_restantes[0]

    gastos_afectados = GastoParticipante.objects.filter(
        participante=participante,
        gasto__eliminado=False,
    ).select_related('gasto')

    for gp in gastos_afectados:
        gasto = gp.gasto
        monto_a_repartir = gp.monto_deuda

        if gasto.pagado_por == participante:
            gasto.pagado_por = organizador
            gasto.save(update_fields=['pagado_por'])

        otros_gps = GastoParticipante.objects.filter(
            gasto=gasto,
            eliminado=False,
        ).exclude(participante=participante)

        if otros_gps.exists():
            n = otros_gps.count()
            parte = _redondear(monto_a_repartir / n)
            residuo = monto_a_repartir - (parte * n)

            for i, otro_gp in enumerate(otros_gps):
                otro_gp.monto_deuda += parte + (residuo if i == 0 else Decimal('0'))
                otro_gp.save(update_fields=['monto_deuda'])

        gp.delete(usuario=participante.usuario)

    GastoParticipante.todos.filter(participante=participante).delete()
    _recalcular_liquidaciones(viaje)
    _registrar_auditoria(
        gasto_id=0,
        accion='abandonado',
        usuario=participante.usuario,
        antes={'participante_abandonado': str(participante.usuario)},
        despues={'participantes_restantes': [str(p.usuario) for p in participantes_restantes]},
    )

    participante.delete()

@transaction.atomic
def expulsar_participante(participante_a_expulsar, organizador, viaje):
    """
    El organizador elimina a un integrante del viaje.
    Sus gastos como pagador quedan registrados (pagado_por → NULL via SET_NULL).
    Sus participaciones se redistribuyen equitativamente entre los restantes.
    """
    from apps.gestion_viajes.models import Participante

    # Verificar que quien ejecuta es organizador
    if organizador.rol != 'organizador':
        raise PermissionError("Solo el organizador puede expulsar integrantes.")

    participantes_restantes = list(
        Participante.objects.filter(viaje=viaje)
        .exclude(id=participante_a_expulsar.id)
    )

    if not participantes_restantes:
        raise ValueError("No puedes expulsar al último integrante del viaje.")

    # Reasignar cada GastoParticipante donde aparece el expulsado
    gastos_afectados = GastoParticipante.objects.filter(
        participante=participante_a_expulsar,
        gasto__eliminado=False,
    ).select_related('gasto')

    for gp in gastos_afectados:
        gasto = gp.gasto
        monto_a_repartir = gp.monto_deuda

        # Si además era el pagador, ese crédito pasa al organizador
        if gasto.pagado_por == participante_a_expulsar:
            gasto.pagado_por = organizador
            gasto.save(update_fields=['pagado_por'])

        # Distribuir su deuda entre los restantes que ya están en el gasto
        otros_gps = GastoParticipante.objects.filter(
            gasto=gasto,
            eliminado=False,
        ).exclude(participante=participante_a_expulsar)

        if otros_gps.exists():
            # Repartir equitativamente entre los que ya participan
            n = otros_gps.count()
            parte = _redondear(monto_a_repartir / n)
            residuo = monto_a_repartir - (parte * n)

            for i, otro_gp in enumerate(otros_gps):
                otro_gp.monto_deuda += parte + (residuo if i == 0 else Decimal('0'))
                otro_gp.save(update_fields=['monto_deuda'])

        # Soft-delete de la participación del expulsado
        gp.delete(usuario=organizador.usuario)

    # Eliminar físicamente cualquier participación residual del expulsado para
    # no bloquear la eliminación del Participante por la FK RESTRICT.
    GastoParticipante.todos.filter(participante=participante_a_expulsar).delete()

    # Recalcular liquidaciones con la nueva distribución
    _recalcular_liquidaciones(viaje)

    # Registrar en auditoría
    _registrar_auditoria(
        gasto_id=0,  # 0 indica operación a nivel viaje, no gasto específico
        accion='eliminado',
        usuario=organizador.usuario,
        antes={'participante_expulsado': str(participante_a_expulsar.usuario)},
        despues={'redistribuido_entre': [str(p.usuario) for p in participantes_restantes]},
    )

    # Finalmente eliminar el Participante
    participante_a_expulsar.delete()