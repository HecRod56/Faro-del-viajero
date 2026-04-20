from django.urls import path
from . import views

urlpatterns = [
    path('inicio/', views.pagina_inicio, name='p_inicio'),
    path('crear_viaje/', views.pagina_crear_viaje, name='p_crear_viaje'),
    path('ver_mis_viajes/', views.pagina_ver_mis_viajes, name='p_ver_mis_viajes'), 
    path('detalle/<int:viaje_id>/', views.pagina_detalle_viaje, name='p_detalle_viaje'),    
    path('viajes_planeados/', views.pagina_viajes_planeados, name='p_viajes_planeados'),
    path('editar/<int:viaje_id>/', views.pagina_editar_viaje, name='p_editar_viaje'),
    path('eliminar/<int:viaje_id>/', views.eliminar_viaje, name='p_eliminar_viaje'),
    path('detalle/<int:viaje_id>/gasto/', views.registrar_gasto, name='p_registrar_gasto'),
    path('gasto/<int:gasto_id>/eliminar/', views.eliminar_gasto, name='p_eliminar_gasto'),
    path('detalle/<int:viaje_id>/unirse/', views.añadir_participante, name='p_unirse_viaje'),
]