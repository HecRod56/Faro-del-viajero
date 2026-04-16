from django.shortcuts import render, redirect # Importamos redirect para navegar tras guardar
from .models import Viaje, Gasto, Participante# Importamos tu modelo para escribir en Postgres
from django.shortcuts import render, get_object_or_404
from django.db.models import Sum # Importamos Sum para hacer matemáticas
from django.contrib.auth import get_user_model # Importa esto al principio
from django.contrib import messages
from django.contrib.auth.decorators import login_required

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
        return redirect('p_ver_mis_viajes')

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
    viaje = get_object_or_404(Viaje, id=viaje_id)
    
    # Verifica si el usuario logueado ya está en la lista de participantes
    es_participante = viaje.participantes.filter(usuario=request.user).exists() if request.user.is_authenticated else False

    # ESTA LÍNEA ES LA CLAVE: Trae a los amigos de la base de datos
    participantes_list = viaje.participantes.all() 
    
    total_gastado = viaje.gastos.aggregate(Sum('cantidad'))['cantidad__sum'] or 0
    presupuesto_restante = (viaje.presupuesto_estimado or 0) - total_gastado

    # Se estima la duracion del viaje en dias 
    duracion = duracion_viaje((viaje.fecha_fin-viaje.fecha_inicio).days)

    # Logica para la barra del presupuesto gastado
    total_gastado = viaje.gastos.aggregate(total=Sum('cantidad'))['total'] or 0
    presupuesto_restante = viaje.presupuesto_estimado - total_gastado

    if viaje.presupuesto_estimado and viaje.presupuesto_estimado > 0:
        porcentaje_gastado = (total_gastado / viaje.presupuesto_estimado) * 100
        porcentaje_gastado = min(porcentaje_gastado, 100)  # tope en 100%
    else:
        porcentaje_gastado = 0

   

    return render(request, 'gestion_viajes/detalle_viaje.html', {
        'viaje': viaje,
        'participantes': participantes_list, # <--- Verifica que diga 'participantes'
        'es_participante': es_participante,
        'total_gastado': total_gastado,
        'presupuesto_restante': presupuesto_restante,
        'duracion_viaje_dias': duracion, 
        'porcentaje_gastado': porcentaje_gastado
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
        return redirect('p_detalle_viaje', viaje_id=viaje.id)

    # Si es GET, enviamos el objeto 'viaje' para rellenar los inputs
    return render(request, 'gestion_viajes/editar_viaje.html', {'viaje': viaje})

# 7. Vista para ELIMINAR un viaje
def eliminar_viaje(request, viaje_id):
    viaje = get_object_or_404(Viaje, id=viaje_id)
    viaje.delete() # ¡Adiós registro!
    return redirect('p_ver_mis_viajes')

# 8. Vista para registrar un nuevo gasto
def registrar_gasto(request, viaje_id):
    viaje = get_object_or_404(Viaje, id=viaje_id)
    
    if request.method == 'POST':
        concepto = request.POST.get('concepto')
        cantidad = request.POST.get('cantidad')
        categoria = request.POST.get('categoria')
        
        # Creamos el gasto ligado a este viaje
        Gasto.objects.create(
            viaje=viaje,
            concepto=concepto,
            cantidad=cantidad,
            categoria=categoria
        )
        
        # Regresamos a la misma página de detalle para ver el gasto reflejado
        return redirect('p_detalle_viaje', viaje_id=viaje.id)
    
    return redirect('p_detalle_viaje', viaje_id=viaje.id)

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
    
    return redirect('p_detalle_viaje', viaje_id=viaje.id)




