from django.shortcuts import get_object_or_404
from .models import Viaje

class ViajeContextMixin:
    """
    Mixin para vistas de módulos secundarios (integrantes, chat, etc.)
    Garantiza que el objeto viaje esté disponible en self.viaje.
    """
    def dispatch(self, request, *args, **kwargs):
        # Captura el viaje_id de la URL y lo guarda en la instancia de la vista
        self.viaje = get_object_or_404(Viaje, pk=kwargs.get('viaje_id'))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Esto es el "doble seguro" que mencionó tu líder
        ctx['viaje_actual'] = self.viaje
        return ctx