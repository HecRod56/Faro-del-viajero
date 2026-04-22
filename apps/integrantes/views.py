from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from apps.gestion_viajes.models import Viaje, Participante
from apps.autenticado.models import CustomUser
from django.contrib import messages

@login_required
def lista_integrantes(request, id_viaje, id_usuario=None):
    viaje = get_object_or_404(Viaje, id=id_viaje)
    participantes = Participante.objects.filter(viaje=viaje).select_related('usuario')

    participacion = Participante.objects.filter(
        viaje=viaje,
        usuario=request.user
    ).first()

    if not participacion:
        messages.error(request, "El viaje que intenta acceder no existe o no tiene acceso.")
        return redirect('core:home')

    es_organizador_actual = participacion.rol == 'organizador'

    # Construir la lista para el template
    integrantes = []
    for p in participantes:
        integrantes.append({
            'id':            p.usuario.id,
            'nombre':        p.usuario.username,
            'rol':           p.get_rol_display(),
            'telefono':      p.usuario.phone or '',
            'es_organizador': p.rol == 'organizador',
            'es_actual':     p.usuario == request.user,
        })

    # Cupos
    cupos_ocupados    = participantes.count()
    cupos_disponibles = viaje.capacidad_max - cupos_ocupados

    return render(request, 'integrantes/revisar_lista.html', {
        'viaje': {
            'id':               viaje.id,
            'nombre':           viaje.nombre,
            'imagen':           viaje.imagen_destino.url if viaje.imagen_destino else '',
            'estado':           viaje.get_estado_display(),
            'cupos_totales':    viaje.capacidad_max,
            'cupos_ocupados':   cupos_ocupados,
            'cupos_disponibles': cupos_disponibles,
        },
        'integrantes':          integrantes,
        'es_organizador_actual': es_organizador_actual,
        'usuario_actual_id':    request.user.id,
    })

def informacion_integrante(request, id_viaje, id_usuario):
    # 🔹 obtener viaje
    viaje = get_object_or_404(Viaje, id=id_viaje)

    # 🔹 obtener usuario
    usuario = get_object_or_404(CustomUser, id=id_usuario)

    # 🔹 obtener relación participante (usuario dentro del viaje)
    participante = get_object_or_404(
        Participante,
        viaje=viaje,
        usuario=usuario
    )

    # 🔹 verificar si es organizador en este viaje
    es_organizador = participante.rol == "organizador"

    # 🔹 viajes del usuario (para la sección "viajes compartidos")
    viajes_usuario = (
        Participante.objects
        .filter(usuario=usuario)
        .select_related("viaje")
    )

    return render(request, "integrantes/visualizar_perfil.html", {
        "usuario": usuario,
        "viaje_actual": viaje,
        "participante": participante,
        "es_organizador": es_organizador,
        "viajes": viajes_usuario,
    })

@login_required
def eliminar_integrante(request, id_integrante):
    if request.method != 'POST':
        return redirect('integrantes:lista', id_viaje=1)

    id_viaje = request.POST.get('id_viaje')

    # Solo el organizador puede eliminar
    es_organizador = Participante.objects.filter(
        viaje_id=id_viaje,
        usuario=request.user,
        rol='organizador'
    ).exists()

    if es_organizador:
        Participante.objects.filter(
            viaje_id=id_viaje,
            usuario_id=id_integrante
        ).delete()

    return redirect('integrantes:lista', id_viaje=id_viaje)


@login_required
def abandonar_viaje(request, id_viaje):
    if request.method != 'POST':
        return redirect('integrantes:lista', id_viaje=id_viaje)

    Participante.objects.filter(
        viaje_id=id_viaje,
        usuario=request.user
    ).delete()

    return redirect('gestion_viajes:lista')  # O donde listes los viajes


@login_required
def asignar_organizador(request, id_integrante):
    if request.method != 'POST':
        return redirect('integrantes:lista', id_viaje=1)

    id_viaje = request.POST.get('id_viaje')

    # Verificar que quien pide el cambio es organizador
    es_organizador = Participante.objects.filter(
        viaje_id=id_viaje,
        usuario=request.user,
        rol='organizador'
    ).exists()

    if es_organizador:
        # El nuevo organizador
        Participante.objects.filter(
            viaje_id=id_viaje,
            usuario_id=id_integrante
        ).update(rol='organizador')

        # El actual pasa a ser integrante
        Participante.objects.filter(
            viaje_id=id_viaje,
            usuario=request.user
        ).update(rol='integrante')

    return redirect('integrantes:lista', id_viaje=id_viaje)


@login_required
def anadir_integrante(request, id_viaje):
    if request.method != 'POST':
        return redirect('integrantes:lista', id_viaje=id_viaje)

    from apps.autenticado.models import CustomUser

    correo = request.POST.get('correo')
    viaje  = get_object_or_404(Viaje, id=id_viaje)

    # Verificar que hay cupos
    cupos_ocupados = Participante.objects.filter(viaje=viaje).count()
    if cupos_ocupados >= viaje.capacidad_max:
        return redirect('integrantes:lista', id_viaje=id_viaje)

    try:
        usuario = CustomUser.objects.get(email=correo)
        # Agregar solo si no está ya en el viaje
        Participante.objects.get_or_create(
            viaje=viaje,
            usuario=usuario,
            defaults={'rol': 'integrante'}
        )
    except CustomUser.DoesNotExist:
        pass  # Aquí después puedes mandar un mensaje de error al template

    return redirect('integrantes:lista', id_viaje=id_viaje)
