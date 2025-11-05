"""
Implementación de la estrategia de cálculo SLA para el patrón Strategy.
Calcula el Nivel de Servicio (SLA) basado en Erlang C y parámetros operacionales.
"""

import math
from .base_strategy import CalculationStrategy
from .erlang_c_strategy import ErlangCStrategy


class SLAStrategy(CalculationStrategy):
    """
    Estrategia de cálculo para el Nivel de Servicio (SLA).
    Calcula el porcentaje de llamadas atendidas dentro de un tiempo objetivo
    basado en el número de agentes, tiempo de servicio y volumen de llamadas.
    """
    
    def calculate(self, agents, service_time, calls_per_hour, aht, **kwargs):
        """
        Calcula el SLA usando la fórmula de Erlang C.
        
        Args:
            agents (int): Número de agentes disponibles
            service_time (float): Tiempo objetivo de servicio en segundos
            calls_per_hour (float): Volumen de llamadas por hora
            aht (float): Tiempo promedio de manejo de llamada (AHT) en segundos
            **kwargs: Argumentos adicionales no utilizados en esta estrategia
            
        Returns:
            float: Porcentaje de llamadas atendidas dentro del tiempo objetivo (valor entre 0 y 1)
        """
        is_valid, error_msg = self.validate_parameters(agents, service_time, calls_per_hour, aht)
        if not is_valid:
            raise ValueError(error_msg)
        
        if calls_per_hour == 0:
            return 1.0
        
        if agents <= 0:
            return 0.0
        
        # Modificado: Permitir AHT = 0 para cálculos especiales
        # pero mantener la validación para otros casos
        
        traffic_rate = (calls_per_hour * aht) / 3600.0
        
        if traffic_rate >= agents:
            return 0.0
        
        c = self._calculate_erlang_c(agents, traffic_rate)
        
        exponent = (traffic_rate - agents) * (service_time / aht)
        
        try:
            sl_queued = 1 - c * math.exp(exponent)
        except OverflowError:
            sl_queued = 0
        
        return max(0.0, min(sl_queued, 1.0))
    
    def get_name(self):
        """
        Obtiene el nombre descriptivo de esta estrategia.
        
        Returns:
            str: Nombre de la estrategia
        """
        return "SLA - Nivel de Servicio"
    
    def validate_parameters(self, agents, service_time, calls_per_hour, aht):
        """
        Valida los parámetros de entrada para el cálculo de SLA.
        
        Args:
            agents (int): Número de agentes a validar
            service_time (float): Tiempo objetivo de servicio a validar
            calls_per_hour (float): Volumen de llamadas por hora a validar
            aht (float): Tiempo promedio de manejo a validar
            
        Returns:
            tuple: (bool, str) donde el primer elemento indica si los parámetros son válidos,
                   y el segundo elemento contiene un mensaje de error si no son válidos
        """
        if not all(isinstance(param, (int, float)) for param in [agents, service_time, calls_per_hour, aht]):
            return False, "Todos los parámetros deben ser numéricos"
        
        if agents <= 0:
            return False, "El número de agentes debe ser mayor que cero"
        
        if aht <= 0:
            return False, "El AHT debe ser mayor que cero"
        
        if calls_per_hour < 0:
            return False, "El volumen de llamadas por hora no puede ser negativo"
        
        if service_time <= 0:
            return False, "El tiempo de servicio debe ser mayor que cero"
        
        return True, ""
    
    @staticmethod
    def _calculate_erlang_c(agents, intensity):
        """
        Método auxiliar para calcular Erlang C, utilizado por SLA.
        
        Args:
            agents (int): Número de agentes
            intensity (float): Intensidad del tráfico
            
        Returns:
            float: Valor de Erlang C
        """
        if agents <= intensity:
            return 1.0
        
        b = ErlangCStrategy._calculate_erlang_b(agents, intensity)
        denominator = (1 - (intensity / agents) * (1 - b))
        
        if denominator == 0:
            return 1.0
        
        c = b / denominator
        return max(0.0, min(c, 1.0))
    
    @staticmethod
    def _calculate_erlang_b(servers, intensity):
        """
        Método auxiliar para calcular Erlang B, utilizado por SLA.
        
        Args:
            servers (int): Número de servidores
            intensity (float): Intensidad del tráfico
            
        Returns:
            float: Valor de Erlang B
        """
        if servers < 0 or intensity < 0:
            return 0.0
        
        max_iterate = int(servers)
        last = 1.0
        b = 1.0
        
        for count in range(1, max_iterate + 1):
            b = (intensity * last) / (count + (intensity * last))
            last = b
        
        return max(0.0, min(b, 1.0))