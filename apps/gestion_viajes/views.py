from django.shortcuts import render

# Create your views here.
def pagina_inicio(request): #Se renderiza la pagina de inicio
    return render(request, 'gestion_viajes/inicio.html')

def pagina_crear_viaje(request): #Se renderiza el formulario para crear un viaje 
    return render(request,'gestion_viajes/crear_viaje.html')

def pagina_ver_mis_viajes(request): 
    return render(request,'gestion_viajes/ver_mis_viajes.html')

def pagina_viajes_planeados(request): 
    return render(request,'gestion_viajes/viajes_planeados.html')