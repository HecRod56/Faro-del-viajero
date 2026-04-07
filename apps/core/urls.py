from django.urls import path
from . import views
from apps.autenticado.views import register

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', register, name='register'),
]