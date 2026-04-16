from apps.gestion_viajes.models import Participante, Viaje
from apps.autenticado.models import CustomUser
from django.shortcuts import get_object_or_404

def lista_integrantes_viaje(viaje, usuario_id):
    participantes_qs = (
        viaje.participantes
        .select_related('usuario')
    )

    integrantes = []

    for p in participantes_qs:
        integrantes.append({
            "id": p.usuario.id,
            "nombre": (
                f"{p.usuario.first_name} {p.usuario.last_name}".strip()
                if p.usuario.first_name or p.usuario.last_name
                else p.usuario.email
            ),
            "rol": "Organizador" if p.rol == "organizador" else "Integrante",
            "es_organizador": (p.rol == "organizador"),
            "telefono": p.usuario.phone,
            "es_actual": (p.usuario.id == usuario_id),
        })

    return integrantes

from apps.gestion_viajes.models import Participante

def usuario_es_organizador(viaje, id_usuario):
    return Participante.objects.filter(
        viaje=viaje,
        usuario_id=id_usuario,
        rol="organizador"
    ).exists()