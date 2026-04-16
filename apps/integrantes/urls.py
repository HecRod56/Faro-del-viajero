from django.urls import path
from . import views

app_name = 'integrantes'

urlpatterns = [
    path('<int:id_viaje>/',                         views.lista_integrantes,   name='lista'),
    path('<int:id_viaje>/anadir/',                  views.anadir_integrante,   name='anadir'),
    path('<int:id_viaje>/abandonar/',               views.abandonar_viaje,     name='abandonar_viaje'),
    path('<int:id_integrante>/eliminar/',            views.eliminar_integrante, name='eliminar'),
    path('<int:id_integrante>/asignar-organizador/', views.asignar_organizador, name='asignar_organizador'),
]