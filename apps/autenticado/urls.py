from django.urls import path
from . import views  # Importamos las vistas de esta misma app

urlpatterns = [
    path('registro/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('recuperar/', views.forgot_password_view, name='forgot_password'),
    path('perfil/', views.profile_view, name='profile'),
    # NUEVAS RUTAS PARA VALIDACIÓN
    path('api/validar-correo/', views.validar_correo, name='validar_correo'),
    path('api/validar-telefono/', views.validar_telefono, name='validar_telefono'),
]