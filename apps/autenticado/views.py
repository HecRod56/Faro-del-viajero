from django.shortcuts import render

# Create your views here.

def register_view(request):
    return render(request, 'autenticado/register.html')

def login_view(request):
    return render(request, 'autenticado/login.html')

def profile_view(request):
    return render(request, 'autenticado/profile.html')

def forgot_password_view(request):
    return render(request, 'autenticado/forgot_password.html')