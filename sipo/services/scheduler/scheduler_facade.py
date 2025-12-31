"""
Fachada principal para el servicio de planificación (Scheduler).
Orquesta los algoritmos de optimización y el preprocesamiento de datos.
"""

import sys
import logging
import time as timing
from .preprocessor import SchedulerPreprocessor
from .greedy import GreedyScheduler
from .solver import CPSATSolver

logger = logging.getLogger(__name__)

class SchedulerService:
    """
    Fachada que ofrece una interfaz unificada para la generación de horarios.
    Decide automáticamente qué algoritmo usar según la carga de datos.
    """

    def __init__(self):
        self.preprocessor = SchedulerPreprocessor()
        self.greedy_engine = GreedyScheduler()
        self.solver_engine = CPSATSolver()

    def generate_schedule(self, agents, start_date, days_count=30, rules_config=None, requirements=None, calls_forecast=None):
        """
        Genera el horario optimizado para un grupo de agentes.
        """
        t_start = timing.time()
        rules_config = rules_config or {}
        requirements = requirements or {}
        calls_forecast = calls_forecast or {}
        
        num_agents = len(agents)
        print(f"[SCHEDULER] Iniciando planificación para {num_agents} agentes, {days_count} días", file=sys.stderr)
        
        # 1. Preprocesamiento
        t_pre = timing.time()
        self.preprocessor.preprocess_agent_windows(agents)
        # logger.debug(f"[SCHEDULER] Preprocesamiento completado en {timing.time()-t_pre:.2f}s")
        
        # 2. Selección de Algoritmo
        # Si hay muchos agentes, usamos Greedy directamente por estabilidad y rapidez
        if num_agents > 20:
            # logger.info(f"[SCHEDULER] Usando motor Greedy (Umbral > 20 agentes)")
            try:
                t_algo = timing.time()
                result = self.greedy_engine.solve(agents, start_date, days_count, rules_config, requirements, calls_forecast)
                # logger.info(f"[SCHEDULER] Greedy finalizado en {timing.time()-t_algo:.2f}s")
                return result
            except Exception as e:
                logger.error(f"Error en GreedyScheduler: {e}")
                raise
        
        # Para menos de 20 agentes, intentamos el Solucionador CP-SAT
        try:
            # logger.info(f"[SCHEDULER] Intentando optimización CP-SAT")
            t_algo = timing.time()
            result = self.solver_engine.solve(agents, start_date, days_count, rules_config, requirements, calls_forecast)
            
            if result:
                # logger.info(f"[SCHEDULER] CP-SAT finalizado con éxito en {timing.time()-t_algo:.2f}s")
                return result
            
            # logger.info("[SCHEDULER] CP-SAT no encontró solución, usando Greedy como respaldo")
        except Exception as e:
            logger.error(f"Error en CPSATSolver: {e}")
            # logger.info(f"[SCHEDULER] Error en CP-SAT: {e}. Usando Greedy como respaldo")
        
        # Fallback a Greedy
        t_algo = timing.time()
        result = self.greedy_engine.solve(agents, start_date, days_count, rules_config, requirements, calls_forecast)
        # logger.info(f"[SCHEDULER] Greedy (Fallback) finalizado en {timing.time()-t_algo:.2f}s")
        return result
