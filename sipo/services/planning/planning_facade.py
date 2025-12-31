"""
Fachada principal para el servicio de planificación (Planning).
Orquesta la preparación de datos, ejecución del scheduler y cálculo de métricas.
"""

import logging
import time as timing_module
from datetime import datetime
from .data_manager import PlanningDataManager
from .executor import PlanningExecutor
from .kpi_service import PlanningKPIService
from .scenario_service import PlanningScenarioService
from services.scheduler.activity_allocator import ActivityAllocator
from services.scheduler.metrics_calculator import DimensioningCalculator

logger = logging.getLogger(__name__)

class PlanningService:
    def __init__(self):
        self.data_manager = PlanningDataManager()
        self.executor = PlanningExecutor()
        self.kpi_service = PlanningKPIService()
        self.scenario_service = PlanningScenarioService()
        self.allocator = ActivityAllocator()
        self.calculator = DimensioningCalculator()

    def generate_full_schedule(self, request_form, request_files):
        """
        Flujo completo: Parsing -> Scheduler -> Actividades -> Métricas -> KPIs.
        """
        # 1. Cargar Escenario de Dimensionamiento (MOVIDO AL INICIO para obtener país)
        scenario_id = request_form.get('scenario_id')
        requirements_data, calls_data, aht_data, sla_params = self.data_manager.load_scenario_requirements(scenario_id)
        
        if scenario_id and not sla_params:
            raise ValueError("No se pudieron cargar los parámetros del escenario de dimensionamiento")

        scenario_country = sla_params.get('country', 'ES')
        logger.info(f"Generating schedule for Scenario {scenario_id} - Country: {scenario_country}")

        # 2. Preparar Agentes y Ausencias (Pasando país)
        agents_file = request_files.get('file')
        absences_file = request_files.get('absences_file')
        fictitious_agents_json = request_form.get('fictitious_agents')
        
        agents = self.data_manager.parse_agents_with_absences(
            agents_file, absences_file, fictitious_agents_json, country_override=scenario_country
        )
        
        # 3. Configurar Fechas
        start_date_str = request_form.get('start_date')
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        else:
            start_date = datetime.now()
            start_date_str = start_date.strftime('%Y-%m-%d')
            
        end_date_str = request_form.get('end_date')
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                days_count = (end_date - start_date).days + 1
                if days_count <= 0: days_count = 1
            except:
                days_count = int(request_form.get('days_count', 30))
        else:
            days_count = int(request_form.get('days_count', 30))

        # 4. Ejecutar Scheduler (Subproceso)
        import json
        rules_config_str = request_form.get('rules_config', '{}')
        try: rules_config = json.loads(rules_config_str)
        except: rules_config = {}
        
        # Aplicar país del escenario a todos los agentes para reglas de negocio (Redundante pero seguro)
        for agent in agents:
            agent['country'] = scenario_country

        raw_schedule = self.executor.run_scheduler_subprocess(
            agents, start_date_str, days_count, rules_config, requirements_data, calls_data
        )
        
        # 5. Asignar Actividades
        full_schedule = self.allocator.allocate_activities(raw_schedule)
        
        # 6. Calcular Métricas y KPIs
        forecast_input = self.data_manager.prepare_forecast_input(requirements_data, calls_data, aht_data)
        
        sla_target = sla_params.get('sla_objetivo')
        sla_time = sla_params.get('sla_tiempo')
        
        metrics = self.calculator.calculate_metrics(
            full_schedule, forecast_input, service_level_target=sla_target, service_time_target=sla_time
        )
        
        kpis = self.kpi_service.calculate_final_kpis(
            full_schedule, metrics, forecast_input, scenario_id, start_date_str, days_count
        )
        
        return {
            "schedule": full_schedule,
            "metrics": metrics,
            "kpis": kpis,
            "warnings": [a.get('validation_warning') for a in agents if a.get('validation_warning')],
            "params": {
                "scenario_id": scenario_id,
                "start_date": start_date,
                "days_count": days_count
            }
        }

    def recalculate_schedule(self, data):
        """
        Recalcula actividades y métricas para un horario modificado manualmente.
        """
        schedule = data.get('schedule')
        scenario_id = data.get('scenarioId')
        start_date_str = data.get('startDate')
        days_count = data.get('daysCount', 7)
        
        requirements_data, calls_data, aht_data, sla_params = self.data_manager.load_scenario_requirements(scenario_id)
        forecast_input = self.data_manager.prepare_forecast_input(requirements_data, calls_data, aht_data)
        
        # Asegurar que los agentes mantienen el país del escenario en el recálculo
        scenario_country = sla_params.get('country', 'ES')
        logger.info(f"Recalculating schedule for Scenario {scenario_id} - Applying Country: {scenario_country}")
        for res in schedule:
            if 'agent' in res:
                res['agent']['country'] = scenario_country

        schedule = self.allocator.allocate_activities(schedule)
        
        sla_target = sla_params.get('sla_objetivo')
        sla_time = sla_params.get('sla_tiempo')
        
        metrics = self.calculator.calculate_metrics(
            schedule, forecast_input, service_level_target=sla_target, service_time_target=sla_time
        )
        
        kpis = self.kpi_service.calculate_final_kpis(
            schedule, metrics, forecast_input, scenario_id, start_date_str, days_count
        )
        
        return {
            "schedule": schedule, 
            "metrics": metrics,
            "kpis": kpis
        }

    def save_planning_scenario(self, data):
        return self.scenario_service.save_scenario(data)

    def list_planning_scenarios(self):
        return self.scenario_service.list_scenarios()

    def get_planning_scenario(self, scenario_id):
        return self.scenario_service.get_scenario(scenario_id)

    def delete_planning_scenario(self, scenario_id):
        return self.scenario_service.delete_scenario(scenario_id)
