from django.shortcuts import render, redirect
from .models import Viaje, Gasto, Participante
from django.shortcuts import render, get_object_or_404
from django.db.models import Sum
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .mixins import ViajeContextMixin
from django.views.generic import DetailView
from datetime import date  # ← nuevo import
import json

# ==========================================
# FUNCIÓN AUXILIAR: Actualizar estado automáticamente
# ==========================================
def actualizar_estado_viaje(viaje):
    hoy = date.today()
    if viaje.fecha_inicio <= hoy <= viaje.fecha_fin:
        nuevo_estado = 'en curso'
    elif hoy > viaje.fecha_fin:
        nuevo_estado = 'finalizado'
    else:
        return  # Es planeado, no cambia

    if viaje.estado != nuevo_estado:
        viaje.estado = nuevo_estado
        viaje.save()

# 1. Página de inicio del módulo
def pagina_inicio(request):
    return render(request, 'gestion_viajes/inicio.html')

# 2. Lógica para mostrar Y GUARDAR el viaje
def pagina_crear_viaje(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        destino = request.POST.get('destino')
        descripcion = request.POST.get('descripcion')
        fecha_inicio = request.POST.get('fecha_inicio')
        fecha_fin = request.POST.get('fecha_fin')
        capacidad = request.POST.get('capacidad_max')
        presupuesto = request.POST.get('presupuesto_estimado')

        nuevo_viaje = Viaje.objects.create(
            nombre=nombre,
            destino=destino,
            descripcion=descripcion,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            capacidad_max=capacidad if capacidad else 2,
            presupuesto_estimado=presupuesto if presupuesto else 0
        )

        user_actual = request.user
        if not user_actual.is_authenticated:
            User = get_user_model()
            user_actual = User.objects.first()

        if user_actual:
            Participante.objects.create(
                viaje=nuevo_viaje,
                usuario=user_actual,
                rol='organizador'
            )

        return redirect('gestion_viajes:p_ver_mis_viajes')

    return render(request, 'gestion_viajes/crear_viaje.html')

# 3. Vista para ver todos los viajes registrados
def pagina_ver_mis_viajes(request):
    user_actual = request.user

    if not user_actual.is_authenticated:
        User = get_user_model()
        user_actual = User.objects.first()

    viajes_db = Viaje.objects.filter(participantes__usuario=user_actual).distinct()

    # ← Actualizar estado de cada viaje antes de mostrarlos
    for viaje in viajes_db:
        actualizar_estado_viaje(viaje)

    estado_filtro = request.GET.get('estado')

    if estado_filtro:
        viajes_db = viajes_db.filter(estado=estado_filtro)

    return render(request, 'gestion_viajes/ver_mis_viajes.html', {
        'viajes': viajes_db,
        'filtro_actual': estado_filtro
    })

# 4. Vista para ver solo los viajes con estado 'planeado'
def pagina_viajes_planeados(request):
    viajes_p = Viaje.objects.filter(estado='planeado')
    return render(request, 'gestion_viajes/viajes_planeados.html', {'viajes': viajes_p})

# 5. Vista para mostrar el detalle de un viaje específico
def pagina_detalle_viaje(request, viaje_id):
    from apps.control_gastos.models import Gasto as GastoControl

    # 1. Obtenemos el viaje o lanzamos 404
    viaje = get_object_or_404(Viaje, id=viaje_id)

    # ← Actualizar estado antes de cualquier lógica
    actualizar_estado_viaje(viaje)

    if request.user.is_authenticated:
        participante_actual = Participante.objects.filter(viaje=viaje, usuario=request.user).first()

        if not participante_actual:
            from django.contrib import messages
            messages.error(request, "Acceso denegado: No eres integrante de este viaje.")
            return redirect('gestion_viajes:p_ver_mis_viajes')

        es_participante = True
        rol_usuario = participante_actual.rol
    else:
        return redirect('login')

    participantes_list = viaje.participantes.all()
    organizador = participantes_list.filter(rol='organizador').first()

    total_gastado = viaje.gastos.aggregate(total=Sum('cantidad'))['total'] or 0
    presupuesto_restante = (viaje.presupuesto_estimado or 0) - total_gastado

    if viaje.presupuesto_estimado and viaje.presupuesto_estimado > 0:
        porcentaje_gastado = min((total_gastado / viaje.presupuesto_estimado) * 100, 100)
    else:
        porcentaje_gastado = 0

    duracion = duracion_viaje((viaje.fecha_fin - viaje.fecha_inicio).days)

    puede_registrar_gasto = True
    razon_no_puede_registrar = ""

    if viaje.estado == 'finalizado':
        puede_registrar_gasto = False
        razon_no_puede_registrar = "No puedes registrar gastos en un viaje finalizado."
    elif presupuesto_restante < 0:
        puede_registrar_gasto = False
        razon_no_puede_registrar = "Presupuesto excedido. No se permiten más gastos."

    gastos_list = []
    for gasto in viaje.gastos.all():
        gasto.puede_eliminar = (request.user == gasto.pagado_por.usuario) or (rol_usuario == 'organizador')
        gastos_list.append(gasto)

    context = {
        'viaje': viaje,
        'participantes': participantes_list,
        'organizador': organizador,
        'es_participante': es_participante,
        'total_gastado': total_gastado,
        'presupuesto_restante': presupuesto_restante,
        'duracion_viaje_dias': duracion,
        'porcentaje_gastado': porcentaje_gastado,
        'puede_registrar_gasto': puede_registrar_gasto,
        'razon_no_puede_registrar': razon_no_puede_registrar,
        'rol_usuario': rol_usuario,
        'gastos': gastos_list
    }

    context.update({
        # Reemplaza 'gastos' (del modelo antiguo) por los de control_gastos
        'gastos':             GastoControl.objects.filter(viaje=viaje),
        'categorias':         GastoControl.CATEGORIAS,
        'metodos_division':   GastoControl.METODOS_DIVISION,
        'participantes_viaje': Participante.objects.filter(viaje=viaje).select_related('usuario'),
    })

    # 7. RENDERIZADO FINAL
    return render(request, 'gestion_viajes/detalle_viaje.html', context=context)

#5.1 Calculo de la duracion de un viaje 
def duracion_viaje(dias):
    def plural(valor, singular, plural):
        return f"{valor} {singular if valor == 1 else plural}"
    anos, resto = divmod(dias, 365)
    meses, dias_restantes = divmod(resto, 30)

    partes = []
    if anos:
        partes.append(plural(anos, "año", "años"))
    if meses:
        partes.append(plural(meses, "mes", "meses"))
    if dias_restantes or not partes:
        partes.append(plural(dias_restantes, "día", "días"))

    return ", ".join(partes)

# 6. Vista para EDITAR un viaje existente
def pagina_editar_viaje(request, viaje_id):
    viaje = get_object_or_404(Viaje, id=viaje_id)

    if request.method == 'POST':
        viaje.nombre = request.POST.get('nombre')
        viaje.destino = request.POST.get('destino')
        viaje.descripcion = request.POST.get('descripcion')
        viaje.fecha_inicio = request.POST.get('fecha_inicio')
        viaje.fecha_fin = request.POST.get('fecha_fin')
        viaje.capacidad_max = request.POST.get('capacidad_max')
        viaje.presupuesto_estimado = request.POST.get('presupuesto_estimado')
        
        hoy = date.today()
        fecha_inicio = viaje.fecha_inicio
        fecha_fin = viaje.fecha_fin
        if isinstance(fecha_inicio, str):
            from datetime import datetime
            fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
            fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()

        if fecha_inicio <= hoy <= fecha_fin:
            viaje.estado = 'en curso'
        elif hoy > fecha_fin:
            viaje.estado = 'finalizado'
        else:
            viaje.estado = 'planeado'

        if 'imagen_fondo' in request.FILES:
            viaje.imagen_fondo = request.FILES['imagen_fondo']

        viaje.save()
        return redirect('gestion_viajes:p_detalle_viaje', viaje_id=viaje.id)

    return render(request, 'gestion_viajes/editar_viaje.html', {
        'viaje': viaje,
        'estado_planeado': viaje.estado == 'planeado',
        'estado_en_curso': viaje.estado == 'en curso',
        'estado_finalizado': viaje.estado == 'finalizado',
    })

# 7. Vista para ELIMINAR un viaje
def eliminar_viaje(request, viaje_id):
    viaje = get_object_or_404(Viaje, id=viaje_id)
    viaje.delete()
    return redirect('gestion_viajes:p_ver_mis_viajes')

# 7.1 Vista AJAX para eliminar un viaje y devolver sus datos para restaurarlo
@require_http_methods(["POST"])
def eliminar_viaje_ajax(request, viaje_id):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'No autenticado'}, status=401)

    viaje = get_object_or_404(Viaje, id=viaje_id)

    participante = Participante.objects.filter(viaje=viaje, usuario=request.user).first()
    if not participante or participante.rol != 'organizador':
        return JsonResponse({'error': 'No tienes permiso para eliminar este viaje'}, status=403)

    participantes_data = [
        {'usuario_id': p.usuario_id, 'rol': p.rol}
        for p in viaje.participantes.all()
    ]

    gastos_data = [
        {
            'concepto': g.concepto,
            'cantidad': str(g.cantidad),
            'categoria': g.categoria,
            'pagado_por_usuario_id': g.pagado_por.usuario_id if g.pagado_por else None,
            'fecha': str(g.fecha),
        }
        for g in viaje.gastos.all()
    ]

    viaje_data = {
        'nombre': viaje.nombre,
        'destino': viaje.destino,
        'descripcion': viaje.descripcion,
        'fecha_inicio': str(viaje.fecha_inicio),
        'fecha_fin': str(viaje.fecha_fin),
        'capacidad_max': viaje.capacidad_max,
        'presupuesto_estimado': str(viaje.presupuesto_estimado) if viaje.presupuesto_estimado else '0',
        'estado': viaje.estado,
        'participantes': participantes_data,
        'gastos': gastos_data,
    }

    request.session['viaje_eliminado_data'] = viaje_data
    viaje.delete()

    return JsonResponse({
        'success': True,
        'message': 'Viaje eliminado',
        'viaje_nombre': viaje_data['nombre'],
    })

# 7.2 Vista AJAX para restaurar un viaje eliminado
@require_http_methods(["POST"])
def restaurar_viaje_ajax(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'No autenticado'}, status=401)

    viaje_data = request.session.pop('viaje_eliminado_data', None)
    if not viaje_data:
        return JsonResponse({'error': 'No hay datos de viaje para restaurar'}, status=400)

    try:
        nuevo_viaje = Viaje.objects.create(
            nombre=viaje_data['nombre'],
            destino=viaje_data['destino'],
            descripcion=viaje_data['descripcion'],
            fecha_inicio=viaje_data['fecha_inicio'],
            fecha_fin=viaje_data['fecha_fin'],
            capacidad_max=viaje_data['capacidad_max'],
            presupuesto_estimado=viaje_data['presupuesto_estimado'],
            estado=viaje_data['estado'],
        )

        User = get_user_model()
        participante_map = {}
        for p_data in viaje_data.get('participantes', []):
            try:
                usuario = User.objects.get(pk=p_data['usuario_id'])
                p = Participante.objects.create(
                    viaje=nuevo_viaje,
                    usuario=usuario,
                    rol=p_data['rol'],
                )
                participante_map[p_data['usuario_id']] = p
            except User.DoesNotExist:
                pass

        for g_data in viaje_data.get('gastos', []):
            pagado_por = participante_map.get(g_data['pagado_por_usuario_id'])
            Gasto.objects.create(
                viaje=nuevo_viaje,
                pagado_por=pagado_por,
                concepto=g_data['concepto'],
                cantidad=g_data['cantidad'],
                categoria=g_data['categoria'],
            )

        return JsonResponse({
            'success': True,
            'message': 'Viaje restaurado correctamente',
            'viaje_id': nuevo_viaje.id,
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

# 8. Vista para registrar un nuevo gasto
def registrar_gasto(request, viaje_id):
    viaje = get_object_or_404(Viaje, id=viaje_id)

    if request.method == 'POST':
        concepto = request.POST.get('concepto')
        cantidad = request.POST.get('cantidad')
        categoria = request.POST.get('categoria')

        if viaje.estado == 'finalizado':
            return redirect('gestion_viajes:p_detalle_viaje', viaje_id=viaje.id)

        total_gastado = viaje.gastos.aggregate(Sum('cantidad'))['cantidad__sum'] or 0
        presupuesto_restante = (viaje.presupuesto_estimado or 0) - total_gastado

        if presupuesto_restante < 0:
            return redirect('gestion_viajes:p_detalle_viaje', viaje_id=viaje.id)

        if request.user.is_authenticated:
            participante = Participante.objects.filter(viaje=viaje, usuario=request.user).first()

            if not participante:
                return redirect('gestion_viajes:p_detalle_viaje', viaje_id=viaje.id)

            Gasto.objects.create(
                viaje=viaje,
                pagado_por=participante,
                concepto=concepto,
                cantidad=cantidad,
                categoria=categoria
            )

        return redirect('gestion_viajes:p_detalle_viaje', viaje_id=viaje.id)

    return redirect('gestion_viajes:p_detalle_viaje', viaje_id=viaje.id)

# 8.1 Vista para eliminar un gasto
def eliminar_gasto(request, gasto_id):
    gasto = get_object_or_404(Gasto, id=gasto_id)
    viaje = gasto.viaje

    if request.user.is_authenticated:
        participante = Participante.objects.filter(viaje=viaje, usuario=request.user).first()

        if participante:
            if gasto.pagado_por.usuario == request.user or participante.rol == 'organizador':
                gasto.delete()
                messages.success(request, "Gasto eliminado correctamente.")
            else:
                messages.error(request, "No tienes permiso para eliminar este gasto.")
        else:
            messages.error(request, "No eres parte de este viaje.")

    return redirect('gestion_viajes:p_detalle_viaje', viaje_id=viaje.id)

# 8.2 Vista AJAX para eliminar un gasto y devolver los datos
@require_http_methods(["POST"])
def eliminar_gasto_ajax(request, gasto_id):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'No autenticado'}, status=401)

    gasto = get_object_or_404(Gasto, id=gasto_id)
    viaje = gasto.viaje

    participante = Participante.objects.filter(viaje=viaje, usuario=request.user).first()

    if not participante:
        return JsonResponse({'error': 'No eres parte de este viaje'}, status=403)

    if gasto.pagado_por.usuario != request.user and participante.rol != 'organizador':
        return JsonResponse({'error': 'No tienes permiso para eliminar este gasto'}, status=403)

    gasto_data = {
        'id': gasto.id,
        'concepto': gasto.concepto,
        'cantidad': str(gasto.cantidad),
        'categoria': gasto.categoria,
        'pagado_por_id': gasto.pagado_por.id,
        'viaje_id': viaje.id,
        'fecha': str(gasto.fecha),
    }

    gasto.delete()

    return JsonResponse({
        'success': True,
        'message': 'Gasto eliminado',
        'gasto_data': gasto_data
    })

# 8.3 Vista AJAX para restaurar un gasto eliminado
@require_http_methods(["POST"])
def restaurar_gasto_ajax(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'No autenticado'}, status=401)

    try:
        data = json.loads(request.body)
        gasto_data = data.get('gasto_data')

        if not gasto_data:
            return JsonResponse({'error': 'Datos de gasto no proporcionados'}, status=400)

        viaje = get_object_or_404(Viaje, id=gasto_data['viaje_id'])
        participante = get_object_or_404(Participante, id=gasto_data['pagado_por_id'])

        gasto = Gasto.objects.create(
            viaje=viaje,
            pagado_por=participante,
            concepto=gasto_data['concepto'],
            cantidad=gasto_data['cantidad'],
            categoria=gasto_data['categoria']
        )

        return JsonResponse({
            'success': True,
            'message': 'Gasto restaurado correctamente',
            'gasto_id': gasto.id
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

# 9. Vista para añadir un participante
def añadir_participante(request, viaje_id):
    viaje = get_object_or_404(Viaje, id=viaje_id)
    User = get_user_model()

    user = request.user
    if not user.is_authenticated:
        user = User.objects.first()

    if user:
        cantidad_actual = Participante.objects.filter(viaje=viaje).count()
        ya_es_participante = Participante.objects.filter(viaje=viaje, usuario=user).exists()

        if not ya_es_participante:
            if cantidad_actual < viaje.capacidad_max:
                Participante.objects.create(viaje=viaje, usuario=user, rol='integrante')
                messages.success(request, "¡Te has unido al viaje con éxito!")
            else:
                messages.error(request, "Lo sentimos, este viaje ya alcanzó su capacidad máxima.")
        else:
            messages.info(request, "Ya formas parte de este viaje.")

    return redirect('gestion_viajes:p_detalle_viaje', viaje_id=viaje.id)

class DetalleViajeView(ViajeContextMixin, DetailView):
    model = Viaje
    template_name = 'gestion_viajes/detalle.html'