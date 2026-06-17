from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, get_user_model, update_session_auth_hash
from django.contrib import messages
from django.http import JsonResponse
from apps.gestion_viajes.models import Viaje
from datetime import datetime
from .forms import CustomPasswordChangeForm
from .tokens import token_activacion


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
            user = User.objects.create_user(username=email, email=email, password=password, first_name=full_name)
            user.phone = phone 
            user.dob = dob
            
            # Bloqueamos la cuenta temporalmente hasta que use el link del correo
            user.is_active = False 
            user.save()
            
            # Generamos el token seguro usando tu archivo tokens.py
            dominio = get_current_site(request).domain
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = token_activacion.make_token(user)
            
            # Armamos el enlace de verificación
            link_verificacion = f"http://{dominio}/activar/{uid}/{token}/"
            
            # Armamos el correo en HTML
            asunto = 'Confirma tu cuenta - Faro del Viajero'
            contexto = {
                'user': user,
                'link': link_verificacion
            }
            mensaje_html = render_to_string('autenticado/correo_verificacion.html', contexto)
            
            # Enviamos por Brevo usando tu configuración de SMTP
            send_mail(
                subject=asunto,
                message='', # Vacío porque es HTML
                from_email=None, # Django jala el DEFAULT_FROM_EMAIL de tu settings
                recipient_list=[user.email],
                html_message=mensaje_html,
                fail_silently=False,
            )
            
            # En lugar de redirigir a viajes, lo mandamos a avisarle que cheque su bandeja
            return render(request, 'autenticado/revisa_correo.html', {'email': user.email})
    
    return render(request, 'autenticado/register.html')

def activar_cuenta(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and token_activacion.check_token(user, token):
        user.is_active = True  # ¡Ya es un usuario oficial!
        user.save()
        messages.success(request, "¡Tu cuenta ha sido verificada! Ya puedes iniciar sesión.")
        return render(request, 'autenticado/activacion_exitosa.html')
    else:
        return render(request, 'autenticado/activacion_fallida.html')

def login_view(request):
    if request.method == 'POST':
        correo = request.POST.get('email')
        contra = request.POST.get('password')

        user_exists = User.objects.filter(email=correo).exists()
        
        if not user_exists:
            messages.error(request, "Usuario inexistente. Por favor, verifica tu correo o regístrate.")
        else:
            user = authenticate(request, username=correo, password=contra)        
            
            if user is not None:
                login(request, user)
                # NUEVO: Redirigimos a los vijaes del usuario después de iniciar sesión
                return redirect('/viajes/ver_mis_viajes/') 
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
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "¡Contraseña actualizada!")
            return redirect('profile')
        else:
            messages.error(request, "Hay un error en los datos ingresados. Revisa las advertencias abajo.")
    else:
        form = CustomPasswordChangeForm(user=request.user)
    return render(request, 'autenticado/cambiar_password.html', {'form': form})

# ==========================================
# VISTAS DE VALIDACIÓN EN TIEMPO REAL (AJAX)
# ==========================================

def validar_correo(request):
    """Verifica si el correo ya existe en CustomUser"""
    email = request.GET.get('email', None)
    existe = False
    
    if email:
        existe = User.objects.filter(email=email).exists()
        
    return JsonResponse({'existe': existe})

def validar_telefono(request):
    """Verifica si el teléfono ya existe en CustomUser"""
    phone = request.GET.get('phone', None)
    existe = False
    
    if phone:
        existe = User.objects.filter(phone=phone).exists()
        
    return JsonResponse({'existe': existe})