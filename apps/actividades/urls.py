from django.urls import path
from . import views

app_name = 'actividades'

urlpatterns = [
    path('proponer/<int:viaje_id>/', views.proponer_actividad, name='proponer_actividad'),
    path('editar/', views.editar_actividad, name='editar_actividad'),
    # Ruta para ver las actividades de un viaje específico
    path('viaje/<int:viaje_id>/', views.lista_actividades, name='lista'),
    # Ruta oculta para procesar el formulario de voto
    path('votar/<int:actividad_id>/', views.votar_actividad, name='votar'),
    # Ruta para eliminar una actividad
    path('eliminar/<int:actividad_id>/', views.eliminar_actividad, name='eliminar'),
    # Ruta para ver el detalle de una actividad
    path('detalle/<int:actividad_id>/', views.detalle_actividad, name='detalle'),
]

