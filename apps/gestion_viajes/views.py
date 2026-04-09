from django.shortcuts import render, redirect # Importamos redirect para navegar tras guardar
from .models import Viaje # Importamos tu modelo para escribir en Postgres
from django.shortcuts import render, get_object_or_404
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

        # Creamos el registro en la base de datos PostgreSQL
        Viaje.objects.create(
            nombre=nombre,
            destino=destino,
            descripcion=descripcion,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            capacidad_max=capacidad if capacidad else 2,
            presupuesto_estimado=presupuesto if presupuesto else 0
        )
        
        # Una vez guardado, redirigimos a la lista de viajes para confirmar
        return redirect('p_ver_mis_viajes')

    # Si entran por primera vez (GET), solo mostramos el formulario
    return render(request, 'gestion_viajes/crear_viaje.html')

# 3. Vista para ver todos los viajes registrados
def pagina_ver_mis_viajes(request):
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
    # Cambia status_404 por 404 a secas
    viaje = get_object_or_404(Viaje, id=viaje_id)
    
    return render(request, 'gestion_viajes/detalle_viaje.html', {'viaje': viaje})
