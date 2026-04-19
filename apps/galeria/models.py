from django.db import models
from django.conf import settings
from apps.gestion_viajes.models import Viaje, Participante
from cloudinary.models import CloudinaryField


def ruta_imagen_galeria(instance, filename):
    """
    Guarda las imágenes en: galeria/viaje_<id>/<filename>
    Ej: galeria/viaje_3/foto_cancun.jpg
    """
    return f"galeria/viaje_{instance.viaje.id}/{filename}"


class ImagenGaleria(models.Model):
    # ── Relaciones ──────────────────────────────────────────
    viaje = models.ForeignKey(
        Viaje,
        on_delete=models.CASCADE,
        related_name="imagenes_galeria",
        help_text="Viaje al que pertenece esta imagen.",
    )
    subida_por = models.ForeignKey(
        # RF-66, RF-67, RNF-25: guardar quién subió la foto
        # Apuntamos a Participante (no directo a CustomUser) para
        # garantizar RNF-27: solo integrantes del viaje pueden subir.
        Participante,
        on_delete=models.SET_NULL,
        null=True,
        related_name="imagenes_subidas",
        help_text="Participante del viaje que subió la imagen.",
    )

    # ── Archivo ─────────────────────────────────────────────
    imagen = CloudinaryField(
        # RNF-28: JPEG y PNG los maneja ImageField nativamente.
        # HEIC requiere pillow-heif instalado en el entorno;
        # la validación de formato se hace en el validator de abajo.
        'image',                                        
        folder='galeria/',                              # carpeta en Cloudinary
        resource_type='image',
        help_text="Archivo de imagen (JPEG, PNG o HEIC).",
    )

    # ── Fechas ──────────────────────────────────────────────
    fecha_subida = models.DateTimeField(
        # RNF-25: fecha y hora de registro automática
        auto_now_add=True,
        help_text="Fecha y hora en que se subió la imagen al sistema.",
    )
    fecha_tomada = models.DateField(
        # RF-66: agrupar por fecha en que se tomó la foto,
        # no por cuándo se subió. Opcional: el usuario puede no saber la fecha exacta.
        null=True,
        blank=True,
        help_text="Fecha en que se tomó la fotografía (para agrupar en la galería).",
    )

    # ── Metadatos opcionales ─────────────────────────────────
    descripcion = models.CharField(
        max_length=255,
        blank=True,
        help_text="Pie de foto opcional.",
    )

    class Meta:
        ordering = ["-fecha_tomada", "-fecha_subida"]
        verbose_name = "Imagen de galería"
        verbose_name_plural = "Imágenes de galería"

    def __str__(self):
        autor = self.subida_por.usuario if self.subida_por else "Usuario eliminado"
        return f"Foto de {autor} en {self.viaje.nombre} ({self.fecha_subida:%Y-%m-%d})"

    # ── Helpers de permisos (RF-68) ──────────────────────────
    def puede_eliminar(self, usuario):
        """
        Devuelve True si el usuario puede eliminar esta imagen:
        - Es quien la subió, O
        - Es organizador del viaje.
        Úsalo en la view: imagen.puede_eliminar(request.user)
        """
        if self.subida_por and self.subida_por.usuario == usuario:
            return True

        return Participante.objects.filter(
            viaje=self.viaje,
            usuario=usuario,
            rol="organizador",
        ).exists()