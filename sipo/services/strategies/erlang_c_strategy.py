"""
Implementación de la estrategia de cálculo Erlang C para el patrón Strategy.
Calcula la probabilidad de espera en sistemas de colas de llamadas.
"""

import math
from .base_strategy import CalculationStrategy


class ErlangCStrategy(CalculationStrategy):
    """
    Estrategia de cálculo para la fórmula de Erlang C.
    Calcula la probabilidad de que una llamada deba esperar en una cola
    antes de ser atendida por un agente disponible.
    """
    
    def calculate(self, servers, intensity, **kwargs):
        """
        Calcula la probabilidad de espera usando la fórmula de Erlang C.
        
        Args:
            servers (int): Número de servidores/agentes disponibles
            intensity (float): Intensidad del tráfico (llamadas por unidad de tiempo)
            **kwargs: Argumentos adicionales no utilizados en esta estrategia
            
        Returns:
            float: Probabilidad de espera (valor entre 0 y 1)
        """
        is_valid, error_msg = self.validate_parameters(servers, intensity)
        if not is_valid:
            raise ValueError(error_msg)
        
        if servers <= intensity:
            return 1.0
        
        b = ErlangCStrategy._calculate_erlang_b(servers, intensity)
        denominator = (1 - (intensity / servers) * (1 - b))
        
        if denominator == 0:
            return 1.0
        
        c = b / denominator
        return max(0.0, min(c, 1.0))
    
    def get_name(self):
        """
        Obtiene el nombre descriptivo de esta estrategia.
        
        Returns:
            str: Nombre de la estrategia
        """
        return "Erlang C - Probabilidad de Espera"
    
    def validate_parameters(self, servers, intensity):
        """
        Valida los parámetros de entrada para el cálculo de Erlang C.
        
        Args:
            servers (int): Número de servidores a validar
            intensity (float): Intensidad del tráfico a validar
            
        Returns:
            tuple: (bool, str) donde el primer elemento indica si los parámetros son válidos,
                   y el segundo elemento contiene un mensaje de error si no son válidos
        """
        if not isinstance(servers, (int, float)) or not isinstance(intensity, (int, float)):
            return False, "Los parámetros deben ser numéricos"
        
        if servers <= 0:
            return False, "El número de servidores debe ser mayor que cero"
        
        if intensity < 0:
            return False, "La intensidad del tráfico no puede ser negativa"
        
        return True, ""
    
    @staticmethod
    def _calculate_erlang_b(servers, intensity):
        """
        Método auxiliar para calcular Erlang B, utilizado por Erlang C.
        
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