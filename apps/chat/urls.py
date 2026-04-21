from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.lista_chats, name='lista_chats'),
    path('<int:viaje_id>/', views.chat_viaje, name='chat_viaje'),
    path('<int:viaje_id>/integrantes/', views.chat_integrantes, name='chat_integrantes'),
    path('<int:viaje_id>/enviar/', views.enviar_mensaje, name='enviar_mensaje'),
    path('<int:viaje_id>/abandonar/', views.abandonar_viaje, name='abandonar_viaje'),
]
