from django.urls import path
from . import views

app_name = 'integrantes'

urlpatterns = [
    path('mock/viaje/<int:id_viaje>/integrantes/', views.integrantes_viaje_mock, name='mock_integrantes'),
    path('viaje/<int:id_viaje>/integrantes/', views.integrantes_viaje, name='integrantes_viaje'),
]