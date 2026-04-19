from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from apps.gestion_viajes.models import Viaje, Participante
from .models import MensajeChat


@login_required
def lista_chats(request):
    viajes = Viaje.objects.filter(participantes__usuario=request.user)
    for v in viajes:
        v.ultimo_msg = MensajeChat.objects.filter(viaje=v).last()
        print(f"Viaje: {v.nombre} | Último msg: {v.ultimo_msg}")
    return render(request, 'chat/lista_chats.html', {'viajes': viajes})

@login_required
def chat_viaje(request, viaje_id):
    viaje = get_object_or_404(Viaje, id=viaje_id)
    viajes = Viaje.objects.filter(participantes__usuario=request.user)
    for v in viajes:
        v.ultimo_msg = MensajeChat.objects.filter(viaje=v).last()
    mensajes = MensajeChat.objects.filter(viaje=viaje)
    integrantes = Participante.objects.filter(viaje=viaje)
    return render(request, 'chat/chat_viaje.html', {
        'viaje': viaje,
        'viajes': viajes,
        'mensajes': mensajes,
        'integrantes': integrantes,
    })

@login_required
def chat_integrantes(request, viaje_id):
    viaje = get_object_or_404(Viaje, id=viaje_id)
    viajes = Viaje.objects.filter(participantes__usuario=request.user)
    mensajes = MensajeChat.objects.filter(viaje=viaje)
    participantes = Participante.objects.filter(viaje=viaje)
    return render(request, 'chat/chat_integrantes.html', {
        'viaje': viaje,
        'viajes': viajes,
        'mensajes': mensajes,
        'participantes': participantes,
    })


@login_required
def enviar_mensaje(request, viaje_id):
    if request.method == 'POST':
        viaje = get_object_or_404(Viaje, id=viaje_id)
        contenido = request.POST.get('contenido', '').strip()
        if contenido:
            MensajeChat.objects.create(
                viaje=viaje,
                usuario=request.user,
                contenido=contenido,
            )
    return redirect('chat:chat_viaje', viaje_id=viaje_id)


@login_required
def abandonar_viaje(request, viaje_id):
    if request.method == 'POST':
        viaje = get_object_or_404(Viaje, id=viaje_id)
        Participante.objects.filter(viaje=viaje, usuario=request.user).delete()
        return redirect('chat:lista_chats')
    return redirect('chat:chat_viaje', viaje_id=viaje_id)   