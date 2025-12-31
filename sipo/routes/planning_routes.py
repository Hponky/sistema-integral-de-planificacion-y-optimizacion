from flask import Blueprint, request, jsonify, current_app
from services.planning import PlanningService
from services.scheduler.export_service import ExportService
from utils.auth import token_required
from datetime import datetime
import os

planning_bp = Blueprint('planning', __name__)
service = PlanningService()
exporter = ExportService()

@planning_bp.route('/api/planning/generate-schedule', methods=['POST'])
@token_required
def generate_schedule():
    """
    Genera una nueva planificación completa.
    """
    try:
        # Delegar toda la lógica pesada al servicio
        result = service.generate_full_schedule(request.form, request.files)
        
        full_schedule = result["schedule"]
        metrics = result["metrics"]
        kpis = result["kpis"]
        params = result["params"]
        
        # Generar Excel de exportación
        campaign_code = None
        if params["scenario_id"]:
            try:
                from models import DimensioningScenario
                scenario = DimensioningScenario.query.get(params["scenario_id"])
                if scenario and scenario.segment and scenario.segment.campaign:
                    campaign_code = scenario.segment.campaign.code
            except: pass

        excel_bytes = exporter.generate_detailed_excel(full_schedule, metrics, campaign_id_global=campaign_code)
        
        filename = f"planificacion_{params['start_date'].strftime('%Y%m%d')}_{int(datetime.now().timestamp())}.xlsx"
        export_dir = os.path.join(current_app.static_folder, 'exports')
        os.makedirs(export_dir, exist_ok=True)
        export_path = os.path.join(export_dir, filename)
        
        with open(export_path, 'wb') as f:
            f.write(excel_bytes)
            
        return jsonify({
            "status": "success",
            "schedule": full_schedule,
            "metrics": metrics,
            "kpis": kpis,
            "download_url": f"/static/exports/{filename}"
        })

    except Exception as e:
        current_app.logger.error(f"Error en generate_schedule: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@planning_bp.route('/api/planning/recalculate', methods=['POST'])
@token_required
def recalculate_schedule():
    """
    Recalcula un horario modificado manualmente.
    """
    try:
        data = request.json
        if not data.get('schedule'):
             return jsonify({"error": "No schedule provided"}), 400

        result = service.recalculate_schedule(data)
        return jsonify({
            "status": "success",
            **result
        })
    except Exception as e:
        current_app.logger.error(f"Error en recalculate_schedule: {str(e)}")
        return jsonify({"error": str(e)}), 500

@planning_bp.route('/api/planning/export-excel', methods=['POST'])
@token_required
def export_excel_filtered():
    """
    Exporta un Excel filtrado por agentes seleccionados.
    """
    try:
        data = request.json
        full_schedule = data.get('schedule', [])
        agent_ids = data.get('agentIds', [])
        scenario_id = data.get('scenarioId')
        metrics = data.get('metrics')
        
        if agent_ids and isinstance(agent_ids, list):
            target_ids = [str(aid).strip().upper() for aid in agent_ids]
            full_schedule = [
                res for res in full_schedule 
                if str(res.get("agent", {}).get("dni") or res.get("agent", {}).get("id") or "").strip().upper() in target_ids
            ]
            
        if not full_schedule:
            return jsonify({"error": "No hay datos para exportar con los agentes seleccionados."}), 400

        campaign_code = None
        if scenario_id:
            try:
                from models import DimensioningScenario
                scenario = DimensioningScenario.query.get(scenario_id)
                if scenario and scenario.segment and scenario.segment.campaign:
                    campaign_code = scenario.segment.campaign.code
            except: pass

        excel_bytes = exporter.generate_detailed_excel(full_schedule, metrics, campaign_id_global=campaign_code)
        
        filename = f"planificacion_filtrada_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        export_dir = os.path.join(current_app.static_folder, 'exports')
        os.makedirs(export_dir, exist_ok=True)
        export_path = os.path.join(export_dir, filename)
        
        with open(export_path, 'wb') as f:
            f.write(excel_bytes)
            
        return jsonify({
            "status": "success",
            "download_url": f"/static/exports/{filename}"
        })
        
    except Exception as e:
        current_app.logger.error(f"Error en export_excel_filtered: {str(e)}")
        return jsonify({"error": str(e)}), 500

@planning_bp.route('/api/planning/scenarios', methods=['POST'])
@token_required
def save_planning_scenario():
    try:
        scenario_id = service.save_planning_scenario(request.json)
        return jsonify({"status": "success", "id": scenario_id, "message": "Scenario saved successfully"})
    except Exception as e:
        current_app.logger.error(f"Error en save_planning_scenario: {str(e)}")
        return jsonify({"error": str(e)}), 500

@planning_bp.route('/api/planning/scenarios', methods=['GET'])
@token_required
def list_planning_scenarios():
    try:
        scenarios = service.list_planning_scenarios()
        return jsonify(scenarios)
    except Exception as e:
        current_app.logger.error(f"Error en list_planning_scenarios: {str(e)}")
        return jsonify({"error": str(e)}), 500

@planning_bp.route('/api/planning/scenarios/<int:scenario_id>', methods=['GET'])
@token_required
def get_planning_scenario(scenario_id):
    try:
        scenario = service.get_planning_scenario(scenario_id)
        if not scenario:
            return jsonify({"error": "Scenario not found"}), 404
        return jsonify(scenario)
    except Exception as e:
        current_app.logger.error(f"Error en get_planning_scenario: {str(e)}")
        return jsonify({"error": str(e)}), 500

@planning_bp.route('/api/planning/scenarios/<int:scenario_id>', methods=['DELETE'])
@token_required
def delete_planning_scenario(scenario_id):
    try:
        if service.delete_planning_scenario(scenario_id):
            return jsonify({"status": "success", "message": "Scenario deleted successfully"})
        return jsonify({"error": "Scenario not found"}), 404
    except Exception as e:
        current_app.logger.error(f"Error en delete_planning_scenario: {str(e)}")
        return jsonify({"error": str(e)}), 500
