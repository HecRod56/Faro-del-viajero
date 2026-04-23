from django.db import models
from django.conf import settings
from apps.gestion_viajes.models import Viaje

class Actividad(models.Model):
    ESTADOS = (
        ('VOTACION', 'En Votación'),
        ('APROBADA', 'Aprobada'),
        ('RECHAZADA', 'Rechazada'),
    )

    # Relación con el viaje
    viaje = models.ForeignKey(Viaje, on_delete=models.CASCADE, related_name='actividades')
    
    # Mantenemos el creador con CASCADE para asegurar la integridad referencial
    creador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    # Combinamos lo mejor de ambos: tu título y su descripción
    titulo = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True, null=True)
    ubicacion = models.CharField(max_length=200, blank=True, null=True)
    
    # Mantenemos fecha y hora separados para tu lógica de formularios
    fecha = models.DateField()
    hora = models.TimeField()
    
    estado = models.CharField(max_length=15, choices=ESTADOS, default='VOTACION')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.titulo} - {self.viaje}"

    @property
    def votos_a_favor(self):
        return self.votos.filter(voto='SI').count()
    
    @property
    def votos_totales(self):
        return self.votos.count()

class VotoActividad(models.Model):
    OPCIONES = (
        ('SI', 'A Favor'),
        ('NO', 'En Contra'),
    )
    actividad = models.ForeignKey(Actividad, on_delete=models.CASCADE, related_name='votos')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    voto = models.CharField(max_length=2, choices=OPCIONES)
    fecha_voto = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Un usuario solo puede votar una vez por actividad
        unique_together = ('actividad', 'usuario')