from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from django.core.exceptions import ValidationError

class CustomPasswordChangeForm(PasswordChangeForm):
    def clean(self):
        # 1. Dejamos que Django valide que las contraseñas nuevas coincidan entre sí
        cleaned_data = super().clean()
        
        # 2. Extraemos los valores ya "limpios"
        old_password = cleaned_data.get("old_password")
        new_password1 = cleaned_data.get("new_password1")

        # 3. Solo comparamos si ambos campos pasaron las validaciones previas
        if old_password and new_password1:
            if old_password == new_password1:
                raise ValidationError(
                    "La nueva contraseña no puede ser igual a la anterior. ¡Intenta con una diferente!"
                )
        
        return cleaned_data