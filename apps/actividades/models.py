from django.db import models
from django.conf import settings  # Importante para referenciar al usuario
from apps.gestion_viajes.models import Viaje

class Actividad(models.Model):
    # Relación con el viaje (Foreign Key)
    viaje = models.ForeignKey(Viaje, on_delete=models.CASCADE, related_name='actividades')
    
    # Campos de la actividad
    nombre = models.CharField(max_length=200)
    fecha_hora = models.DateTimeField()
    ubicacion = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    
    # Relación con el usuario que propone la actividad
    # Usamos settings.AUTH_USER_MODEL para que Django sepa cuál es tu usuario de IPN/ESCOM
    responsable = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.nombre} ({self.viaje.destino})"