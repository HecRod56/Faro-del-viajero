from django.urls import path
from . import views

app_name = "busqueda"

urlpatterns = [
    path("viaje/<int:viaje_id>/destinos/", views.p_destinos, name="p_destinos"),
    path("viaje/<int:viaje_id>/agregar-actividad/", views.agregar_actividad, name="agregar_actividad"),
    path('viaje/<int:viaje_id>/destino/detalle/',   views.detalle_lugar_view,  name='detalle_lugar'),
]
