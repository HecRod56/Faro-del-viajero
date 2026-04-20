from django.urls import path
from . import views

app_name = 'actividades'

urlpatterns = [
    path('proponer/<int:viaje_id>/', views.proponer_actividad, name='proponer_actividad'),
    path('editar/', views.editar_actividad, name='editar_actividad'),
]

