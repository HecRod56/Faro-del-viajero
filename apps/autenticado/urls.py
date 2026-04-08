from django.urls import path
from . import views  # Importamos las vistas de esta misma app

urlpatterns = [
    path('registro/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('recuperar/', views.forgot_password_view, name='forgot_password'),
    path('perfil/', views.profile_view, name='profile'),
]