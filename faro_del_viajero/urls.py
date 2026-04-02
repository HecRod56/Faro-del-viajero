"""
URL configuration for faro_del_viajero project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from apps.gestion_viajes.views import pagina_inicio, pagina_crear_viaje, pagina_ver_mis_viajes, pagina_viajes_planeados
from django.shortcuts import render
from django.http import HttpResponse

def home_temporal(request): #pantalla a conectar en el futuro
    return render(request, 'gestion_viajes/inicio.html')

def profile_temp(request): #pantalla a conectar en el futuro
    return render(request, 'gestion_viajes/inicio.html')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_temporal, name='home'),
    path('',profile_temp, name='profile'),
    path('', include('core.urls')),
    path('inicio/', pagina_inicio, name='p_inicio'),
    path('crear_viaje/', pagina_crear_viaje, name='p_crear_viaje'),
    path('ver_mis_viajes/', pagina_ver_mis_viajes,name='p_ver_mis_viajes'), 
    path('viajes_planeados/', pagina_viajes_planeados, name='p_viajes_planeados'),
]
