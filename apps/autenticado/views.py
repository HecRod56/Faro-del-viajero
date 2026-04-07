from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from .models import CustomUser
from django.contrib import messages

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
            messages.success(request, "¡Cuenta creada con éxito!")
            return redirect('login')
    
    return render(request, 'autenticado/register.html')

def login_view(request):
    if request.method == 'POST':
        # 1. Saca los datos del form
        correo = request.POST.get('email')
        contra = request.POST.get('password')

        # 2. Django busca si el usuario existe y la contraseña es correcta
        # Como se uso el correo como username en el registro anterior:
        user = authenticate(request, username=correo, password=contra)

        if user is not None:
            # SI EXISTE: Iniciamos sesión y mandamos al home
            login(request, user)
            return redirect('core:home')
        else:
            # NO EXISTE o datos mal: Mandamos error
            messages.error(request, "Correo o contraseña incorrectos.")
            
    return render(request, 'autenticado/login.html')

def profile_view(request):
    return render(request, 'autenticado/profile.html')

def forgot_password_view(request):
    return render(request, 'autenticado/forgot_password.html')