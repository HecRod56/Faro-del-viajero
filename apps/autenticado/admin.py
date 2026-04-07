
# Register your models here.
from django.contrib import admin
from .models import CustomUser

# Registramos el modelo para verlo en el panel
admin.site.register(CustomUser)