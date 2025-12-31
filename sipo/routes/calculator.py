"""
Rutas de la API para la calculadora de dimensionamiento.
Este módulo solo contiene los endpoints HTTP, delegando la lógica de negocio
a los servicios correspondientes.
"""

from flask import Blueprint, request, jsonify
import pandas as pd
import json
from models import Segment
from services.calculator.calculator_service import CalculatorService
from services.calculator.storage_service import StorageService

calculator_bp = Blueprint('calculator', __name__, url_prefix='/api/calculator')
service = CalculatorService()


@calculator_bp.route('/', methods=['GET'])
def calculator_page():
    """
    GET /api/calculator/
    Devuelve la lista de segmentos disponibles para dimensionamiento.
    """
    try:
        segments = Segment.query.all()
        segments_data = [{
            'id': s.id,
            'name': s.name,
            'campaign_id': s.campaign_id,
            'campaign_name': s.campaign.name if s.campaign else None
        } for s in segments]
        
        return jsonify(segments_data)
    except Exception as e:
        return jsonify({"error": f"Error al obtener segmentos: {e}"}), 500


@calculator_bp.route('/calculate', methods=['POST'])
def calculate():
    """
    POST /api/calculator/calculate
    Procesa un cálculo de dimensionamiento y guarda los resultados.
    
    Form Data:
        - segment_id: ID del segmento
        - start_date: Fecha de inicio
        - end_date: Fecha de fin
        - sla_objetivo: SLA objetivo (0-1)
        - sla_tiempo: Tiempo SLA en segundos
        - intervalo: Intervalo en minutos
        - id_legal: ID legal del usuario (opcional)
        - username: Nombre de usuario (opcional)
        - file_llamadas: Archivo Excel con volumen de llamadas
        - file_reductores: Archivo Excel con reductores
    """
    try:
        # Validar y extraer datos del formulario
        segment_id = request.form.get('segment_id', type=int)
        if not segment_id:
            return jsonify({"error": "Falta el ID del segmento"}), 400
        
        segment = Segment.query.get_or_404(segment_id)
        
        # Extraer archivo Excel (contiene todas las hojas)
        plantilla_excel = request.files.get('plantilla_excel')
        
        if not plantilla_excel:
            return jsonify({"error": "Falta el archivo de plantilla Excel"}), 400
        
        # Extraer configuración - sin valores por defecto, deben venir del formulario
        sla_objetivo_raw = request.form.get('sla_objetivo')
        sla_tiempo_raw = request.form.get('sla_tiempo')
        nda_objetivo_raw = request.form.get('nda_objetivo')
        intervalo_seg_raw = request.form.get('intervalo_seg')
        
        # Validar campos requeridos
        if not all([sla_objetivo_raw, sla_tiempo_raw, nda_objetivo_raw]):
            return jsonify({"error": "Faltan parámetros requeridos: sla_objetivo, sla_tiempo, nda_objetivo"}), 400
        
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        
        print(f"[DEBUG ROUTES] RAW start_date: {start_date_str}, end_date: {end_date_str}", flush=True)
        print(f"[DEBUG ROUTES] RAW parameters: SLA={sla_objetivo_raw}, NDA={nda_objetivo_raw}", flush=True)
        
        config = {
            "start_date": start_date_str,
            "end_date": end_date_str,
            "sla_objetivo": float(sla_objetivo_raw),
            "sla_tiempo": int(sla_tiempo_raw),
            "nda_objetivo": float(nda_objetivo_raw),
            "intervalo": int(intervalo_seg_raw or 1800) // 60,
            "segment": segment
        }
        
        print(f"Calculator config: SLA={config['sla_objetivo']}, NDA={config['nda_objetivo']}, Time={config['sla_tiempo']}s", flush=True)
        
        # Leer todas las hojas del archivo Excel
        all_sheets = pd.read_excel(plantilla_excel, sheet_name=None)
        
        # Verificar y normalizar nombres de hojas
        # Permitir tanto 'Volumen_a_gestionar' como 'Llamadas_esperadas'/'Llamadas_Esperadas' para compatibilidad
        volume_sheet_names = ['Volumen_a_gestionar', 'Llamadas_esperadas', 'Llamadas_Esperadas', 'Distribucion_Intraday']
        volume_sheet_found = any(name in all_sheets for name in volume_sheet_names)

        if volume_sheet_found:
            print("[DEBUG CALCULATOR] SOURCE: EXCEL FILE (Sheet found)", flush=True)
            source_msg = "Archivo Excel cargado"
        else:
            # Intentar fallback desde Forecasting DB
            print("[DEBUG CALCULATOR] SOURCE: FORECASTING DB (Fallback)", flush=True)
            id_legal = request.form.get('id_legal')
            start_date_val = config["start_date"]
            end_date_val = config["end_date"]
            
            df_fallback, fallback_msg = service.get_fallback_volume(segment_id, start_date_val, end_date_val, id_legal)
            
            if df_fallback is not None and not df_fallback.empty:
                print(f"[DEBUG CALCULATOR] FALLBACK SUCCESS: {fallback_msg}", flush=True)
                all_sheets['Volumen_a_gestionar'] = df_fallback
                volume_sheet_found = True
                source_msg = "Forecasting DB (Activa)"
            else:
                detail = fallback_msg or "No se encontró distribución activa."
                return jsonify({
                    "error": f"No hay datos de volumen y no se encontró distribución activa. \nDetalle: {detail}"
                }), 400
        
        # Procesar plantilla y calcular
        try:
            results = service.procesar_plantilla_unica(config, all_sheets)
            df_dimensionados, df_presentes, df_logados, df_efectivos, kpi_data, df_calls, df_aht = results
            print(f"[DEBUG CALCULATOR] CALCULATION COMPLETE. Rows processed: {len(df_calls)}", flush=True)
        except ValueError as ve:
            return jsonify({"error": str(ve)}), 400
        
        if df_dimensionados is None or df_dimensionados.empty:
            return jsonify({"error": "No se pudieron procesar los datos para el cálculo."}), 400
        
        # Crear escenario
        id_legal = request.form.get('id_legal')
        username = request.form.get('username')
        scenario = StorageService.create_scenario(segment_id, config, id_legal, username)
        
        # Guardar resultados
        StorageService.save_calculation_results(
            scenario_id=scenario.id,
            df_dimensionados=df_dimensionados,
            df_presentes=df_presentes,
            df_logados=df_logados,
            df_efectivos=df_efectivos,
            kpi_data=kpi_data,
            df_calls=df_calls,
            df_aht=df_aht
        )
        
        # Formatear resultados para respuesta
        results_to_send = {
            "scenario_id": scenario.id,
            "dimensionados": service.format_and_calculate_simple(df_dimensionados).to_dict(orient='split'),
            "efectivos": service.format_and_calculate_simple(df_efectivos).to_dict(orient='split'),
            "presentes": service.format_and_calculate_simple(df_presentes).to_dict(orient='split'),
            "logados": service.format_and_calculate_simple(df_logados).to_dict(orient='split'),
            "kpis": kpi_data,
            "warning": fallback_msg if 'fallback_msg' in locals() else None
        }
        
        # Limpieza de index
        for key in results_to_send:
            if isinstance(results_to_send[key], dict) and 'index' in results_to_send[key]:
                del results_to_send[key]['index']
        
        return jsonify(results_to_send)
        
    except Exception as e:
        from app import db
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Error en el cálculo: {str(e)}"}), 500


@calculator_bp.route('/history', methods=['GET'])
def get_history():
    """
    GET /api/calculator/history?id_legal=<id>
    Obtiene el historial de cálculos de un usuario.
    
    Query Parameters:
        - id_legal: ID legal del usuario (requerido)
    """
    try:
        id_legal = request.args.get('id_legal')
        
        if not id_legal:
            return jsonify({"error": "El parámetro 'id_legal' es requerido"}), 400
        
        history_data = StorageService.get_scenario_history(id_legal)
        return jsonify(history_data)
        
    except Exception as e:
        return jsonify({"error": f"Error al obtener el historial: {e}"}), 500


@calculator_bp.route('/history/<int:scenario_id>', methods=['GET'])
def get_scenario_details(scenario_id):
    """
    GET /api/calculator/history/<scenario_id>
    Obtiene los detalles completos de un escenario específico.
    
    Path Parameters:
        - scenario_id: ID del escenario
    """
    try:
        results_dict = StorageService.get_scenario_details(scenario_id)
        return jsonify(results_dict)
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Error al obtener detalles del escenario: {e}"}), 500


@calculator_bp.route('/history/<int:scenario_id>', methods=['DELETE'])
def delete_scenario(scenario_id):
    """
    DELETE /api/calculator/history/<scenario_id>
    Elimina un escenario y sus resultados asociados.
    
    Path Parameters:
        - scenario_id: ID del escenario
    """
    try:
        StorageService.delete_scenario(scenario_id)
        return jsonify({"message": "Escenario eliminado exitosamente"}), 200
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        from app import db
        db.session.rollback()
        return jsonify({"error": f"Error al eliminar el escenario: {e}"}), 500
