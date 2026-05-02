from django.db import models
from django.conf import settings
from apps.gestion_viajes.models import Viaje


class MensajeChat(models.Model):
    viaje = models.ForeignKey(Viaje, on_delete=models.CASCADE, related_name='mensajes')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    contenido = models.TextField()
    fecha_envio = models.DateTimeField(auto_now_add=True)
    es_sistema = models.BooleanField(default=False)

    class Meta:
        ordering = ['fecha_envio']

    def __str__(self):
        return f"{self.viaje.nombre} - {self.usuario} - {self.fecha_envio}"


class ChatAbandonado(models.Model):
    viaje = models.ForeignKey(Viaje, on_delete=models.CASCADE)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('viaje', 'usuario')

    def __str__(self):
        return f"{self.usuario} abandono chat de {self.viaje}"