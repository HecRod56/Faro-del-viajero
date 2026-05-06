from django.urls import path
from . import views

app_name = 'actividades'

urlpatterns = [
    # Rutas para ver información
    path('viaje/<int:viaje_id>/', views.lista_actividades, name='lista'),
    path('detalle/<int:actividad_id>/', views.detalle_actividad, name='detalle'),
    
    # Rutas para gestionar actividades
    path('proponer/<int:viaje_id>/', views.proponer_actividad, name='proponer_actividad'),
    path('actividad/editar/<int:id>/', views.editar_actividad, name='editar_actividad'),
    path('eliminar/<int:actividad_id>/', views.eliminar_actividad, name='eliminar'),
    path('actividad/<int:actividad_id>/', views.detalle_actividad, name='detalle_actividad'),
    
    # Ruta oculta para procesar votos
    path('votar/<int:actividad_id>/', views.votar_actividad, name='votar'),
]