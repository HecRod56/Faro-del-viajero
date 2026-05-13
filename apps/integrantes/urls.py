from django.urls import path
from . import views

app_name = "integrantes"

# Base: http://127.0.0.1:8000/viajes/integrantes/

urlpatterns = [
    path("<int:id_viaje>/",                            views.lista_integrantes,          name="lista"),
    path("<int:id_viaje>/anadir/",                     views.anadir_integrante,          name="anadir"),
    path("<int:id_viaje>/abandonar/",                  views.abandonar_viaje,            name="abandonar_viaje"),
    path("<int:id_integrante>/eliminar/",              views.eliminar_integrante,        name="eliminar"),
    path("<int:id_integrante>/asignar-organizador/",   views.asignar_organizador,        name="asignar_organizador"),
    path("<int:id_viaje>/perfil/<int:id_usuario>/",    views.informacion_integrante,     name="informacion_integrante"),

    # Endpoint AJAX para cargar datos financieros de un integrante
    # antes de confirmar su eliminación en el modal
    path("<int:id_viaje>/gastos-info/<int:id_participante>/", views.detalle_gastos_integrante, name="gastos_info"),
]