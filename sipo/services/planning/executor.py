"""
Módulo para la ejecución del motor de planificación.
Maneja la ejecución aislada del scheduler mediante subprocesos.
"""

import os
import sys
import json
import logging
import subprocess
import time as timing_module
from flask import current_app

logger = logging.getLogger(__name__)

class PlanningExecutor:
    def run_scheduler_subprocess(self, agents, start_date_str, days_count, rules_config, requirements_data, calls_data):
        """
        Ejecuta el scheduler en un proceso aislado para evitar bloqueos del GIL y mejorar la estabilidad.
        """
        temp_dir = os.path.join(current_app.instance_path, 'planning_temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        timestamp = int(timing_module.time())
        sched_input_path = os.path.join(temp_dir, f"sched_in_{timestamp}.json")
        sched_output_path = os.path.join(temp_dir, f"sched_out_{timestamp}.json")
        
        input_data = {
            "agents": agents,
            "start_date": start_date_str,
            "days_count": days_count,
            "rules_config": rules_config,
            "requirements": requirements_data,
            "calls": calls_data
        }
        
        try:
            with open(sched_input_path, 'w', encoding='utf-8') as f:
                json.dump(input_data, f)
                
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            cmd = [sys.executable, "-m", "services.scheduler.isolate_service", sched_input_path, sched_output_path]
            
            # logger.debug(f"Ejecutando scheduler subprocess: {cmd}")
            t0 = timing_module.time()
            proc = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True)
            t1 = timing_module.time()
            # logger.info(f"Subproceso scheduler finalizado en {t1-t0:.2f}s")
            
            if proc.returncode != 0:
                log_path = os.path.join(current_app.instance_path, 'scheduler_error.log')
                with open(log_path, 'w', encoding='utf-8') as f:
                    f.write(f"STDOUT:\n{proc.stdout}\n\nSTDERR:\n{proc.stderr}")
                raise Exception(f"Error en el subproceso del scheduler. Revise logs en {log_path}")
                
            with open(sched_output_path, 'r', encoding='utf-8') as f:
                raw_schedule = json.load(f)
                
            return raw_schedule
            
        finally:
            if os.path.exists(sched_input_path): os.remove(sched_input_path)
            if os.path.exists(sched_output_path): os.remove(sched_output_path)
