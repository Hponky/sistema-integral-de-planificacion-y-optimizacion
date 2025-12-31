"""
Optimized Scheduler Implementation (Legacy Wrapper).
Este módulo ahora delega la lógica a la nueva implementación modular en services/scheduler/.
"""

import logging
from .scheduler_facade import SchedulerService as NewSchedulerService

logger = logging.getLogger(__name__)

class OptimizedSchedulerService:
    """
    Wrapper que mantiene la interfaz original para compatibilidad.
    """
    
    def __init__(self):
        self._service = NewSchedulerService()
    
    def generate_schedule(self, agents, start_date, days_count=30, rules_config=None, requirements=None, calls_forecast=None):
        return self._service.generate_schedule(agents, start_date, days_count, rules_config, requirements, calls_forecast)
