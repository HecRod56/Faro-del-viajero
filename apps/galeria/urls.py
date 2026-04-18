from django.urls import path
from . import views

app_name = 'galeria'

urlpatterns = [
    path('mock/viaje/<int:id_viaje>/galeria/',              views.galeria_mock,      name='galeria_mock'),
    path('mock/viaje/<int:id_viaje>/galeria/subir/',        views.subir_foto_mock,   name='subir_foto'),
    path('mock/galeria/<int:id_foto>/eliminar/',            views.eliminar_foto_mock, name='eliminar_foto'),
]

