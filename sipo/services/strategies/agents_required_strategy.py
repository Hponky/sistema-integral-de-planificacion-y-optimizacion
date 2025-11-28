"""
Implementación de la estrategia de cálculo Agents Required para el patrón Strategy.
Calcula el número de agentes requeridos para alcanzar un SLA objetivo.
"""

import math
from .base_strategy import CalculationStrategy
from .sla_strategy import SLAStrategy


class AgentsRequiredStrategy(CalculationStrategy):
    """
    Estrategia de cálculo para el número de agentes requeridos.
    Calcula el número mínimo de agentes necesarios para alcanzar un SLA objetivo
    basado en el volumen de llamadas, AHT y tiempo de servicio objetivo.
    """
    
    def calculate(self, target_sla, service_time, calls_per_hour, aht, **kwargs):
        """
        Calcula el número de agentes requeridos usando búsqueda binaria.
        
        Args:
            target_sla (float): SLA objetivo (valor entre 0 y 1)
            service_time (float): Tiempo objetivo de servicio en segundos
            calls_per_hour (float): Volumen de llamadas por hora
            aht (float): Tiempo promedio de manejo de llamada (AHT) en segundos
            **kwargs: Argumentos adicionales no utilizados en esta estrategia
        
        Returns:
            int: Número mínimo de agentes requeridos
        """
        is_valid, error_msg = self.validate_parameters(target_sla, service_time, calls_per_hour, aht)
        if not is_valid:
            raise ValueError(error_msg)
        
        if calls_per_hour == 0:
            return 1
        
        # Si el SLA objetivo es 0 o negativo, no se necesitan agentes
        if target_sla <= 0:
            return 1
        
        # Búsqueda binaria para encontrar el número mínimo de agentes
        # que alcanza el SLA objetivo
        min_agents = 1
        max_agents = max(100, int(calls_per_hour * aht / 3600) * 2)  # Límite superior razonable
        
        sla_strategy = SLAStrategy()
        
        # Primero verificamos si el máximo alcanza el SLA
        current_sla = sla_strategy.calculate(max_agents, service_time, calls_per_hour, aht)
        if current_sla < target_sla:
            # Si ni siquiera con el máximo alcanzamos el SLA, devolvemos el máximo
            return max_agents
        
        # Búsqueda binaria para encontrar el mínimo
        while min_agents < max_agents:
            mid_agents = (min_agents + max_agents) // 2
            current_sla = sla_strategy.calculate(mid_agents, service_time, calls_per_hour, aht)
            
            if current_sla >= target_sla:
                max_agents = mid_agents
            else:
                min_agents = mid_agents + 1
        
        return max_agents
    
    def get_name(self):
        """
        Obtiene el nombre descriptivo de esta estrategia.
        
        Returns:
            str: Nombre de la estrategia
        """
        return "Agents Required - Agentes Requeridos"
    
    def validate_parameters(self, target_sla, service_time, calls_per_hour, aht):
        """
        Valida los parámetros de entrada para el cálculo de agentes requeridos.
        
        Args:
            target_sla (float): SLA objetivo a validar
            service_time (float): Tiempo objetivo de servicio a validar
            calls_per_hour (float): Volumen de llamadas por hora a validar
            aht (float): Tiempo promedio de manejo a validar
        
        Returns:
            tuple: (bool, str) donde el primer elemento indica si los parámetros son válidos,
                   y el segundo elemento contiene un mensaje de error si no son válidos
        """
        if not all(isinstance(param, (int, float)) for param in [target_sla, service_time, calls_per_hour, aht]):
            return False, "Todos los parámetros deben ser numéricos"
        
        if target_sla < 0 or target_sla > 1:
            return False, "El SLA objetivo debe estar entre 0 y 1"
        
        if aht < 0:
            return False, "El AHT no puede ser negativo"
        
        # Permitir AHT = 0 con un valor predeterminado
        if aht == 0:
            aht = 180  # Valor predeterminado de 3 minutos (180 segundos)
        
        if calls_per_hour < 0:
            return False, "El volumen de llamadas por hora no puede ser negativo"
        
        if service_time <= 0:
            return False, "El tiempo de servicio debe ser mayor que cero"
        
        return True, ""