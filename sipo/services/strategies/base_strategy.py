"""
Interfaz base para el patrón Strategy de cálculos de Erlang.
Define el contrato común que todas las estrategias de cálculo deben implementar.
"""

from abc import ABC, abstractmethod


class CalculationStrategy(ABC):
    """
    Interfaz base para estrategias de cálculo de Erlang.
    Define el contrato que todas las estrategias de cálculo deben seguir.
    """
    
    @abstractmethod
    def calculate(self, *args, **kwargs):
        """
        Método abstracto para realizar el cálculo específico.
        
        Args:
            *args: Argumentos posicionales requeridos para el cálculo
            **kwargs: Argumentos de palabra clave opcionales para el cálculo
            
        Returns:
            Resultado del cálculo específico de la estrategia
        """
        pass
    
    @abstractmethod
    def get_name(self):
        """
        Método abstracto para obtener el nombre de la estrategia.
        
        Returns:
            str: Nombre descriptivo de la estrategia
        """
        pass
    
    @abstractmethod
    def validate_parameters(self, *args, **kwargs):
        """
        Método abstracto para validar los parámetros de entrada.
        
        Args:
            *args: Argumentos posicionales a validar
            **kwargs: Argumentos de palabra clave a validar
            
        Returns:
            tuple: (bool, str) donde el primer elemento indica si los parámetros son válidos,
                   y el segundo elemento contiene un mensaje de error si no son válidos
        """
        pass