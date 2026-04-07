"""
URL configuration for faro_del_viajero project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
"""

from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

from apps.autenticado.views import register, login_view, profile_view, forgot_password_view

# Creamos una vista falsa rapidísima solo para que el base.html no se rompa
def home_temporal(request):
    return HttpResponse("<h1>Inicio de Faro del Viajero</h1> <a href='/login/'>Ir al Login</a>")

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # CONEXIÓN DE RAIZ CON LA APP
    path('', include('core.urls')),
    path('', include('integrantes.urls')),
    
    # --- RUTAS EQUIPO 1 (GESTIÓN DE VIAJES) ---
    # Esto llama al archivo urls.py que crearemos dentro de tu app
    path('viajes/', include('apps.gestion_viajes.urls')), 
    
    # --- RUTAS DE OTROS EQUIPOS ---
    path('', home_temporal, name='home'),
    path('registro/', register, name='register'),
    path('login/', login_view, name='login'),
    path('recuperar/', forgot_password_view, name='forgot_password'), 
    path('perfil/', profile_view, name='profile'),
]