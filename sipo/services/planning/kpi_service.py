"""
Módulo para el cálculo de KPIs y métricas de planificación.
"""

import json
import logging
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)

class PlanningKPIService:
    def calculate_final_kpis(self, full_schedule, metrics, forecast_input, scenario_id, start_date_str, days_count):
        """
        Calcula KPIs globales consolidados con los nombres de campos esperados por el frontend.
        """
        # 1. SLA & NDA de métricas
        total_slots = 0
        total_pct = 0
        total_attainable = 0
        total_demand = 0
        
        if metrics and 'daily_metrics' in metrics:
            for d, d_data in metrics['daily_metrics'].items():
                 for slot in d_data.get('slots', []):
                     total_slots += 1
                     total_pct += slot.get('coverage_pct', 100)
                     total_attainable += slot.get('attainable', 0)
                     total_demand += slot.get('demand', 0)
        
        service_level = (total_pct / total_slots) if total_slots > 0 else 100
        nda = (total_attainable / total_demand * 100) if total_demand > 0 else 100
        
        # 2. Ausentismos (BMED y VAC)
        total_bmed = 0
        total_vac = 0
        days_count_val = days_count if days_count and days_count > 0 else 7

        for agent_res in full_schedule:
            for d_str, shift in agent_res["shifts"].items():
                shift_type = shift.get("type", "").upper()
                shift_label = shift.get("label", "").upper()
                
                if shift_type == "ABSENCE":
                    label_str = shift_label.upper()
                    if any(k in label_str for k in ["BMED", "BAJA", "ENFERMEDAD", "HOSPITAL", "IT"]):
                        total_bmed += 1
                    elif any(k in label_str for k in ["VAC", "VACACIONES"]):
                        total_vac += 1
        
        avg_bmed = round(total_bmed / days_count_val, 1)
        avg_vac = round(total_vac / days_count_val, 1)

        # 3. AHT Promedio
        avg_aht = self._get_avg_aht(scenario_id, forecast_input)

        # 4. Horas promedio
        avg_hours = 0
        if metrics:
            total_h = metrics.get('total_hours', 0)
            n_ag = metrics.get('total_agents_scheduled', 0)
            if n_ag > 0:
                # Horas totales entre agentes (esto da el promedio del periodo)
                avg_hours = total_h / n_ag

        return {
            "activeAgents": len(full_schedule),
            "avgBmed": avg_bmed,
            "avgVac": avg_vac,
            "serviceLevel": round(service_level, 1),
            "nda": round(nda, 1),
            "totalCoverage": round(nda, 1),
            "avgAht": round(avg_aht, 0),
            "avgHours": round(avg_hours, 1)
        }

    def _get_avg_aht(self, scenario_id, forecast_input):
        """
        Obtiene el AHT promedio desde el escenario o lo calcula desde el input.
        """
        avg_aht = 0
        if scenario_id:
            try:
                from models import DimensioningScenario
                scenario_db = DimensioningScenario.query.get(scenario_id)
                if scenario_db and scenario_db.kpis_data:
                    kpis_json = json.loads(scenario_db.kpis_data) if isinstance(scenario_db.kpis_data, str) else scenario_db.kpis_data
                    avg_aht = kpis_json.get('aht_promedio', 0)
            except Exception as e:
                logger.error(f"Error recuperando AHT del escenario: {e}")

        if avg_aht == 0 and forecast_input:
            total_w_aht = 0
            total_c = 0
            for d, day_data in forecast_input.items():
                for i, val in day_data.items():
                    c = val.get('calls', 0)
                    a = val.get('aht', 0)
                    total_w_aht += c*a
                    total_c += c
            avg_aht = (total_w_aht / total_c) if total_c > 0 else 300
            
        return avg_aht
