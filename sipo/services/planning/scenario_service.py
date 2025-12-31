"""
Módulo para la gestión de persistencia de escenarios de planificación.
"""

import json
import logging
from datetime import datetime, timedelta
from models import PlanningScenario, db

logger = logging.getLogger(__name__)

class PlanningScenarioService:
    def save_scenario(self, data):
        """
        Guarda un nuevo escenario de planificación.
        """
        name = data.get('name')
        start_date_str = data.get('startDate')
        days_count = data.get('daysCount')
        schedule_data = data.get('schedule')
        metrics_data = data.get('metrics')
        kpis_data = data.get('kpis')
        username = data.get('username')
        id_legal = data.get('idLegal')
        is_temporary = data.get('isTemporary', False)
        dim_scn_id = data.get('dimensioning_scenario_id')

        # Procesar ID de escenario de dimensionamiento en métricas
        if dim_scn_id and metrics_data:
            if isinstance(metrics_data, dict):
                metrics_data['dimensioning_scenario_id'] = dim_scn_id
            elif isinstance(metrics_data, str):
                try:
                    m = json.loads(metrics_data)
                    if isinstance(m, dict):
                        m['dimensioning_scenario_id'] = dim_scn_id
                        metrics_data = m
                except: pass

        expires_at = None
        if is_temporary:
             expires_at = datetime.now() + timedelta(days=30)

        start_date = datetime.now()
        if start_date_str:
            try: start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            except: pass
        
        scenario = PlanningScenario(
            name=name,
            username=username,
            id_legal=id_legal,
            start_date=start_date,
            days_count=days_count,
            schedule_data=json.dumps(schedule_data) if isinstance(schedule_data, (dict, list)) else schedule_data,
            metrics_data=json.dumps(metrics_data) if isinstance(metrics_data, (dict, list)) else metrics_data,
            kpis_data=json.dumps(kpis_data) if isinstance(kpis_data, (dict, list)) else kpis_data,
            is_temporary=1 if is_temporary else 0,
            expires_at=expires_at
        )
        
        db.session.add(scenario)
        db.session.commit()
        return scenario.id

    def list_scenarios(self, limit=20):
        """
        Lista los escenarios más recientes y limpia los expirados.
        """
        # Cleanup lazy
        now = datetime.now()
        PlanningScenario.query.filter(PlanningScenario.expires_at < now).delete()
        db.session.commit()
            
        scenarios = PlanningScenario.query.order_by(PlanningScenario.created_at.desc()).limit(limit).all()
        return [s.to_dict() for s in scenarios]

    def get_scenario(self, scenario_id):
        """
        Obtiene el detalle de un escenario específico.
        """
        scenario = PlanningScenario.query.get(scenario_id)
        if not scenario:
            return None
            
        metrics = json.loads(scenario.metrics_data) if scenario.metrics_data else {}
        dim_id = metrics.get('dimensioning_scenario_id') if isinstance(metrics, dict) else None

        return {
            "id": scenario.id,
            "name": scenario.name,
            "startDate": scenario.start_date.strftime('%Y-%m-%d'),
            "daysCount": scenario.days_count,
            "dimensioningScenarioId": dim_id,
            "schedule": json.loads(scenario.schedule_data) if scenario.schedule_data else [],
            "metrics": metrics,
            "kpis": json.loads(scenario.kpis_data) if scenario.kpis_data else {}
        }

    def delete_scenario(self, scenario_id):
        """
        Elimina un escenario.
        """
        scenario = PlanningScenario.query.get(scenario_id)
        if not scenario:
            return False
        db.session.delete(scenario)
        db.session.commit()
        return True
