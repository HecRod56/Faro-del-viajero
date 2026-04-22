from django.shortcuts import render, redirect # Importamos redirect para navegar tras guardar
from .models import Viaje, Gasto, Participante# Importamos tu modelo para escribir en Postgres
from django.shortcuts import render, get_object_or_404
from django.db.models import Sum # Importamos Sum para hacer matemáticas
from django.contrib.auth import get_user_model # Importa esto al principio
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .mixins import ViajeContextMixin
from django.views.generic import DetailView
import json

# 1. Página de inicio del módulo
def pagina_inicio(request):
    return render(request, 'gestion_viajes/inicio.html')

# 2. Lógica para mostrar Y GUARDAR el viaje
def pagina_crear_viaje(request):
    if request.method == 'POST':
        # Extraemos los datos que vienen del formulario HTML (usando los 'name')
        nombre = request.POST.get('nombre')
        destino = request.POST.get('destino')
        descripcion = request.POST.get('descripcion')
        fecha_inicio = request.POST.get('fecha_inicio')
        fecha_fin = request.POST.get('fecha_fin')
        capacidad = request.POST.get('capacidad_max')
        presupuesto = request.POST.get('presupuesto_estimado')

        # 1. Creamos el viaje y lo guardamos en una variable 'nuevo_viaje' (Postgres)
        nuevo_viaje = Viaje.objects.create(
            nombre=nombre,
            destino=destino,
            descripcion=descripcion,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            capacidad_max=capacidad if capacidad else 2,
            presupuesto_estimado=presupuesto if presupuesto else 0
        )
        
        # 2. AUTOMATIZACIÓN: Registrar al creador como Organizador
        # Si el usuario no está logueado (por pruebas), usamos el primero de la DB
        user_actual = request.user
        if not user_actual.is_authenticated:
            User = get_user_model()
            user_actual = User.objects.first()

        if user_actual:
            Participante.objects.create(
                viaje=nuevo_viaje,
                usuario=user_actual,
                rol='organizador' # <--- Clave para RF.2-07 y RF.2-09
            )
        
        # Una vez guardado, redirigimos a la lista de viajes para confirmar
        return redirect('gestion_viajes:p_ver_mis_viajes')

    # Si entran por primera vez (GET), solo mostramos el formulario
    return render(request, 'gestion_viajes/crear_viaje.html')

# 3. Vista para ver todos los viajes registrados
def pagina_ver_mis_viajes(request):
    user_actual = request.user
    
    # Si no está logueado, para que no truene, buscamos al primer usuario de la DB
    if not user_actual.is_authenticated:
        User = get_user_model()
        user_actual = User.objects.first()

    # RF.2-05: Solo traer viajes donde participa este usuario
    viajes_db = Viaje.objects.filter(participantes__usuario=user_actual)

    # Obtenemos el estado desde la URL (ej: ?estado=planeado)
    estado_filtro = request.GET.get('estado')
    
    if estado_filtro:
        # Filtramos los viajes por ese estado
        viajes_db = Viaje.objects.filter(estado=estado_filtro)
    else:
        # Si no hay filtro, mostramos todos
        viajes_db = Viaje.objects.all()
        
    return render(request, 'gestion_viajes/ver_mis_viajes.html', {
        'viajes': viajes_db,
        'filtro_actual': estado_filtro  # Pasamos esto para saber qué botón iluminar
    })

# 4. Vista para ver solo los viajes con estado 'planeado'
def pagina_viajes_planeados(request):
    viajes_p = Viaje.objects.filter(estado='planeado')
    return render(request, 'gestion_viajes/viajes_planeados.html', {'viajes': viajes_p})

# 5. Vista para mostrar el detalle de un viaje específico
def pagina_detalle_viaje(request, viaje_id):
    # 1. Obtenemos el viaje o lanzamos 404
    viaje = get_object_or_404(Viaje, id=viaje_id)
    
    # 2. --- BLOQUE DE SEGURIDAD RNF-06 (Control de Acceso) ---
    # Verificamos si el usuario es participante antes de calcular nada
    if request.user.is_authenticated:
        participante_actual = Participante.objects.filter(viaje=viaje, usuario=request.user).first()
        
        if not participante_actual:
            from django.contrib import messages
            messages.error(request, "Acceso denegado: No eres integrante de este viaje.")
            return redirect('gestion_viajes:p_ver_mis_viajes')
        
        es_participante = True
        rol_usuario = participante_actual.rol
    else:
        # Si no está autenticado, lo mandamos al login o lista
        return redirect('login') 

    # 3. LÓGICA DE CÁLCULOS (Presupuesto y Gastos)
    # Traemos a todos los participantes para la lista lateral
    participantes_list = viaje.participantes.all()
    
    # Obtener al organizador del viaje
    organizador = participantes_list.filter(rol='organizador').first() 
    
    # Matemáticas de gastos
    total_gastado = viaje.gastos.aggregate(total=Sum('cantidad'))['total'] or 0
    presupuesto_restante = (viaje.presupuesto_estimado or 0) - total_gastado

    # Porcentaje para la barra de progreso
    if viaje.presupuesto_estimado and viaje.presupuesto_estimado > 0:
        porcentaje_gastado = min((total_gastado / viaje.presupuesto_estimado) * 100, 100)
    else:
        porcentaje_gastado = 0  

    # 4. CÁLCULO DE DURACIÓN
    # Usamos tu función auxiliar duracion_viaje
    duracion = duracion_viaje((viaje.fecha_fin - viaje.fecha_inicio).days)

    # 5. REGLAS DE NEGOCIO PARA REGISTRO DE GASTOS
    puede_registrar_gasto = True
    razon_no_puede_registrar = ""
    
    # Regla 1: Estado finalizado
    if viaje.estado == 'finalizado':
        puede_registrar_gasto = False
        razon_no_puede_registrar = "No puedes registrar gastos en un viaje finalizado."
    
    # Regla 2: Presupuesto agotado
    elif presupuesto_restante < 0:
        puede_registrar_gasto = False
        razon_no_puede_registrar = "Presupuesto excedido. No se permiten más gastos."

    # 6. RENDERIZADO FINAL
    return render(request, 'gestion_viajes/detalle_viaje.html', {
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
        'rol_usuario': rol_usuario # Útil para mostrar/ocultar botones en el HTML
    })

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
    if dias_restantes or not partes:  # asegura que algo se muestre
        partes.append(plural(dias_restantes, "día", "días"))

    return ", ".join(partes) 

# 6. Vista para EDITAR un viaje existente
def pagina_editar_viaje(request, viaje_id):
    viaje = get_object_or_404(Viaje, id=viaje_id)

    if request.method == 'POST':
        # Actualizamos los campos del objeto con lo que viene del formulario
        viaje.nombre = request.POST.get('nombre')
        viaje.destino = request.POST.get('destino')
        viaje.descripcion = request.POST.get('descripcion')
        viaje.fecha_inicio = request.POST.get('fecha_inicio')
        viaje.fecha_fin = request.POST.get('fecha_fin')
        viaje.capacidad_max = request.POST.get('capacidad_max')
        viaje.presupuesto_estimado = request.POST.get('presupuesto_estimado')
        viaje.estado = request.POST.get('estado') # Agregamos estado por si quieren cambiarlo
        
        viaje.save() # Guardamos los cambios en Postgres
        return redirect('gestion_viajes:p_detalle_viaje', viaje_id=viaje.id)

    # Si es GET, enviamos el objeto 'viaje' para rellenar los inputs
    return render(request, 'gestion_viajes/editar_viaje.html', {'viaje': viaje})

# 7. Vista para ELIMINAR un viaje
def eliminar_viaje(request, viaje_id):
    viaje = get_object_or_404(Viaje, id=viaje_id)
    viaje.delete() # ¡Adiós registro!
    return redirect('gestion_viajes:p_ver_mis_viajes')

# 8. Vista para registrar un nuevo gasto
def registrar_gasto(request, viaje_id):
    viaje = get_object_or_404(Viaje, id=viaje_id)
    
    if request.method == 'POST':
        concepto = request.POST.get('concepto')
        cantidad = request.POST.get('cantidad')
        categoria = request.POST.get('categoria')
        
        # VALIDACIÓN 1: El estado del viaje no puede ser "finalizado"
        if viaje.estado == 'finalizado':
            # Redirigimos sin guardar el gasto
            return redirect('gestion_viajes:p_detalle_viaje', viaje_id=viaje.id)
        
        # VALIDACIÓN 2: Verificar que el presupuesto no esté en cifras negativas
        total_gastado = viaje.gastos.aggregate(Sum('cantidad'))['cantidad__sum'] or 0
        presupuesto_restante = (viaje.presupuesto_estimado or 0) - total_gastado
        
        # Si la suma de este gasto + lo ya gastado excede el presupuesto
        if presupuesto_restante < 0:
            return redirect('gestion_viajes:p_detalle_viaje', viaje_id=viaje.id)
        
        # VALIDACIÓN 3: El usuario debe ser participante del viaje
        if request.user.is_authenticated:
            participante = Participante.objects.filter(
                viaje=viaje,
                usuario=request.user
            ).first()
            
            if not participante:
                return redirect('gestion_viajes:p_detalle_viaje', viaje_id=viaje.id)
        
            # Si pasa todas las validaciones, creamos el gasto ligado a este viaje y al participante
            Gasto.objects.create(
                viaje=viaje,
                pagado_por=participante,
                concepto=concepto,
                cantidad=cantidad,
                categoria=categoria
            )
        
        # Regresamos a la misma página de detalle para ver el gasto reflejado
        return redirect('gestion_viajes:p_detalle_viaje', viaje_id=viaje.id)
    
    return redirect('gestion_viajes:p_detalle_viaje', viaje_id=viaje.id)

# 8.1 Vista para eliminar un gasto
def eliminar_gasto(request, gasto_id):
    gasto = get_object_or_404(Gasto, id=gasto_id)
    viaje = gasto.viaje
    
    # Verificar que el usuario sea el que registró el gasto o un organizador
    if request.user.is_authenticated:
        participante = Participante.objects.filter(viaje=viaje, usuario=request.user).first()
        
        if participante:
            # Permite eliminar si es quien registró el gasto o si es organizador
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
    """Elimina un gasto y devuelve sus datos en JSON para poder restaurarlo"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'No autenticado'}, status=401)
    
    gasto = get_object_or_404(Gasto, id=gasto_id)
    viaje = gasto.viaje
    
    # Verificar permisos
    participante = Participante.objects.filter(viaje=viaje, usuario=request.user).first()
    
    if not participante:
        return JsonResponse({'error': 'No eres parte de este viaje'}, status=403)
    
    if gasto.pagado_por.usuario != request.user and participante.rol != 'organizador':
        return JsonResponse({'error': 'No tienes permiso para eliminar este gasto'}, status=403)
    
    # Guardar los datos del gasto antes de eliminarlo
    gasto_data = {
        'id': gasto.id,
        'concepto': gasto.concepto,
        'cantidad': str(gasto.cantidad),
        'categoria': gasto.categoria,
        'pagado_por_id': gasto.pagado_por.id,
        'viaje_id': viaje.id,
        'fecha': str(gasto.fecha),
    }
    
    # Eliminar el gasto
    gasto.delete()
    
    return JsonResponse({
        'success': True,
        'message': 'Gasto eliminado',
        'gasto_data': gasto_data
    })

# 8.3 Vista AJAX para restaurar un gasto eliminado
@require_http_methods(["POST"])
def restaurar_gasto_ajax(request):
    """Restaura un gasto que fue eliminado recientemente"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'No autenticado'}, status=401)
    
    try:
        data = json.loads(request.body)
        gasto_data = data.get('gasto_data')
        
        if not gasto_data:
            return JsonResponse({'error': 'Datos de gasto no proporcionados'}, status=400)
        
        # Obtener el viaje
        viaje = get_object_or_404(Viaje, id=gasto_data['viaje_id'])
        
        # Obtener el participante que pagó
        participante = get_object_or_404(Participante, id=gasto_data['pagado_por_id'])
        
        # Recrear el gasto
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

# 9. Vista para añadir un participante (por ahora simplificado)

def añadir_participante(request, viaje_id):
    viaje = get_object_or_404(Viaje, id=viaje_id)
    User = get_user_model() # Esto obtiene automáticamente tu CustomUser
    
    user = request.user
    # Si no hay sesión iniciada, buscamos al primer usuario de tu tabla CustomUser
    if not user.is_authenticated:
        user = User.objects.first() 

    if user:
        # 1. Contar cuántos participantes tiene ya este viaje
        cantidad_actual = Participante.objects.filter(viaje=viaje).count()

        # 2. Validar si ya existe el usuario en el viaje
        ya_es_participante = Participante.objects.filter(viaje=viaje, usuario=user).exists()

        if not ya_es_participante:
            # 3. Validar capacidad máxima
            if cantidad_actual < viaje.capacidad_max:
                Participante.objects.create(
                    viaje=viaje,
                    usuario=user,
                    rol='integrante'
                )
                messages.success(request, "¡Te has unido al viaje con éxito!")
            else:
                # Si llega aquí, es porque alguien intentó entrar por URL y el viaje está lleno
                messages.error(request, "Lo sentimos, este viaje ya alcanzó su capacidad máxima.")
        else:
            messages.info(request, "Ya formas parte de este viaje.")
    
    return redirect('gestion_viajes:p_detalle_viaje', viaje_id=viaje.id)

class DetalleViajeView(ViajeContextMixin, DetailView):
    model = Viaje
    template_name = 'gestion_viajes/detalle.html'