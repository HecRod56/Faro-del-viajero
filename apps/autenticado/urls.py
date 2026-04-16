from django.urls import path
from django.contrib.auth import views as auth_views
from . import views  # Importamos las vistas de esta misma app
from django.urls import reverse_lazy

urlpatterns = [
    path('registro/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('perfil/', views.profile_view, name='profile'),
    # NUEVAS RUTAS PARA VALIDACIÓN
    path('api/validar-correo/', views.validar_correo, name='validar_correo'),
    path('api/validar-telefono/', views.validar_telefono, name='validar_telefono'),
    #RUTAS RECUPERACION CONTRASEÑA
    path('recuperar/', auth_views.PasswordResetView.as_view(
        template_name='autenticado/forgot_password.html',
        email_template_name='autenticado/password_reset_email.html',
        subject_template_name='autenticado/password_reset_subject.txt', # Para el asunto
        success_url=reverse_lazy('password_reset_done')
    ), name='forgot_password'),
    path('recuperar/enviado/', auth_views.PasswordResetDoneView.as_view(
        template_name='autenticado/forgot_password.html'
    ), name='password_reset_done'),
    path('restablecer/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='autenticado/password_reset_form.html',
        success_url='/login/' # Al terminar, lo mandamos al login
    ), name='password_reset_confirm'),
]