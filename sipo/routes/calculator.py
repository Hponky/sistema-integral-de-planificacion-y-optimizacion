"""
Módulo de rutas para la calculadora de dimensionamiento.
"""

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
import pandas as pd
import io
import datetime
import json
from sipo.app import db
from sipo.models import Segment, Campaign, StaffingResult, User
from sipo.services.calculator_service import CalculatorService

calculator_bp = Blueprint('calculator', __name__, url_prefix='/calculator')

@calculator_bp.route('/segments', methods=['GET'])
def get_segments():
    """
    API para obtener la lista de segmentos disponibles.
    Requiere que el usuario esté autenticado.
    """
    if 'user' not in session:
        return jsonify({"error": "No autorizado"}), 401

    user = User.query.filter_by(username=session['user']).first()
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 401

    if user.role == 'admin':
        segments = Segment.query.join(Campaign).order_by(Campaign.name, Segment.name).all()
    else:
        segments = Segment.query.join(Campaign).filter(Campaign.id.in_([c.id for c in user.campaigns])).order_by(Campaign.name, Segment.name).all()
    
    segments_data = []
    for segment in segments:
        segments_data.append({
            'id': segment.id,
            'name': segment.name,
            'campaign_name': segment.campaign.name,
            'description': segment.description or ''
        })
    
    return jsonify(segments_data)

@calculator_bp.route('/', methods=['GET'])
def calculator_page():
    """
    Renderiza la página de la calculadora de dimensionamiento.
    Requiere que el usuario esté autenticado.
    """
    if 'user' not in session:
        flash("Por favor, inicia sesión para acceder a la calculadora.", "error")
        return redirect(url_for('auth.login')) # Redirigir a la ruta de login del blueprint 'auth'

    user = User.query.filter_by(username=session['user']).first()
    if not user:
        session.clear()
        flash("Usuario no encontrado. Por favor, inicia sesión de nuevo.", "error")
        return redirect(url_for('auth.login'))

    if user.role == 'admin':
        segments = Segment.query.join(Campaign).order_by(Campaign.name, Segment.name).all()
    else:
        segments = Segment.query.join(Campaign).filter(Campaign.id.in_([c.id for c in user.campaigns])).order_by(Campaign.name, Segment.name).all()
    
    return render_template('calculator/calculator.html', segments=segments)

@calculator_bp.route('/calculate', methods=['POST'])
def calculate():
    """
    Procesa el formulario de la calculadora, realiza los cálculos de dimensionamiento
    y guarda los resultados en la base de datos.
    """
    if 'user' not in session:
        return jsonify({"error": "No autorizado"}), 401

    try:
        segment_id = request.form['segment_id']
        start_date_str = request.form['start_date']
        end_date_str = request.form['end_date']
        plantilla_excel_file = request.files['plantilla_excel']

        if not all([segment_id, start_date_str, end_date_str, plantilla_excel_file]):
            return jsonify({"error": "Debe seleccionar un segmento, un rango de fechas y cargar un archivo Excel."}), 400

        config = {
            "sla_objetivo": float(request.form['sla_objetivo']),
            "sla_tiempo": int(request.form['sla_tiempo']),
            "nda_objetivo": float(request.form['nda_objetivo']), # Aunque no se usa directamente en procesar_plantilla_unica, se mantiene por consistencia
            "intervalo_seg": int(request.form['intervalo_seg']) # Aunque no se usa directamente en procesar_plantilla_unica, se mantiene por consistencia
        }

        # Leer el archivo Excel de reductores
        file_content = plantilla_excel_file.read()
        all_sheets_from_file = pd.read_excel(io.BytesIO(file_content), sheet_name=None)

        # Obtener pronóstico de llamadas de la base de datos para el rango de fechas
        start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        forecast_results = StaffingResult.query.filter(
            StaffingResult.segment_id == segment_id,
            StaffingResult.result_date.between(start_date, end_date)
        ).order_by(StaffingResult.result_date).all()

        if not forecast_results:
            return jsonify({"error": "No se encontró un pronóstico de llamadas guardado en la base de datos para este segmento y rango de fechas."}), 404

        calls_data_list = [json.loads(r.calls_forecast) for r in forecast_results if r.calls_forecast]
        if not calls_data_list:
             return jsonify({"error": "Los registros de pronóstico de llamadas encontrados están vacíos o corruptos."}), 400

        df_calls_from_db = pd.DataFrame(calls_data_list)
        df_calls_from_db['Fecha'] = pd.to_datetime(df_calls_from_db['Fecha'])

        # Combinar las hojas del archivo subido con el pronóstico de llamadas de la DB
        all_sheets = {'Llamadas_esperadas': df_calls_from_db}
        all_sheets.update(all_sheets_from_file)

        # Procesar la plantilla usando el servicio
        df_dimensionados, df_presentes, df_logados, df_efectivos, kpi_data = CalculatorService.procesar_plantilla_unica(config, all_sheets)
        
        if df_dimensionados is None or df_dimensionados.empty:
            return jsonify({"error": "No se pudieron procesar los datos para el cálculo."}), 400
        
        # Guardar resultados en la base de datos
        if not df_dimensionados.empty:
            df_dimensionados['Fecha'] = pd.to_datetime(df_dimensionados['Fecha'])
            min_date_calc = df_dimensionados['Fecha'].min().date()
            max_date_calc = df_dimensionados['Fecha'].max().date()
            
            # Eliminar registros existentes para el rango de fechas y segmento
            StaffingResult.query.filter(
                StaffingResult.segment_id == segment_id,
                StaffingResult.result_date.between(min_date_calc, max_date_calc)
            ).delete(synchronize_session=False)
            db.session.commit()

        index_cols = ['Fecha', 'Dia', 'Semana', 'Tipo']
        # Obtener time_cols de df_dimensionados después de procesar
        time_cols = [col for col in df_dimensionados.columns if col not in index_cols]
        all_dates = pd.to_datetime(df_dimensionados['Fecha']).dt.date.unique()
        
        new_entries = []
        
        def row_to_json_string(df, date_obj):
            """Convierte una fila de DataFrame a una cadena JSON."""
            df_copy = df.copy()
            df_copy['Fecha'] = pd.to_datetime(df_copy['Fecha'])
            row_df = df_copy[df_copy['Fecha'].dt.date == date_obj]
            if row_df.empty:
                return "{}"
            row_df = row_df.replace({np.nan: None})
            row_dict = row_df.iloc[0].to_dict()
            if 'Fecha' in row_dict and isinstance(row_dict['Fecha'], pd.Timestamp):
                row_dict['Fecha'] = row_dict['Fecha'].strftime('%Y-%m-%d %H:%M:%S')
            for k, v in row_dict.items():
                if isinstance(v, np.generic):
                    row_dict[k] = v.item()
            return json.dumps(row_dict)

        for fecha_obj in all_dates:
            reducers_data = {"absenteeism": {}, "shrinkage": {}, "auxiliaries": {}}
            reducer_map_dfs = {
                "absenteeism": all_sheets.get('Absentismo_esperado'),
                "shrinkage": all_sheets.get('Desconexiones_esperadas'),
                "auxiliaries": all_sheets.get('Auxiliares_esperados')
            }
            for key, df_reducer in reducer_map_dfs.items():
                temp_dict = {}
                if df_reducer is not None and not df_reducer.empty:
                    df_reducer['Fecha'] = pd.to_datetime(df_reducer['Fecha'], errors='coerce')
                    reducer_row = df_reducer[df_reducer['Fecha'].dt.date == fecha_obj]
                    if not reducer_row.empty:
                        for t_col in time_cols:
                            if t_col in reducer_row.columns:
                                val = reducer_row.iloc[0].get(t_col, 0)
                                numeric_val = pd.to_numeric(val, errors='coerce')
                                temp_dict[t_col] = 0.0 if pd.isna(numeric_val) else numeric_val
                reducers_data[key] = temp_dict
            
            # Obtener AHT y Llamadas del DataFrame combinado (all_sheets) para guardar
            calls_forecast_data = all_sheets['Llamadas_esperadas'][all_sheets['Llamadas_esperadas']['Fecha'].dt.date == fecha_obj]
            aht_forecast_data = all_sheets['AHT_esperado'][all_sheets['AHT_esperado']['Fecha'].dt.date == fecha_obj]

            new_entry = StaffingResult(
                result_date=fecha_obj,
                agents_online=row_to_json_string(df_efectivos, fecha_obj),
                agents_total=row_to_json_string(df_dimensionados, fecha_obj),
                calls_forecast=row_to_json_string(calls_forecast_data, fecha_obj),
                aht_forecast=row_to_json_string(aht_forecast_data, fecha_obj),
                reducers_forecast=json.dumps(reducers_data),
                segment_id=segment_id,
                sla_target_percentage=config["sla_objetivo"],
                sla_target_time=config["sla_tiempo"]
            )
            new_entries.append(new_entry)

        db.session.bulk_save_objects(new_entries)
        db.session.commit()
        
        results_to_send = {
            "dimensionados": CalculatorService.format_and_calculate_simple(df_dimensionados).to_dict(orient='split'),
            "presentes": CalculatorService.format_and_calculate_simple(df_presentes).to_dict(orient='split'),
            "logados": CalculatorService.format_and_calculate_simple(df_logados).to_dict(orient='split'),
            "efectivos": CalculatorService.format_and_calculate_simple(df_efectivos).to_dict(orient='split'),
            "kpis": kpi_data
        }
        
        for key in results_to_send:
            if 'index' in results_to_send.get(key, {}):
                del results_to_send[key]['index']
        
        flash('Dimensionamiento calculado y guardado con éxito.', 'success')
        return jsonify(results_to_send)
        
    except Exception as e:
        import traceback; traceback.print_exc()
        db.session.rollback()
        return jsonify({"error": f"Error al procesar el archivo: {e}"}), 400
