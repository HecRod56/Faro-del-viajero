from django.urls import path
from . import views

app_name = 'transporte'

urlpatterns = [
    path('transporte/', views.transporte_principal, name='principal'),
    path('transporte/registrar/', views.registrar_trayecto, name='registrar_trayecto'),
    path('transporte/buscar-ruta/', views.buscar_ruta_interna, name='buscar_ruta_interna'),
    path('transporte/eliminar/<int:trayecto_id>/', views.eliminar_trayecto, name='eliminar_trayecto'),
]