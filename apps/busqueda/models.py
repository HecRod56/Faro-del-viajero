from django.db import models


class DestinoCache(models.Model):
    destino   = models.CharField(max_length=100)
    categoria = models.CharField(max_length=50)
    datos     = models.JSONField()
    fecha     = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('destino', 'categoria')

    def __str__(self):
        return f"{self.destino} — {self.categoria}"
