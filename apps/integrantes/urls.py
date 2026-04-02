from django.urls import path
from . import views

app_name = 'integrantes'

urlpatterns = [
    path('mock/viaje/<int:id_viaje>/integrantes/', views.integrantes_viaje_mock, name='mock_integrantes'),
    path('mock/viaje/<int:id_viaje>/integrantes/como/<int:usuario_id>/', views.integrantes_viaje_mock, name='mock_integrantes_como'),
    path('viaje/<int:id_viaje>/integrantes/', views.integrantes_viaje, name='integrantes_viaje'),
    path("viajes/integrantes/<int:id_integrante>/eliminar/", views.eliminar_integrante_mock, name="eliminar_integrante_mock"),
    path("mock/viaje/<int:id_viaje>/integrantes/anadir/", views.anadir_integrante_mock, name="anadir_integrante_mock"),
]