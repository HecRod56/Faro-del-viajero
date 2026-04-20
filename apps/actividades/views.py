from django.shortcuts import render, get_object_or_404, redirect
from apps.gestion_viajes.models import Viaje
from .models import Actividad
from django.contrib import messages
from django.db import IntegrityError
from django.contrib.auth.models import User

# Create your views here.
def proponer_actividad(request, viaje_id):
    viaje = get_object_or_404(Viaje, id=viaje_id)
    participantes = viaje.participantes.all()

    # Si no hay participantes, mostramos al usuario actual (tú)
    es_lista_usuarios = not participantes.exists()
    participantes_lista = [request.user] if es_lista_usuarios else participantes

    context = {
        'viaje': viaje,
        'participantes': participantes_lista,
        'es_lista_usuarios': es_lista_usuarios
    }

    if request.method == 'POST':
        nombre = request.POST.get('nombre_actividad')
        categoria = request.POST.get('categoria')
        detalle_otro = request.POST.get('otro_transporte_detalle')
        fecha_hora = request.POST.get('fecha_hora')
        
        # Obtenemos el ID que viene del <select name="responsable">
        responsable_id = request.POST.get('responsable')

        # Validación manual de "Otro"
        if categoria == 'Otro' and not detalle_otro:
            messages.error(request, "⚠️ Por favor, detalla el transporte.")
            return render(request, 'actividades/proponer_actividad.html', context)

        try:
            # Creamos el objeto. responsable_id debe ser un ID de la tabla User.
            nueva_actividad = Actividad(
                viaje=viaje,
                nombre=nombre,
                responsable_id=int(responsable_id), # Forzamos a que sea entero
                descripcion=request.POST.get('descripcion'),
                fecha_hora=fecha_hora,
                ubicacion=request.POST.get('ubicacion'),
            )
            nueva_actividad.save()
            messages.success(request, f'¡Actividad "{nombre}" guardada con éxito!')
            return redirect(f'/viajes/detalle/{viaje.id}/')

        except (IntegrityError, ValueError, TypeError) as e:
            print(f"DEBUG ERROR: {e}") # Revisa tu consola de VS Code para ver el error real
            messages.error(request, "⚠️ Error al guardar: El responsable no es válido.")
            return render(request, 'actividades/proponer_actividad.html', context)

    return render(request, 'actividades/proponer_actividad.html', context)

def editar_actividad(request):
    # datos de act especifica
    return render(request, 'actividades/editar_actividad.html')