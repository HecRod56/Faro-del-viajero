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
from apps.gestion_viajes.views import pagina_inicio
from django.shortcuts import render
from django.http import HttpResponse

def home_temporal(request): #pantalla a conectar en el futuro
    return render(request, 'gestion_viajes/pagina_inicio.html')

def profile_temp(request): #pantalla a conectar en el futuro
    return render(request, 'gestion_viajes/pagina_inicio.html')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_temporal, name='home'),
    path('',profile_temp, name='profile'),
    path('', include('core.urls')),
    path('pagina_inicio/', pagina_inicio, name='pagina_inicio'),
]
