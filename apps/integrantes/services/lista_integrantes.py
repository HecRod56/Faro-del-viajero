from apps.gestion_viajes.models import Participante, Viaje
from django.contrib.auth import get_user_model

def lista_integrantes_viaje(id_viaje):
    viaje = Viaje.objects.get(id_viaje)
    participantes = viaje.participantes.select_related('usuario')

    for p in participantes:
        print(p.usuario.email, p.rol)