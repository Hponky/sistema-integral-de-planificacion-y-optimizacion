"""
Contexto Strategy para seleccionar la estrategia de cálculo apropiada.
Implementa el patrón Context para gestionar diferentes estrategias de cálculo.
"""

from typing import Dict, Any
from .base_strategy import CalculationStrategy
from .erlang_b_strategy import ErlangBStrategy
from .erlang_c_strategy import ErlangCStrategy
from .sla_strategy import SLAStrategy


class StrategyContext:
    """
    Contexto para gestionar y seleccionar estrategias de cálculo.
    Implementa el patrón Context para permitir la selección dinámica
    de estrategias basada en el tipo de cálculo requerido.
    """
    
    def __init__(self):
        """
        Inicializa el contexto con las estrategias disponibles.
        """
        self._strategies: Dict[str, CalculationStrategy] = {
            'erlang_b': ErlangBStrategy(),
            'erlang_c': ErlangCStrategy(),
            'sla': SLAStrategy()
        }
    
    def get_strategy(self, strategy_type: str) -> CalculationStrategy:
        """
        Obtiene la estrategia de cálculo según el tipo solicitado.
        
        Args:
            strategy_type (str): Tipo de estrategia ('erlang_b', 'erlang_c', 'sla')
            
        Returns:
            CalculationStrategy: Instancia de la estrategia solicitada
            
        Raises:
            ValueError: Si el tipo de estrategia no está disponible
        """
        if strategy_type not in self._strategies:
            available_strategies = ', '.join(self._strategies.keys())
            raise ValueError(f"Estrategia no disponible. Estrategias disponibles: {available_strategies}")
        
        return self._strategies[strategy_type]
    
    def calculate(self, strategy_type: str, *args, **kwargs):
        """
        Ejecuta el cálculo utilizando la estrategia especificada.
        
        Args:
            strategy_type (str): Tipo de estrategia a utilizar
            *args: Argumentos posicionales para el cálculo
            **kwargs: Argumentos de palabra clave para el cálculo
            
        Returns:
            Any: Resultado del cálculo específico
        """
        strategy = self.get_strategy(strategy_type)
        return strategy.calculate(*args, **kwargs)
    
    def get_available_strategies(self):
        """
        Obtiene la lista de estrategias disponibles.
        
        Returns:
            list: Lista de nombres de estrategias disponibles
        """
        return list(self._strategies.keys())