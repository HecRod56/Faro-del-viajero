def datos_viaje(viaje):
    cupos_ocupados = viaje.participantes.count()
    cupos_totales = viaje.capacidad_max

    return {
        "id": viaje.id,
        "nombre": viaje.nombre,
        "estado": viaje.estado,
        "cupos_ocupados": cupos_ocupados,
        "cupos_totales": cupos_totales,
        "cupos_disponibles": cupos_totales - cupos_ocupados,
        "imagen": viaje.imagen_destino.url if viaje.imagen_destino else None
    }