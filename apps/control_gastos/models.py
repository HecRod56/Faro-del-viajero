from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal


# ─── Managers ────────────────────────────────────────────────────────────────

class SoftDeleteManager(models.Manager):
    """Solo devuelve registros activos (no eliminados)."""
    def get_queryset(self):
        return super().get_queryset().filter(eliminado=False)


class TodosManager(models.Manager):
    """Devuelve todos los registros, incluyendo eliminados."""
    def get_queryset(self):
        return super().get_queryset()


# ─── Modelo base ─────────────────────────────────────────────────────────────

class SoftDeleteModel(models.Model):
    """
    Modelo abstracto con soft-delete y timestamps de auditoría.
    Hereda de este en lugar de models.Model.
    """
    # Soft-delete
    eliminado      = models.BooleanField(default=False, db_index=True)
    eliminado_en   = models.DateTimeField(null=True, blank=True)
    eliminado_por  = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='%(class)s_eliminados',
    )

    # Auditoría (RF-24 / RNF-24)
    creado_en      = models.DateTimeField(auto_now_add=True)
    creado_por     = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='%(class)s_creados',
    )
    modificado_en  = models.DateTimeField(auto_now=True)
    modificado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='%(class)s_modificados',
    )

    objects = SoftDeleteManager()  # default: solo activos
    todos   = TodosManager()       # incluye eliminados

    class Meta:
        abstract = True

    def delete(self, usuario=None, *args, **kwargs):
        """Soft-delete: marca como eliminado en lugar de borrar."""
        self.eliminado     = True
        self.eliminado_en  = timezone.now()
        self.eliminado_por = usuario
        self.save(update_fields=['eliminado', 'eliminado_en', 'eliminado_por'])

    def restore(self):
        """Restaura un registro eliminado."""
        self.eliminado     = False
        self.eliminado_en  = None
        self.eliminado_por = None
        self.save(update_fields=['eliminado', 'eliminado_en', 'eliminado_por'])


# ─── Gasto ───────────────────────────────────────────────────────────────────

class Gasto(SoftDeleteModel):
    """
    Registro central de un gasto del viaje.
    Cubre RF-38, RF-39, RF-46, RF-47, RF-48
    y RNF-17 (validación de monto > 0).
    """

    CATEGORIAS = [
        ('transporte',      'Transporte 🚗'),
        ('alojamiento',     'Alojamiento 🏨'),
        ('alimentacion',    'Alimentación 🍕'),
        ('entretenimiento', 'Entretenimiento 🎟️'),
        ('compras',         'Compras 🛍️'),
        ('gasolina_casetas', 'Gasolina / Casetas ⛽'),  # RF-48
    ]

    METODOS_DIVISION = [
        ('equitativo',  'Equitativo'),       # RF-40: partes iguales
        ('porcentaje',  'Por porcentaje'),   # RF-40: % por persona
        ('monto_fijo',  'Monto fijo'),       # RF-40: cantidad específica
    ]

    # Relaciones
    viaje       = models.ForeignKey(
        'gestion_viajes.Viaje',
        on_delete=models.CASCADE,
        related_name='gastos_compartidos',
    )
    pagado_por  = models.ForeignKey(           # RF-38: quién pagó
        'gestion_viajes.Participante',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='gastos_pagados',
    )

    # Datos del gasto (RF-38)
    concepto    = models.CharField(max_length=150)
    monto       = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],  # RNF-17
    )
    categoria   = models.CharField(            # RF-39
        max_length=20,
        choices=CATEGORIAS,
    )
    fecha       = models.DateField()

    # División (RF-40)
    metodo_division = models.CharField(
        max_length=20,
        choices=METODOS_DIVISION,
        default='equitativo',
    )

    class Meta:
        ordering = ['-fecha', '-creado_en']
        verbose_name = 'Gasto'
        verbose_name_plural = 'Gastos'

    def __str__(self):
        return f"{self.concepto} (${self.monto}) — {self.viaje}"


# ─── GastoParticipante ───────────────────────────────────────────────────────

class GastoParticipante(SoftDeleteModel):
    """
    Participación individual en un gasto.
    Contiene cuánto pagó y cuánto debe cada persona.

    balance = monto_pagado - monto_deuda
      > 0  → le deben dinero
      < 0  → debe dinero
      = 0  → está a mano

    Cubre RF-40, RF-41 y RNF-18, RNF-19.
    """
    gasto       = models.ForeignKey(
        Gasto,
        on_delete=models.CASCADE,
        related_name='participaciones',
    )
    participante = models.ForeignKey(
        'gestion_viajes.Participante',
        on_delete=models.RESTRICT,
        related_name='participaciones_gastos',
    )

    # RNF-19: precisión de 4 decimales internamente, se redondea al mostrar
    monto_pagado = models.DecimalField(
        max_digits=10, decimal_places=4,
        default=Decimal('0.0000'),
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    monto_deuda = models.DecimalField(
        max_digits=10, decimal_places=4,
        default=Decimal('0.0000'),
        validators=[MinValueValidator(Decimal('0.00'))],
    )

    # Para división por porcentaje (RF-40)
    porcentaje  = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True,
        help_text='Solo aplica si método es por_porcentaje',
    )

    class Meta:
        unique_together = ('gasto', 'participante')
        verbose_name = 'Participación en gasto'
        verbose_name_plural = 'Participaciones en gastos'

    @property
    def balance(self) -> Decimal:
        return self.monto_pagado - self.monto_deuda

    def __str__(self):
        return (
            f"{self.participante} en '{self.gasto.concepto}': "
            f"pagó ${self.monto_pagado} / debe ${self.monto_deuda}"
        )


# ─── PresupuestoPersonal ─────────────────────────────────────────────────────

class PresupuestoPersonal(models.Model):
    """
    Presupuesto que cada integrante define para sí mismo en un viaje.
    Cubre RF-44, RF-45.
    """
    viaje        = models.ForeignKey(
        'gestion_viajes.Viaje',
        on_delete=models.CASCADE,
        related_name='presupuestos_personales',
    )
    participante = models.ForeignKey(
        'gestion_viajes.Participante',
        on_delete=models.CASCADE,
        related_name='presupuesto_personal',
    )
    monto        = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('viaje', 'participante')
        verbose_name = 'Presupuesto personal'
        verbose_name_plural = 'Presupuestos personales'

    def __str__(self):
        return f"{self.participante} — ${self.monto} en {self.viaje}"


# ─── Liquidacion ─────────────────────────────────────────────────────────────

class Liquidacion(models.Model):
    """
    Deuda calculada: X le debe Y una cantidad en un viaje.
    Se recalcula cada vez que hay un cambio en los gastos (RNF-16, RNF-21).
    El botón 'Marcar como pagado' solo lo puede presionar el acreedor (RF-43).
    """
    viaje     = models.ForeignKey(
        'gestion_viajes.Viaje',
        on_delete=models.CASCADE,
        related_name='liquidaciones',
    )
    deudor    = models.ForeignKey(
        'gestion_viajes.Participante',
        on_delete=models.CASCADE,
        related_name='deudas',
    )
    acreedor  = models.ForeignKey(
        'gestion_viajes.Participante',
        on_delete=models.CASCADE,
        related_name='acreencias',
    )
    monto     = models.DecimalField(max_digits=10, decimal_places=2)

    monto_pagado = models.DecimalField(
        max_digits=10, decimal_places=2,
        default=Decimal('0.00')
    )

    pagado    = models.BooleanField(default=False)
    pagado_en = models.DateTimeField(null=True, blank=True)

    @property
    def monto_pendiente(self):
        """Lo que falta por pagar."""
        return self.monto - self.monto_pagado

    def marcar_pagado(self):
        self.pagado    = True
        self.pagado_en = timezone.now()
        self.save(update_fields=['pagado', 'pagado_en'])

    # NUEVO: abono parcial o total
    def abonar(self, cantidad):
        from decimal import Decimal
        cantidad = Decimal(str(cantidad))
        if cantidad <= 0:
            raise ValueError("El abono debe ser mayor a cero.")
        if cantidad > self.monto_pendiente:
            raise ValueError(
                f"El abono (${cantidad}) supera lo pendiente (${self.monto_pendiente})."
            )
        self.monto_pagado += cantidad
        if self.monto_pagado >= self.monto:
            self.monto_pagado = self.monto
            self.pagado    = True
            self.pagado_en = timezone.now()
            self.save(update_fields=['monto_pagado', 'pagado', 'pagado_en'])
        else:
            self.save(update_fields=['monto_pagado'])


# ─── AuditoriaGasto ──────────────────────────────────────────────────────────

class AuditoriaGasto(models.Model):
    """
    Historial inmutable de cada operación sobre un gasto.
    Cubre RNF-24: fecha, hora, integrante y tipo de operación.
    Se usa gasto_id (int) en lugar de FK para conservar el historial
    incluso si el gasto es eliminado permanentemente.
    """

    ACCIONES = [
        ('creado',      'Creado'),
        ('modificado',  'Modificado'),
        ('eliminado',   'Eliminado'),
        ('restaurado',  'Restaurado'),
    ]

    gasto_id       = models.IntegerField(db_index=True)
    accion         = models.CharField(max_length=20, choices=ACCIONES)
    realizado_por  = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name='auditorias_gasto',
    )
    fecha          = models.DateTimeField(auto_now_add=True)

    # Snapshot antes/después para auditoría completa (RNF-24)
    detalle_antes  = models.JSONField(null=True, blank=True)
    detalle_despues = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Auditoría de gasto'
        verbose_name_plural = 'Auditoría de gastos'

    def __str__(self):
        return f"Gasto #{self.gasto_id} — {self.accion} ({self.fecha:%Y-%m-%d %H:%M})"