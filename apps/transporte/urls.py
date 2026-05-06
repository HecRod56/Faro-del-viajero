from django.urls import path
from . import views

app_name = 'transporte'

urlpatterns = [
    
    path('transporte/<int:viaje_id>/', views.transporte_principal, name='principal'),
    path('transporte/<int:viaje_id>/registrar/', views.registrar_trayecto, name='registrar_trayecto'),
    path('transporte/<int:viaje_id>/ruta-interna/', views.buscar_ruta_interna, name='buscar_ruta_interna'),
    path('transporte/<int:viaje_id>/eliminar/<int:trayecto_id>/', views.eliminar_trayecto, name='eliminar_trayecto'),
]