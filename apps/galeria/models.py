from django.db import models

class FotoGaleria(models.Model):
    """
    Representa una fotografía subida a la galería de un viaje.

    Args:
        viaje_id (int): ID del viaje al que pertenece la foto.
        usuario_id (int): ID del usuario que subió la foto.
        archivo (ImageField): Archivo de imagen almacenado.
        nombre_archivo (str): Nombre original del archivo.
        fecha_subida (date): Fecha en que se subió la imagen.
        hora_subida (time): Hora en que se subió la imagen.

    Returns:
        str: Nombre del archivo al representar el objeto.
    """
    viaje_id       = models.IntegerField()
    usuario_id     = models.IntegerField()
    nombre_usuario = models.CharField(max_length=150)
    archivo        = models.ImageField(upload_to='galeria/%Y/%m/%d/')
    nombre_archivo = models.CharField(max_length=255)
    fecha_subida   = models.DateField(auto_now_add=True)
    hora_subida    = models.TimeField(auto_now_add=True)

    class Meta:
        db_table      = 'foto_galeria'
        ordering      = ['-fecha_subida', '-hora_subida']
        verbose_name  = 'Foto de galería'
        verbose_name_plural = 'Fotos de galería'

    def __str__(self):
        return self.nombre_archivo