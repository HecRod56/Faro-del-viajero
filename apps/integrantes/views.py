from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from decimal import Decimal

from apps.gestion_viajes.models import Viaje, Participante
from apps.autenticado.models import CustomUser
from apps.control_gastos.services import (
    puede_abandonar_viaje,
    calcular_mi_billetera,
    expulsar_participante,
)
from apps.control_gastos.models import GastoParticipante


# ─── Helper ──────────────────────────────────────────────────────────────────

def _contexto_viaje_base(viaje, request):
    """Contexto compartido que necesitan varias vistas."""
    participantes_qs = Participante.objects.filter(viaje=viaje).select_related('usuario')
    cupos_ocupados   = participantes_qs.count()

    participacion = participantes_qs.filter(usuario=request.user).first()
    es_organizador = participacion.rol == 'organizador' if participacion else False

    integrantes = []
    for p in participantes_qs:
        integrantes.append({
            'id':             p.usuario.id,
            'participante_id': p.id,
            'nombre':         p.usuario.get_full_name() or p.usuario.email,
            'rol':            p.get_rol_display(),
            'telefono':       p.usuario.phone or '',
            'es_organizador': p.rol == 'organizador',
            'es_actual':      p.usuario == request.user,
        })

    return {
        'viaje': {
            'id':                viaje.id,
            'nombre':            viaje.nombre,
            'imagen':            viaje.imagen_destino.url if viaje.imagen_destino else '',
            'estado':            viaje.get_estado_display(),
            'cupos_totales':     viaje.capacidad_max,
            'cupos_ocupados':    cupos_ocupados,
            'cupos_disponibles': viaje.capacidad_max - cupos_ocupados,
        },
        'integrantes':            integrantes,
        'es_organizador_actual':  es_organizador,
        'usuario_actual_id':      request.user.id,
        'participacion_actual':   participacion,
    }


def _contexto_abandonar(viaje, participante_actual):
    """
    Calcula si el usuario puede abandonar el viaje y su situación financiera.
    Se incluye en la vista de lista para que el modal tenga los datos al abrirse.
    """
    puede, razon = puede_abandonar_viaje(participante_actual)
    billetera     = calcular_mi_billetera(viaje, participante_actual)

    return {
        'puede_abandonar':  puede,
        'razon_no_puede':   razon,
        'deudas_que_tengo': billetera['deudas_que_tengo'],
        'deudas_hacia_mi':  billetera['deudas_hacia_mi'],
    }


def _contexto_eliminar(participante_a_eliminar, participantes_restantes_count):
    """
    Calcula cuántos gastos se verían afectados si se expulsa al participante.
    Se usa para mostrar el resumen en el modal de confirmación.
    """
    gastos_qs = GastoParticipante.objects.filter(
        participante=participante_a_eliminar,
        gasto__eliminado=False,
    )

    gastos_afectados_count = gastos_qs.count()
    monto_total_afectado   = gastos_qs.aggregate(
        total=__import__('django.db.models', fromlist=['Sum']).Sum('monto_deuda')
    )['total'] or Decimal('0.00')

    return {
        'tiene_gastos_pendientes':       gastos_afectados_count > 0,
        'gastos_afectados_count':        gastos_afectados_count,
        'monto_total_afectado':          monto_total_afectado,
        'participantes_restantes_count': participantes_restantes_count,
    }


# ─── Vistas ──────────────────────────────────────────────────────────────────

@login_required
def lista_integrantes(request, id_viaje):
    viaje = get_object_or_404(Viaje, id=id_viaje)

    participacion = Participante.objects.filter(
        viaje=viaje, usuario=request.user
    ).first()

    if not participacion:
        messages.error(request, "No tienes acceso a este viaje.")
        return redirect('core:home')

    ctx = _contexto_viaje_base(viaje, request)

    # Contexto para modal "Abandonar viaje"
    ctx.update(_contexto_abandonar(viaje, participacion))

    # Contexto base para modal "Eliminar integrante"
    # Los datos específicos del integrante seleccionado se cargan
    # con data-* en el botón y se pasan al modal via JS (ver template)
    participantes_restantes_count = (
        Participante.objects.filter(viaje=viaje).count() - 1
    )
    ctx.update({
        'integrante_a_eliminar_nombre':  '',
        'integrante_a_eliminar_id':      0,
        'tiene_gastos_pendientes':       False,
        'gastos_afectados_count':        0,
        'monto_total_afectado':          Decimal('0.00'),
        'participantes_restantes_count': participantes_restantes_count,
    })

    return render(request, 'integrantes/revisar_lista.html', ctx)


@login_required
def detalle_gastos_integrante(request, id_viaje, id_participante):
    """
    Endpoint AJAX que devuelve el resumen financiero de un integrante
    para poblar el modal de "Eliminar integrante" dinámicamente.
    GET /integrantes/<id_viaje>/gastos-info/<id_participante>/
    """
    from django.http import JsonResponse

    viaje = get_object_or_404(Viaje, id=id_viaje)

    # Solo el organizador puede consultar esto
    es_organizador = Participante.objects.filter(
        viaje=viaje, usuario=request.user, rol='organizador'
    ).exists()
    if not es_organizador:
        return JsonResponse({'error': 'Sin permiso'}, status=403)

    participante = get_object_or_404(Participante, id=id_participante, viaje=viaje)

    participantes_restantes_count = (
        Participante.objects.filter(viaje=viaje).exclude(id=id_participante).count()
    )
    ctx = _contexto_eliminar(participante, participantes_restantes_count)

    return JsonResponse({
        'nombre':                    participante.usuario.get_full_name() or participante.usuario.email,
        'tiene_gastos_pendientes':   ctx['tiene_gastos_pendientes'],
        'gastos_afectados_count':    ctx['gastos_afectados_count'],
        'monto_total_afectado':      str(ctx['monto_total_afectado']),
        'participantes_restantes_count': ctx['participantes_restantes_count'],
    })


@login_required
def eliminar_integrante(request, id_integrante):
    """
    Elimina un integrante del viaje.
    Si tiene gastos activos, los redistribuye entre los restantes
    usando expulsar_participante() del service de control_gastos.
    Solo el organizador puede ejecutar esta acción.
    """
    if request.method != 'POST':
        return redirect('integrantes:lista', id_viaje=1)

    id_viaje = request.POST.get('id_viaje')
    viaje    = get_object_or_404(Viaje, id=id_viaje)

    organizador_participante = get_object_or_404(
        Participante, viaje=viaje, usuario=request.user, rol='organizador'
    )

    participante_a_eliminar = get_object_or_404(
        Participante, viaje=viaje, pk=id_integrante
    )

    # No puede eliminarse a sí mismo con esta acción
    if participante_a_eliminar.usuario == request.user:
        messages.error(request, "Usa 'Abandonar viaje' para salir tú mismo del viaje.")
        return redirect('integrantes:lista', id_viaje=id_viaje)

    try:
        expulsar_participante(
            participante_a_expulsar=participante_a_eliminar,
            organizador=organizador_participante,
            viaje=viaje,
        )
        nombre = participante_a_eliminar.usuario.get_full_name() or participante_a_eliminar.usuario.email
        messages.success(request, f"{nombre} fue eliminado del viaje y sus gastos fueron redistribuidos.")
    except PermissionError as e:
        messages.error(request, str(e))
    except ValueError as e:
        messages.error(request, str(e))
    except Exception as e:
        messages.error(request, f"Ocurrió un error al eliminar al integrante: {e}")

    return redirect('integrantes:lista', id_viaje=id_viaje)


@login_required
def abandonar_viaje(request, id_viaje):
    """
    El usuario abandona el viaje.
    Solo se permite si su balance es cero (sin deudas ni créditos pendientes).
    """
    if request.method != 'POST':
        return redirect('integrantes:lista', id_viaje=id_viaje)

    viaje        = get_object_or_404(Viaje, id=id_viaje)
    participante = get_object_or_404(Participante, viaje=viaje, usuario=request.user)

    puede, razon = puede_abandonar_viaje(participante)

    if not puede:
        messages.error(request, razon)
        return redirect('integrantes:lista', id_viaje=id_viaje)

    participante.delete()
    messages.success(request, f"Abandonaste el viaje '{viaje.nombre}' correctamente.")
    return redirect('gestion_viajes:lista')


@login_required
def asignar_organizador(request, id_integrante):
    if request.method != 'POST':
        return redirect('integrantes:lista', id_viaje=1)

    id_viaje = request.POST.get('id_viaje')

    es_organizador = Participante.objects.filter(
        viaje_id=id_viaje, usuario=request.user, rol='organizador'
    ).exists()

    if es_organizador:
        Participante.objects.filter(
            viaje_id=id_viaje, usuario_id=id_integrante
        ).update(rol='organizador')

        Participante.objects.filter(
            viaje_id=id_viaje, usuario=request.user
        ).update(rol='integrante')

    return redirect('integrantes:lista', id_viaje=id_viaje)


@login_required
def anadir_integrante(request, id_viaje):
    if request.method != 'POST':
        return redirect('integrantes:lista', id_viaje=id_viaje)

    correo = request.POST.get('correo')
    viaje  = get_object_or_404(Viaje, id=id_viaje)

    cupos_ocupados = Participante.objects.filter(viaje=viaje).count()
    if cupos_ocupados >= viaje.capacidad_max:
        messages.error(request, "El viaje ya alcanzó su capacidad máxima.")
        return redirect('integrantes:lista', id_viaje=id_viaje)

    try:
        usuario = CustomUser.objects.get(email=correo)
        _, creado = Participante.objects.get_or_create(
            viaje=viaje, usuario=usuario,
            defaults={'rol': 'integrante'}
        )
        if not creado:
            messages.warning(request, f"{usuario.get_full_name() or correo} ya es integrante del viaje.")
        else:
            messages.success(request, f"{usuario.get_full_name() or correo} fue añadido al viaje.")
    except CustomUser.DoesNotExist:
        messages.error(request, f"No existe ningún usuario registrado con el correo '{correo}'.")

    return redirect('integrantes:lista', id_viaje=id_viaje)


@login_required
def informacion_integrante(request, id_viaje, id_usuario):
    viaje       = get_object_or_404(Viaje, id=id_viaje)
    usuario     = get_object_or_404(CustomUser, id=id_usuario)
    participante = get_object_or_404(Participante, viaje=viaje, usuario=usuario)

    viajes_compartidos_ids = Participante.objects.filter(
        usuario=request.user
    ).values_list('viaje_id', flat=True)

    viajes_usuario = Participante.objects.filter(
        usuario=usuario,
        viaje_id__in=viajes_compartidos_ids,
    ).select_related('viaje')

    return render(request, 'integrantes/visualizar_perfil.html', {
        'usuario':       usuario,
        'viaje_actual':  viaje,
        'participante':  participante,
        'es_organizador': participante.rol == 'organizador',
        'viajes':        viajes_usuario,
    })