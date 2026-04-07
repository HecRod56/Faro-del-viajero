from django.urls import path
from . import views

urlpatterns = [
    path('inicio/', views.pagina_inicio, name='p_inicio'),
    path('crear_viaje/', views.pagina_crear_viaje, name='p_crear_viaje'),
    path('ver_mis_viajes/', views.pagina_ver_mis_viajes, name='p_ver_mis_viajes'), 
    path('viajes_planeados/', views.pagina_viajes_planeados, name='p_viajes_planeados'),
]