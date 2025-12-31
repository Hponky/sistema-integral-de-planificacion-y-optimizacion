from flask import Blueprint, request, jsonify, send_file, current_app, g
from services.forecasting import ForecastingService
from utils.auth import token_required
import json
import pandas as pd
import io
from datetime import datetime

forecasting_bp = Blueprint('forecasting', __name__)
service = ForecastingService()

@forecasting_bp.route('/api/forecasting/analyze-intraday', methods=['POST'])
@token_required
def analyze_intraday():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        
        file = request.files['file']
        weeks = int(request.form.get('weeks', 4))
        
        result = service.analyze_intraday_distribution(file, weeks)
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Error in analyze_intraday: {e}")
        return jsonify({"error": str(e)}), 500

@forecasting_bp.route('/api/forecasting/analyze-holidays', methods=['POST'])
@token_required
def analyze_holidays():
    try:
        if 'historical_file' not in request.files or 'holidays_file' not in request.files:
            return jsonify({"error": "Se requieren ambos archivos: histórico y festivos."}), 400
        
        historical_file = request.files['historical_file']
        holidays_file = request.files['holidays_file']
        
        result = service.analyze_holiday_distribution(historical_file, holidays_file)
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Error in analyze_holidays: {e}")
        return jsonify({"error": str(e)}), 500

@forecasting_bp.route('/api/forecasting/build-curve', methods=['POST'])
@token_required
def build_curve():
    try:
        data = request.json
        weights = data.get('weights')
        day_of_week = data.get('day_of_week')
        all_weekly_data = data.get('all_weekly_data')
        labels = data.get('labels')
        
        result = service.build_weighted_curve(weights, day_of_week, all_weekly_data, labels)
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Error in build_curve: {e}")
        return jsonify({"error": str(e)}), 500

@forecasting_bp.route('/api/forecasting/analyze-date', methods=['POST'])
@token_required
def analyze_date():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        
        file = request.files['file']
        target_date = request.form.get('target_date')
        
        result = service.analyze_specific_date_historically(file, target_date)
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Error in analyze_date: {e}")
        return jsonify({"error": str(e)}), 500

@forecasting_bp.route('/api/forecasting/analyze-date-curve', methods=['POST'])
@token_required
def analyze_date_curve():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        
        file = request.files['file']
        specific_date = request.form.get('specific_date')
        
        result = service.analyze_specific_date_curve(file, specific_date)
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Error in analyze_date_curve: {e}")
        return jsonify({"error": str(e)}), 500

@forecasting_bp.route('/api/forecasting/monthly-forecast', methods=['POST'])
@token_required
def monthly_forecast():
    try:
        if 'historical_file' not in request.files:
            return jsonify({"error": "Historical file is required"}), 400
        
        historical_file = request.files['historical_file']
        holidays_file = request.files.get('holidays_file')
        
        recency_weight = float(request.form.get('recency_weight', 0.5))
        manual_overrides = json.loads(request.form.get('manual_overrides', '{}'))
        year_weights = json.loads(request.form.get('year_weights', '{}'))
        
        result = service.calculate_monthly_forecast(
            historical_file, holidays_file, recency_weight, manual_overrides, year_weights
        )
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Error in monthly_forecast: {e}")
        return jsonify({"error": str(e)}), 500

@forecasting_bp.route('/api/forecasting/distribute-intramonth', methods=['POST'])
@token_required
def distribute_intramonth():
    try:
        if 'historical_file' not in request.files:
            return jsonify({"error": "Historical file is required"}), 400
            
        historical_file = request.files['historical_file']
        holidays_file = request.files.get('holidays_file')
        
        monthly_volume_str = request.form.get('monthly_volume')
        if not monthly_volume_str:
             return jsonify({"error": "Monthly volume data is required"}), 400
             
        monthly_volume_df = pd.DataFrame(json.loads(monthly_volume_str))
        df_result = service.distribute_intramonth_forecast(monthly_volume_df, historical_file, holidays_file)
        
        excel_output = service.export_intramonth_distribution_to_excel(df_result)
        
        return send_file(
            excel_output, 
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True, 
            download_name='distribucion_intrames.xlsx'
        )
    except Exception as e:
        current_app.logger.error(f"Error in distribute_intramonth: {e}")
        return jsonify({"error": str(e)}), 500

@forecasting_bp.route('/api/forecasting/distribute-intraday', methods=['POST'])
@token_required
def distribute_intraday():
    try:
        if 'forecast_file' not in request.files:
             return jsonify({"error": "Forecast file is required"}), 400
             
        forecast_file = request.files['forecast_file']
        holidays_file = request.files.get('holidays_file')
        curves_data = json.loads(request.form.get('curves_data', '{}'))
        
        if not curves_data:
            return jsonify({"error": "Curves data is required"}), 400
            
        output_rows, time_labels = service.distribute_intraday_volume(forecast_file, holidays_file, curves_data)
        
        # Transformar a 30 min para el calculador
        output_rows, time_labels = service.transform_hourly_to_half_hourly(output_rows, time_labels)
        
        # --- NUEVO: Guardar automáticamente la distribución generada para uso en Calculadora ---
        segment_id = request.form.get('segment_id')
        if segment_id:
             try:
                 # Determinar rango de fechas desde los datos de salida
                 start_date = None
                 end_date = None
                 dates = [pd.to_datetime(r['Fecha'], dayfirst=True) for r in output_rows if 'Fecha' in r]
                 if dates:
                     start_date = min(dates).date()
                     end_date = max(dates).date()
                 
                 if start_date and end_date:
                     user_info = getattr(request, 'user_info', {})
                     full_labels = service.get_full_time_labels(interval=30)
                     service.repository.save_distribution(
                         segment_id=int(segment_id),
                         start_date=start_date,
                         end_date=end_date,
                         output_rows=output_rows,
                         time_labels=full_labels,
                         user_info=user_info
                     )
             except Exception as e:
                 current_app.logger.warning(f"No se pudo guardar la distribución automática: {e}")
        # -------------------------------------------------------------------------------------

        # Persistir curvas si se solicita
        if request.form.get('save_curves') == 'true' and request.form.get('segment_id'):
            try:
                user_info = getattr(request, 'user_info', {})
                service.save_forecasting_curves(
                    segment_id=int(request.form.get('segment_id')),
                    name=request.form.get('curve_name', f'Forecast_{datetime.now().strftime("%Y%m%d_%H%M%S")}'),
                    curves_by_day=curves_data.get('curves', {}),
                    time_labels=curves_data.get('labels', time_labels),
                    user_info=user_info,
                    weeks_analyzed=request.form.get('weeks_analyzed'),
                    date_range=request.form.get('date_range')
                )
            except Exception as e:
                current_app.logger.error(f"Error persisting curves during distribution: {e}")

        excel_output = service.export_intraday_distribution_to_excel(output_rows, time_labels)
        
        return send_file(
            excel_output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='proyeccion_intradia.xlsx'
        )
    except Exception as e:
        current_app.logger.error(f"Error in distribute_intraday: {e}")
        return jsonify({"error": str(e)}), 500

@forecasting_bp.route('/api/forecasting/save-curves', methods=['POST'])
@token_required
def save_curves():
    try:
        data = request.json
        required = ['segment_id', 'name', 'curves_by_day', 'time_labels']
        if not all(k in data for k in required):
            return jsonify({"error": f"Faltan campos requeridos: {required}"}), 400
        
        user_info = getattr(g, 'user', {})
        curve_id = service.save_forecasting_curves(
            segment_id=data['segment_id'],
            name=data['name'],
            curves_by_day=data['curves_by_day'],
            time_labels=data['time_labels'],
            user_info=user_info,
            weeks_analyzed=data.get('weeks_analyzed'),
            date_range=data.get('date_range')
        )
        
        return jsonify({"success": True, "curve_id": curve_id, "message": "Curvas guardadas exitosamente"})
    except Exception as e:
        current_app.logger.error(f"Error in save_curves: {e}")
        return jsonify({"error": str(e)}), 500

@forecasting_bp.route('/api/forecasting/curves/<int:segment_id>', methods=['GET'])
@token_required
def get_curves_by_segment(segment_id):
    try:
        curves = service.get_forecasting_curves_by_segment(segment_id)
        return jsonify({"success": True, "curves": curves})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@forecasting_bp.route('/api/forecasting/curve/<int:curve_id>', methods=['GET'])
@token_required
def get_curve_by_id(curve_id):
    try:
        curve = service.get_forecasting_curve_by_id(curve_id)
        return jsonify({"success": True, "curve": curve})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@forecasting_bp.route('/api/forecasting/generate-expected-calls', methods=['POST'])
@token_required
def generate_expected_calls():
    try:
        data = request.json
        if not all(k in data for k in ['curve_id', 'start_date', 'end_date']):
            return jsonify({"error": "Faltan campos requeridos: curve_id, start_date, end_date"}), 400
        
        df = service.generate_expected_calls_from_curves(
            curve_id=data['curve_id'],
            start_date=data['start_date'],
            end_date=data['end_date'],
            daily_volumes=data.get('daily_volumes')
        )
        
        return jsonify({
            "success": True, 
            "data": df.to_dict(orient='records'),
            "total_rows": len(df)
        })
    except Exception as e:
        current_app.logger.error(f"Error in generate_expected_calls: {e}")
        return jsonify({"error": str(e)}), 500

@forecasting_bp.route('/api/forecasting/save-distribution', methods=['POST'])
@token_required
def save_distribution():
    try:
        data = request.json
        required = ['segment_id', 'rows', 'time_labels']
        if not all(k in data for k in required):
            return jsonify({"error": f"Faltan campos requeridos: {required}"}), 400
        
        # Determinar fechas
        dates = [pd.to_datetime(r['Fecha'], dayfirst=True) for r in data['rows'] if 'Fecha' in r]
        if not dates:
            return jsonify({"error": "No se encontraron fechas válidas en los datos"}), 400
            
        start_date = min(dates).date()
        end_date = max(dates).date()
        
        user_info = getattr(g, 'user', {})
        
        # Asegurar que grabamos intervalos completos para el calculador
        full_labels = service.get_full_time_labels(interval=30)
        
        dist_id = service.save_distribution(
            segment_id=int(data['segment_id']),
            start_date=start_date,
            end_date=end_date,
            output_rows=data['rows'],
            time_labels=full_labels, # Use full 24h labels
            user_info=user_info,
            curve_id=data.get('curve_id')
        )
        
        return jsonify({"success": True, "distribution_id": dist_id, "message": "Distribución guardada exitosamente"})
    except Exception as e:
        current_app.logger.error(f"Error in save_distribution route: {e}")
        return jsonify({"error": str(e)}), 500

@forecasting_bp.route('/api/forecasting/export-curves', methods=['POST'])
@token_required
def export_curves():
    try:
        data = request.json
        if not data.get('curves_by_day') or not data.get('time_labels'):
             return jsonify({"error": "Faltan datos de curvas o etiquetas"}), 400
             
        output = service.export_all_curves_to_excel(data['curves_by_day'], data['time_labels'])
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='curvas_forecast.xlsx'
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@forecasting_bp.route('/api/forecasting/download-expected-calls', methods=['POST'])
@token_required
def download_expected_calls():
    try:
        data = request.json
        if not all(k in data for k in ['curve_id', 'start_date', 'end_date']):
            return jsonify({"error": "Faltan campos requeridos: curve_id, start_date, end_date"}), 400
        
        df = service.generate_expected_calls_from_curves(
            curve_id=data['curve_id'],
            start_date=data['start_date'],
            end_date=data['end_date'],
            daily_volumes=data.get('daily_volumes')
        )
        
        excel_output = service.exporter.export_expected_calls(df)
        
        return send_file(
            excel_output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='llamadas_esperadas.xlsx'
        )
    except Exception as e:
        current_app.logger.error(f"Error in download_expected_calls: {e}")
        return jsonify({"error": str(e)}), 500

@forecasting_bp.route('/api/forecasting/export-distribution', methods=['POST'])
@token_required
def export_distribution():
    try:
        data = request.json
        if not data.get('rows') or not data.get('time_labels'):
             return jsonify({"error": "Faltan datos de filas o etiquetas"}), 400
             
        output = service.export_intraday_distribution_to_excel(data['rows'], data['time_labels'])
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='distribucion_pronostico.xlsx'
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@forecasting_bp.route('/api/forecasting/parse-expected-calls', methods=['POST'])
@token_required
def parse_expected_calls():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No se subió ningún archivo"}), 400
            
        file = request.files['file']
        file_stream = io.BytesIO(file.read())
        
        try:
            daily_volumes = service.parse_expected_calls_file(file_stream)
            return jsonify(daily_volumes)
        except ValueError as ve:
            current_app.logger.warning(f"Error de validación en parse_expected_calls: {ve}")
            return jsonify({"error": str(ve)}), 400
        except Exception as e:
            current_app.logger.error(f"Error procesando archivo en parse_expected_calls: {e}", exc_info=True)
            return jsonify({"error": f"Error procesando el archivo: {str(e)}"}), 500
                
    except Exception as e:
        current_app.logger.error(f"Error en parse_expected_calls (wrapper): {e}")
        return jsonify({"error": str(e)}), 500

@forecasting_bp.route('/api/forecasting/curves/<int:curve_id>', methods=['DELETE', 'OPTIONS'])
@token_required
def delete_forecasting_curve(curve_id):
    """
    DELETE /api/forecasting/curves/<curve_id>
    Elimina una curva de forecasting.
    """
    try:
        service.delete_curve(curve_id)
        return jsonify({"message": "Curva eliminada exitosamente"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@forecasting_bp.route('/api/forecasting/distributions/<int:segment_id>', methods=['GET', 'OPTIONS'])
@token_required
def get_distributions(segment_id):
    """
    GET /api/forecasting/distributions/<segment_id>
    Obtiene distribuciones guardadas.
    """
    try:
        dists = service.get_distributions_by_segment(segment_id)
        return jsonify(dists)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@forecasting_bp.route('/api/forecasting/distributions/<int:dist_id>', methods=['DELETE', 'OPTIONS'])
@token_required
def delete_distribution(dist_id):
    """
    DELETE /api/forecasting/distributions/<dist_id>
    Elimina una distribución guardada.
    """
    try:
        service.delete_distribution(dist_id)
        return jsonify({"message": "Distribución eliminada exitosamente"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@forecasting_bp.route('/api/forecasting/distributions/<int:dist_id>/select', methods=['POST', 'OPTIONS'])
@token_required
def select_distribution(dist_id):
    """
    POST /api/forecasting/distributions/<dist_id>/select
    Marca una distribución como seleccionada.
    """
    try:
        service.select_distribution(dist_id)
        return jsonify({"message": "Distribución seleccionada exitosamente"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
