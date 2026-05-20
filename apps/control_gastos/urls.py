from django.urls import path
from . import views

app_name = 'gastos'

urlpatterns = [
    path('<int:viaje_id>/',                               views.resumen_grupal,        name='resumen'),
    path('<int:viaje_id>/crear/',                         views.crear_gasto_view,      name='crear'),
    path('<int:viaje_id>/editar/<int:gasto_id>/',         views.modificar_gasto_view,  name='modificar'),
    path('<int:viaje_id>/eliminar/<int:gasto_id>/',       views.eliminar_gasto_view,   name='eliminar'),
    path('<int:viaje_id>/pagar/<int:liquidacion_id>/',    views.marcar_pagada_view,    name='marcar_pagada'),
    path('<int:viaje_id>/enviar-transporte/', views.enviar_gasto_transporte, name='enviar_transporte'),
]
