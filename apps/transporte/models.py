
# Create your models here.
# apps/transporte/models.py
# ==========================================
# Modelos del módulo de transporte (RF-70, RF-74)
# ==========================================

from django.db import models
from django.conf import settings
from apps.gestion_viajes.models import Viaje


class Trayecto(models.Model):
    """
    Representa un trayecto principal de ida o regreso
    registrado por un integrante del viaje.
    """

    TIPO_CHOICES = [
        ('IDA', 'Ida'),
        ('REGRESO', 'Regreso'),
    ]

    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente de comprobante'),
        ('CONFIRMADO', 'Reserva confirmada'),
    ]

    # ==========================================
    # Relaciones
    # ==========================================
    viaje = models.ForeignKey(
        Viaje,
        on_delete=models.CASCADE,
        related_name='trayectos',
        help_text="Viaje al que pertenece este trayecto"
    )
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='trayectos_registrados',
        help_text="Usuario que registró el trayecto"
    )

    # ==========================================
    # Tipo y estado
    # ==========================================
    tipo = models.CharField(
        max_length=10,
        choices=TIPO_CHOICES,
        default='IDA'
    )
    estado = models.CharField(
        max_length=15,
        choices=ESTADO_CHOICES,
        default='PENDIENTE'
    )

    # ==========================================
    # Datos del vuelo (RF-70, RF-74)
    # ==========================================
    aerolinea = models.CharField(max_length=100)
    numero_vuelo = models.CharField(max_length=20)
    
    origen_codigo = models.CharField(max_length=5, help_text="Código IATA del aeropuerto de origen")
    destino_codigo = models.CharField(max_length=5, help_text="Código IATA del aeropuerto de destino")
    
    fecha_salida = models.DateTimeField()
    fecha_llegada = models.DateTimeField()
    
    duracion = models.CharField(max_length=20, blank=True, default="")
    escalas = models.IntegerField(default=0)
    escalas_texto = models.CharField(max_length=50, blank=True, default="Directo")

    # ==========================================
    # Precio (RF-75)
    # ==========================================
    precio_total = models.DecimalField(max_digits=10, decimal_places=2)
    moneda = models.CharField(max_length=5, default="USD")
    pasajeros = models.IntegerField(default=1)

    # ==========================================
    # Datos de la reserva (RF-74)
    # ==========================================
    offer_id = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="ID de la oferta en Duffel"
    )
    numero_asiento = models.CharField(max_length=10, blank=True, default="")
    enlace_ticket = models.URLField(blank=True, default="")
    comprobante = models.FileField(
        upload_to='comprobantes_transporte/',
        blank=True,
        null=True
    )

    # ==========================================
    # Metadata
    # ==========================================
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['fecha_salida']
        verbose_name = 'Trayecto'
        verbose_name_plural = 'Trayectos'

    def __str__(self):
        return f"{self.tipo} | {self.aerolinea} {self.numero_vuelo} | {self.origen_codigo} → {self.destino_codigo}"