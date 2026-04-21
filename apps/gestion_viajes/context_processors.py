from .models import Viaje

def viaje_actual(request):
    try:
        # resolver_match puede ser None en requests con error (404, 500)
        if not request.resolver_match:
            return {'viaje_actual': None}
        
        viaje_id = request.resolver_match.kwargs.get('viaje_id')
        if viaje_id:
            return {'viaje_actual': Viaje.objects.get(pk=viaje_id)}
    except (Viaje.DoesNotExist, AttributeError):
        pass
    return {'viaje_actual': None}