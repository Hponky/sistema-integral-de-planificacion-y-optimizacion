"""
Módulo de rutas para la calculadora de dimensionamiento.
"""

from flask import Blueprint, request, jsonify, session
import pandas as pd
import numpy as np
import io
import datetime
import json
from sipo.app import db
from sipo.models import Segment, Campaign, StaffingResult, User
from sipo.services.calculator_service import CalculatorService

calculator_bp = Blueprint('calculator', __name__, url_prefix='/api/calculator')

@calculator_bp.route('/', methods=['GET'])
def calculator_page():
    """
    Devuelve los datos necesarios para la calculadora de dimensionamiento.
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
    
    # Devolver los segmentos como JSON para que el frontend los procese
    segments_data = []
    for segment in segments:
        segments_data.append({
            'id': segment.id,
            'name': segment.name,
            'campaign_name': segment.campaign.name
        })
    
    return jsonify(segments_data)

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
        plantilla_excel_file = request.files['plantilla_excel']
        start_date = request.form.get('start_date', '')
        end_date = request.form.get('end_date', '')

        if not all([segment_id, plantilla_excel_file, start_date, end_date]):
            return jsonify({"error": "Debe seleccionar un segmento, cargar un archivo Excel y especificar las fechas de inicio y fin."}), 400

        # Convertir las fechas a objetos datetime
        try:
            start_date_obj = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date_obj = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"error": "El formato de las fechas es inválido. Use AAAA-MM-DD."}), 400

        config = {
            "start_date": start_date_obj,
            "end_date": end_date_obj,
            "sla_objetivo": float(request.form['sla_objetivo']),
            "sla_tiempo": int(request.form['sla_tiempo']),
            "nda_objetivo": float(request.form['nda_objetivo']),
            "intervalo_seg": int(request.form['intervalo_seg'])
        }

        # Leer el archivo Excel completo (incluye llamadas, AHT y reductores)
        file_content = plantilla_excel_file.read()
        all_sheets = pd.read_excel(io.BytesIO(file_content), sheet_name=None)

        # Verificar que todas las hojas requeridas estén presentes
        # Permitir tanto 'Volumen_a_gestionar' como 'Llamadas_esperadas'/'Llamadas_Esperadas' para compatibilidad
        volume_sheet_found = ('Volumen_a_gestionar' in all_sheets or
                            'Llamadas_esperadas' in all_sheets or
                            'Llamadas_Esperadas' in all_sheets)
        
        if not volume_sheet_found:
            return jsonify({
                "error": "La plantilla debe contener una hoja llamada 'Volumen_a_gestionar', 'Llamadas_esperadas' o 'Llamadas_Esperadas'"
            }), 400
            
        # Si encontramos 'Llamadas_esperadas' o 'Llamadas_Esperadas', la renombramos a 'Volumen_a_gestionar' para consistencia
        if 'Llamadas_esperadas' in all_sheets and 'Volumen_a_gestionar' not in all_sheets:
            all_sheets['Volumen_a_gestionar'] = all_sheets.pop('Llamadas_esperadas')
        elif 'Llamadas_Esperadas' in all_sheets and 'Volumen_a_gestionar' not in all_sheets:
            all_sheets['Volumen_a_gestionar'] = all_sheets.pop('Llamadas_Esperadas')
        
        required_sheets = ['Volumen_a_gestionar', 'AHT_esperado', 'Absentismo_esperado', 'Auxiliares_esperados', 'Desconexiones_esperadas']
        for sheet_name in required_sheets:
            if sheet_name not in all_sheets:
                return jsonify({"error": f"Falta la hoja requerida: '{sheet_name}'"}), 400

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
            
            # Convertir TODAS las columnas a strings para evitar problemas con datetime
            new_columns = {}
            for col in df_copy.columns:
                if isinstance(col, (datetime.datetime, datetime.time, pd.Timestamp)):
                    new_columns[col] = col.strftime('%H:%M') if hasattr(col, 'strftime') else str(col)
                else:
                    new_columns[col] = str(col)
            
            # Aplicar el nuevo nombre de columnas
            df_copy = df_copy.rename(columns=new_columns)
            
            row_df = df_copy[df_copy['Fecha'].dt.date == date_obj]
            if row_df.empty:
                return "{}"
            row_df = row_df.replace({np.nan: None})
            
            # Obtener la fila como diccionario
            row_dict = row_df.iloc[0].to_dict()
            
            # Procesar valores si es necesario
            processed_dict = {}
            for k, v in row_dict.items():
                # La clave ya debe ser string después de la conversión
                key_str = str(k)
                
                # Convertir valor si es necesario
                if isinstance(v, (datetime.datetime, datetime.time, pd.Timestamp)):
                    if isinstance(v, pd.Timestamp):
                        processed_dict[key_str] = v.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        processed_dict[key_str] = v.strftime('%H:%M') if isinstance(v, (datetime.time)) else v.strftime('%Y-%m-%d %H:%M:%S')
                elif isinstance(v, np.generic):
                    processed_dict[key_str] = v.item()
                else:
                    processed_dict[key_str] = v
                    
            return json.dumps(processed_dict)

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
            
            new_entry = StaffingResult(
                result_date=fecha_obj,
                agents_online=row_to_json_string(df_efectivos, fecha_obj),
                agents_total=row_to_json_string(df_dimensionados, fecha_obj),
                calls_forecast=row_to_json_string(all_sheets['Volumen_a_gestionar'], fecha_obj),
                aht_forecast=row_to_json_string(all_sheets['AHT_esperado'], fecha_obj),
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
        
        return jsonify(results_to_send)
        
    except Exception as e:
        import traceback; traceback.print_exc()
        db.session.rollback()
        return jsonify({"error": f"Error al procesar el archivo: {e}"}), 400
