from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import IntegrityError
from django.contrib.auth.models import User

from apps.gestion_viajes.models import Viaje
from .models import Actividad, VotoActividad

# ==========================================
# VISTAS DE Andy (Adaptadas al nuevo modelo)
# ==========================================
def proponer_actividad(request, viaje_id):
    viaje = get_object_or_404(Viaje, id=viaje_id)
    participantes = viaje.participantes.all()

    # Si no hay participantes, mostramos al usuario actual
    es_lista_usuarios = not participantes.exists()
    participantes_lista = [request.user] if es_lista_usuarios else participantes

    context = {
        'viaje': viaje,
        'participantes': participantes_lista,
        'es_lista_usuarios': es_lista_usuarios
    }

    if request.method == 'POST':
        # Adaptamos el 'nombre_actividad' de su formulario a tu campo 'titulo'
        titulo = request.POST.get('nombre_actividad')
        categoria = request.POST.get('categoria')
        detalle_otro = request.POST.get('otro_transporte_detalle')
        
        # Su formulario manda fecha y hora juntos, el tuyo separado. 
        # Lo separamos aquí para que la base de datos no arroje error.
        fecha_hora_str = request.POST.get('fecha_hora')
        fecha = None
        hora = None
        if fecha_hora_str:
            # Asumiendo formato "YYYY-MM-DDTHH:MM" que envían los inputs datetime-local
            partes = fecha_hora_str.split('T')
            if len(partes) == 2:
                fecha = partes[0]
                hora = partes[1]

        responsable_id = request.POST.get('responsable')

        # Validación manual de "Otro"
        if categoria == 'Otro' and not detalle_otro:
            messages.error(request, "⚠️ Por favor, detalla el transporte.")
            return render(request, 'actividades/proponer_actividad.html', context)

        try:
            # Creamos el objeto con los campos del modelo unificado
            nueva_actividad = Actividad(
                viaje=viaje,
                titulo=titulo, # Antes nombre
                creador_id=int(responsable_id), # Antes responsable_id
                descripcion=request.POST.get('descripcion'),
                fecha=fecha, # Antes fecha_hora
                hora=hora,
                ubicacion=request.POST.get('ubicacion'),
                estado='VOTACION' # Inicia en votación por defecto
            )
            nueva_actividad.save()
            messages.success(request, f'¡Actividad "{titulo}" guardada con éxito!')
            return redirect(f'/viajes/detalle/{viaje.id}/')

        except (IntegrityError, ValueError, TypeError) as e:
            print(f"DEBUG ERROR: {e}")
            messages.error(request, "⚠️ Error al guardar: Revisa los datos enviados.")
            return render(request, 'actividades/proponer_actividad.html', context)

    return render(request, 'actividades/proponer_actividad.html', context)

def editar_actividad(request):
    # datos de act especifica
    return render(request, 'actividades/editar_actividad.html')

# ==========================================
# TUS VISTAS (Línea de tiempo y Votación)
# ==========================================
@login_required
def lista_actividades(request, viaje_id):
    viaje = get_object_or_404(Viaje, id=viaje_id)
    
    actividades_pendientes = Actividad.objects.filter(viaje=viaje, estado='VOTACION').order_by('fecha', 'hora')
    actividades_aprobadas = Actividad.objects.filter(viaje=viaje, estado='APROBADA').order_by('fecha', 'hora')
    
    total_integrantes = viaje.integrantes.count() if hasattr(viaje, 'integrantes') else 6

    context = {
        'viaje': viaje,
        'actividades_pendientes': actividades_pendientes,
        'actividades_aprobadas': actividades_aprobadas,
        'total_integrantes': total_integrantes,
    }
    return render(request, 'actividades/actividades.html', context)

@login_required
def votar_actividad(request, actividad_id):
    if request.method == 'POST':
        actividad = get_object_or_404(Actividad, id=actividad_id)
        tipo_voto = request.POST.get('voto')
        
        VotoActividad.objects.update_or_create(
            actividad=actividad,
            usuario=request.user,
            defaults={'voto': tipo_voto}
        )

        total_integrantes = actividad.viaje.integrantes.count() if hasattr(actividad.viaje, 'integrantes') else 6
        votos_necesarios = (total_integrantes // 2) + 1
        
        if actividad.votos_a_favor >= votos_necesarios:
            actividad.estado = 'APROBADA'
            actividad.save()
            messages.success(request, f"¡La actividad '{actividad.titulo}' ha sido aprobada por el grupo!")
        else:
            messages.success(request, "Tu voto ha sido registrado.")

        return redirect('actividades:lista', viaje_id=actividad.viaje.id)
    
@login_required
def eliminar_actividad(request, actividad_id):
    # Buscamos la actividad en la base de datos
    actividad = get_object_or_404(Actividad, id=actividad_id)
    viaje_id = actividad.viaje.id # Guardamos el ID del viaje para saber a dónde regresar
    
    # Por seguridad, solo borramos si la petición viene de un formulario (POST)
    if request.method == 'POST':
        nombre_borrado = actividad.titulo
        actividad.delete()
        messages.success(request, f"La actividad '{nombre_borrado}' ha sido eliminada.")
        
    return redirect('actividades:lista', viaje_id=viaje_id)

@login_required
def detalle_actividad(request, actividad_id):
    # Buscamos la actividad en la base de datos
    actividad = get_object_or_404(Actividad, id=actividad_id)
    
    # Calculamos el total de integrantes para los porcentajes/badges
    total_integrantes = actividad.viaje.integrantes.count() if hasattr(actividad.viaje, 'integrantes') else 6
    
    context = {
        'actividad': actividad,
        'total_integrantes': total_integrantes,
    }
    return render(request, 'actividades/actividad_detalle.html', context)