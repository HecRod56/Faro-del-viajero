"""
URL configuration for faro_del_viajero project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
"""

from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

# Creamos una vista falsa rapidísima solo para que el base.html no se rompa
def home_temporal(request):
    return HttpResponse("<h1>Inicio de Faro del Viajero</h1> <a href='/login/'>Ir al Login</a>")

urlpatterns = [
    path('admin/', admin.site.urls),
    #CONEXIÓN DE RAIZ CON LA APP
    #path('', home_temporal, name='home'),  # <-- ¡ESTO SALVA AL base.html!
    path('', include('core.urls')),
    path('', include('integrantes.urls')),
    path('', include('apps.autenticado.urls')),
    path('viajes/', include('apps.gestion_viajes.urls')),
    path('', include('actividades.urls')),
    path('', include('chat.urls')),
    path('', include('galeria.urls')),
]
