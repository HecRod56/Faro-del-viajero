from django.contrib.auth.tokens import PasswordResetTokenGenerator

class TokenVerificacionCuenta(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        # Esto asegura que si el usuario cambia algo, el token viejo expire
        return str(user.pk) + str(timestamp) + str(user.is_active)

token_activacion = TokenVerificacionCuenta()