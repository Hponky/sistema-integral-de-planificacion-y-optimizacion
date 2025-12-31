"""
Utilidades para el servicio de planificación.
"""

def compute_earliest_start(last_end_min):
    """
    Dado el tiempo de fin de un turno, calcula el tiempo de inicio válido más temprano
    para el turno del día siguiente (regla de 12h de descanso).
    O(1) operation.
    """
    if last_end_min is None:
        return 0
    
    # Tiempo hasta medianoche + 12 horas - 24 horas (ajuste día siguiente)
    rest_needed = 12 * 60
    time_until_midnight = 24 * 60 - last_end_min
    
    if time_until_midnight >= rest_needed:
        # Descanso satisfecho al final del día, puede empezar a las 0:00
        return 0
    else:
        # Debe esperar al día siguiente
        return rest_needed - time_until_midnight
