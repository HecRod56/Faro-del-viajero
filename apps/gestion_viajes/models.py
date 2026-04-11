from django.db import models
from django.conf import settings #Para referenciar al usuario del sistema

class Viaje(models.Model):
    ESTADOS_VIAJE = [
        ('planeado','Planeado'),
        ('en curso','En curso'),
        ('finalizado','Finalizado'),
    ]

    nombre = models.CharField(max_length=100)
    destino = models.CharField(max_length=100) #Estado de la Rep. Mexicana
    descripcion = models.TextField(blank=True, null=True) #Opcional
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    capacidad_max = models.PositiveIntegerField()
    presupuesto_estimado = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    estado = models.CharField(max_length=20, choices=ESTADOS_VIAJE, default='planeado')
    imagen_destino = models.ImageField(upload_to='destinos/',blank=True, null=True)

    def __str__(self):
        return self.nombre
    
class Participante(models.Model):
    ROLES = [
        ('organizador','Organizador'),
        ('integrante','Integrante'),
    ]

    viaje = models.ForeignKey(Viaje, on_delete=models.CASCADE, related_name='participantes')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rol = models.CharField(max_length=20, choices=ROLES, default='integrante')
    fecha_union = models.DateTimeField(auto_now_add=True)
    class Meta:
        # Esto evita que un usuario se una dos veces al mismo viaje
        unique_together = ('viaje', 'usuario')

    def __str__(self):
        return f"{self.usuario} en {self.viaje} ({self.rol})"
    
class HistorialEstado(models.Model):
    viaje = models.ForeignKey(Viaje, on_delete=models.CASCADE)
    estado_anterior = models.CharField(max_length=20)
    estado_nuevo = models.CharField(max_length=20)
    usuario_cambio = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    fecha_cambio = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cambio en {self.viaje.nombre}: {self.estado_anterior} -> {self.estado_nuevo}"

class Gasto(models.Model):
    CATEGORIAS = [
        ('transporte', 'Transporte 🚗'),
        ('comida', 'Comida 🍕'),
        ('hospedaje', 'Hospedaje 🏨'),
        ('entretenimiento', 'Entretenimiento 🎟️'),
        ('otros', 'Otros 📦'),
    ]

    viaje = models.ForeignKey(Viaje, on_delete=models.CASCADE, related_name='gastos')
    # Opcional: ¿Quién pagó? Referenciamos a Participante
    pagado_por = models.ForeignKey(Participante, on_delete=models.SET_NULL, null=True, blank=True)
    
    concepto = models.CharField(max_length=100)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    categoria = models.CharField(max_length=20, choices=CATEGORIAS, default='otros')
    fecha = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.concepto} (${self.cantidad}) - {self.viaje.nombre}"