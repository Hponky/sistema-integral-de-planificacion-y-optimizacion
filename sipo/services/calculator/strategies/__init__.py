"""
Paquete de estrategias de cálculo para el patrón Strategy.
Contiene las implementaciones específicas para diferentes tipos de cálculos de Erlang.
"""

from .base_strategy import CalculationStrategy
from .erlang_b_strategy import ErlangBStrategy
from .erlang_c_strategy import ErlangCStrategy
from .sla_strategy import SLAStrategy