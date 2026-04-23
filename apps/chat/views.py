from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.gestion_viajes.mixins import ViajeContextMixin
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

class ChatViajeView(LoginRequiredMixin, ViajeContextMixin, TemplateView):
    template_name = 'chat/chat_viaje.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # El Mixin 'ViajeContextMixin' debería estar poniendo self.viaje o self.viaje_actual
        # Nos aseguramos de tener el objeto viaje disponible
        viaje_obj = getattr(self, 'viaje', getattr(self, 'viaje_actual', None))
        
        viajes = Viaje.objects.filter(participantes__usuario=self.request.user)
        for v in viajes:
            v.ultimo_msg = MensajeChat.objects.filter(viaje=v).last()
            
        context.update({
            'viaje': viaje_obj, # <--- ESTO ES LO QUE ESTABA FALTANDO
            'viajes': viajes,
            'mensajes': MensajeChat.objects.filter(viaje=viaje_obj),
            'integrantes': Participante.objects.filter(viaje=viaje_obj),
        })
        return context

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