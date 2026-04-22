from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models

class CustomUser(AbstractUser):
    # Identificador principal
    email = models.EmailField(unique=True)
    
    # Campos adicionales
    phone = models.CharField(max_length=15, blank=True, null=True)
    dob = models.DateField(null=True, blank=True, verbose_name="Fecha de nacimiento")
    
    CURRENCY_CHOICES = [
        ('MXN', 'Peso Mexicano'),
        ('USD', 'Dólar Estadounidense'),
        ('EUR', 'Euro'),
        ('COP', 'Peso Colombiano'),
    ]
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='MXN')
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  # username sigue siendo requerido por AbstractUser, aunque no lo uses para login

    # Solución al choque de nombres (Error E304)
    groups = models.ManyToManyField(
        Group,
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name="custom_user_groups",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="custom_user_permissions",
    )

    def __str__(self):
        return self.email