from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, get_user_model
from .models import CustomUser
from django.contrib import messages
from django.http import JsonResponse  # <-- NUEVO IMPORT NECESARIO

User = get_user_model()

# Create your views here.

def register(request):
    if request.method == 'POST':
        # 1. Recibe los datos del formulario
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        phone = request.POST.get('phone')
        dob = request.POST.get('dob')

        # 2. Crea el usuario en la base de datos
        if email and password:
            user = CustomUser.objects.create_user(username=email, email=email, password=password, first_name=full_name)
            user.phone = phone 
            user.date_of_birth = dob
            user.save()
            
            # NUEVO: Iniciamos sesión automáticamente después de registrarse
            login(request, user)
            messages.success(request, "¡Cuenta creada con éxito! Bienvenido.")
            
            # NUEVO: Redirigimos al perfil
            return redirect('profile') 
    
    return render(request, 'autenticado/register.html')

def login_view(request):
    if request.method == 'POST':
        correo = request.POST.get('email')
        contra = request.POST.get('password')

        user_exists = CustomUser.objects.filter(email=correo).exists()
        
        if not user_exists:
            messages.error(request, "Usuario inexistente. Por favor, verifica tu correo o regístrate.")
        else:
            user = authenticate(request, username=correo, password=contra)        
            
            if user is not None:
                login(request, user)
                # NUEVO: Redirigimos al perfil en lugar del home
                return redirect('profile') 
            else:
                messages.error(request, "Contraseña incorrecta. Inténtalo de nuevo.")
            
    return render(request, 'autenticado/login.html')

def profile_view(request):
    return render(request, 'autenticado/profile.html')

def forgot_password_view(request):
    return render(request, 'autenticado/forgot_password.html')


# ==========================================
# VISTAS DE VALIDACIÓN EN TIEMPO REAL (AJAX)
# ==========================================

def validar_correo(request):
    """Verifica si el correo ya existe en CustomUser"""
    email = request.GET.get('email', None)
    existe = False
    
    if email:
        existe = CustomUser.objects.filter(email=email).exists()
        
    return JsonResponse({'existe': existe})

def validar_telefono(request):
    """Verifica si el teléfono ya existe en CustomUser"""
    phone = request.GET.get('phone', None)
    existe = False
    
    if phone:
        existe = CustomUser.objects.filter(phone=phone).exists()
        
    return JsonResponse({'existe': existe})