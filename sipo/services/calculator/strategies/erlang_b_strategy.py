"""
Implementación de la estrategia de cálculo Erlang B para el patrón Strategy.
Calcula la probabilidad de bloqueo en sistemas de telecomunicaciones.
"""

import math
from .base_strategy import CalculationStrategy


class ErlangBStrategy(CalculationStrategy):
    """
    Estrategia de cálculo para la fórmula de Erlang B.
    Calcula la probabilidad de que una llamada sea bloqueada en un sistema
    con un número determinado de servidores y una intensidad de tráfico dada.
    """
    
    def calculate(self, servers, intensity, **kwargs):
        """
        Calcula la probabilidad de bloqueo usando la fórmula de Erlang B.
        
        Args:
            servers (int): Número de servidores/canales disponibles
            intensity (float): Intensidad del tráfico (llamadas por unidad de tiempo)
            **kwargs: Argumentos adicionales no utilizados en esta estrategia
            
        Returns:
            float: Probabilidad de bloqueo (valor entre 0 y 1)
        """
        is_valid, error_msg = self.validate_parameters(servers, intensity)
        if not is_valid:
            raise ValueError(error_msg)
        
        if servers == 0:
            return 1.0
        
        max_iterate = int(servers)
        last = 1.0
        b = 1.0
        
        for count in range(1, max_iterate + 1):
            b = (intensity * last) / (count + (intensity * last))
            last = b
        
        return max(0.0, min(b, 1.0))
    
    def get_name(self):
        """
        Obtiene el nombre descriptivo de esta estrategia.
        
        Returns:
            str: Nombre de la estrategia
        """
        return "Erlang B - Probabilidad de Bloqueo"
    
    def validate_parameters(self, servers, intensity):
        """
        Valida los parámetros de entrada para el cálculo de Erlang B.
        
        Args:
            servers (int): Número de servidores a validar
            intensity (float): Intensidad del tráfico a validar
            
        Returns:
            tuple: (bool, str) donde el primer elemento indica si los parámetros son válidos,
                   y el segundo elemento contiene un mensaje de error si no son válidos
        """
        if not isinstance(servers, (int, float)) or not isinstance(intensity, (int, float)):
            return False, "Los parámetros deben ser numéricos"
        
        if servers < 0:
            return False, "El número de servidores no puede ser negativo"
        
        if intensity < 0:
            return False, "La intensidad del tráfico no puede ser negativa"
        
        return True, ""