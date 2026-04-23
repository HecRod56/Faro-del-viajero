from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, get_user_model
from .models import CustomUser
from django.contrib import messages
from django.http import JsonResponse  # <-- NUEVO IMPORT NECESARIO
from apps.gestion_viajes.models import Viaje
from datetime import datetime
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm


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

@login_required
def ver_perfil(request):
    user = request.user
    
    if request.method == 'POST':
        # Guardamos los cambios en el modelo CustomUser
        user.first_name = request.POST.get('full_name')
        user.phone = request.POST.get('phone')
        
        dob_raw = request.POST.get('dob') # Recibes "21/04/2026" del input text
        
        if dob_raw:
            try:
                # TRADUCCIÓN: Pasamos de texto "dd/mm/aaaa" a objeto DATE de Python
                # Esto es lo que PostgreSQL (el campo dob date) sí acepta
                user.dob = datetime.strptime(dob_raw, '%d/%m/%Y').date()
                messages.success(request, "¡Fecha guardada!")
            except ValueError:
                messages.error(request, "Formato de fecha inválido (usa DD/MM/AAAA).")
        
        user.save() # Aquí se manda todo a la BD
        return redirect('profile')

    #return render(request, 'autenticado/profile.html', {'user': user})

    # Filtro correcto atravesando la tabla intermedia de tu imagen
    from apps.gestion_viajes.models import Viaje
    viajes_activos = Viaje.objects.filter(participantes__usuario=user).distinct()
    
    context = {
        'user': user,
        'viajes': viajes_activos
    }
    
    return render(request, 'autenticado/profile.html', context)

def forgot_password_view(request):
    return render(request, 'autenticado/forgot_password.html')

@login_required
def cambiar_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "¡Contraseña actualizada!")
            return redirect('profile')
    else:
        form = PasswordChangeForm(user=request.user)
    return render(request, 'autenticado/cambiar_password.html', {'form': form})

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