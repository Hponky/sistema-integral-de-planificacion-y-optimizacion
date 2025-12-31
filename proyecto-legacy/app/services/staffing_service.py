# app/services/staffing_service.py

"""
Servicio para la lógica de cálculo de personal (Staffing).
CORREGIDO: Cálculo ponderado de KPIs y redondeo de decimales.
CONSERVADO: Lógica original de Erlang VBA y estructura de datos.
"""
import math
import io
import json
import datetime
import traceback
import numpy as np
import pandas as pd
from ..models import StaffingResult
from .. import db

# ==============================================================================
# 1. FUNCIONES PRINCIPALES (PROCESAMIENTO)
# ==============================================================================

def prepare_staffing_data_from_request(file, segment_id, start_date_str, end_date_str):
    """
    Lee el Excel, normaliza columnas y maneja la lógica de fallback a BBDD.
    """
    try:
        xls = pd.ExcelFile(io.BytesIO(file.read()))
        # Leemos todo como texto para tener control total
        all_sheets = {sheet_name: pd.read_excel(xls, sheet_name=sheet_name, dtype=str) for sheet_name in xls.sheet_names}
        
        if 'Llamadas_esperadas' in all_sheets:
            all_sheets['Volumen_a_gestionar'] = all_sheets.pop('Llamadas_esperadas')

        # --- Lógica de Fallback (Si no hay volumen en Excel, busca en BD) ---
        if 'Volumen_a_gestionar' not in all_sheets or all_sheets['Volumen_a_gestionar'].empty:
            start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
            
            db_forecasts = StaffingResult.query.filter(
                StaffingResult.segment_id == segment_id, 
                StaffingResult.result_date.between(start_date, end_date)
            ).order_by(StaffingResult.result_date).all()
            
            if not db_forecasts: 
                return {"error": "Excel no contiene 'Volumen_a_gestionar' y no se encontró pronóstico en BBDD."}
            
            db_rows = []
            for f in db_forecasts:
                if f.calls_forecast and f.calls_forecast != '{}':
                    try:
                        row_data = json.loads(f.calls_forecast)
                        # Normalizar fecha para pandas
                        row_data['Fecha'] = pd.to_datetime(f.result_date).normalize()
                        if 'Dia' not in row_data: row_data['Dia'] = ''
                        if 'Semana' not in row_data: row_data['Semana'] = ''
                        if 'Tipo' not in row_data: row_data['Tipo'] = 'N'
                        db_rows.append(row_data)
                    except (json.JSONDecodeError, KeyError): continue
            
            if not db_rows: return {"error": "Registros en BBDD no contienen datos válidos."}
            all_sheets['Volumen_a_gestionar'] = pd.DataFrame(db_rows)
        
        # --- Limpieza de Fechas ---
        for sheet_name, df in all_sheets.items():
            if df is None or df.empty: continue
            
            # Buscar columna fecha
            date_col_name = next((col for col in df.columns if 'fecha' in str(col).lower()), None)
            if not date_col_name: continue
            
            if date_col_name != 'Fecha': df.rename(columns={date_col_name: 'Fecha'}, inplace=True)
            
            # Mapeo meses español a inglés para conversión robusta
            month_map = {
                'ene': 'jan', 'feb': 'feb', 'mar': 'mar', 'abr': 'apr', 'may': 'may', 'jun': 'jun',
                'jul': 'jul', 'ago': 'aug', 'sep': 'sep', 'oct': 'oct', 'nov': 'nov', 'dic': 'dec'
            }
            df['Fecha'] = df['Fecha'].astype(str).str.lower()
            for esp, eng in month_map.items():
                df['Fecha'] = df['Fecha'].str.replace(esp, eng, regex=False)
            
            df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
            df.dropna(subset=['Fecha'], inplace=True)
            if not df.empty: df['Fecha'] = df['Fecha'].dt.normalize()

        if 'Volumen_a_gestionar' not in all_sheets or all_sheets['Volumen_a_gestionar'].empty:
            return {"error": "No se encontraron datos de volumen de llamadas."}
        
        return _normalize_sheets(all_sheets)

    except Exception as e:
        traceback.print_exc()
        return {"error": f"Error al procesar Excel: {str(e)}"}

def process_staffing_template(config, all_sheets):
    """
    Realiza los cálculos de dimensionamiento (Erlang/Lineal).
    CORRECCIÓN: Calcula KPIs ponderados correctamente para evitar el "0%".
    """
    try:
        service_type = config.get("service_type", "INBOUND")
        df_volume = all_sheets['Volumen_a_gestionar']
        df_aht = all_sheets['AHT_esperado']
        df_absent = all_sheets['Absentismo_esperado']
        df_aux = all_sheets['Auxiliares_esperados']
        df_shrink = all_sheets['Desconexiones_esperadas']
        
        index_cols = ['Fecha', 'Dia', 'Semana', 'Tipo']
        time_cols = [col for col in df_volume.columns if col not in index_cols]

        # Convertir columnas de tiempo a numérico
        for df in [df_volume, df_aht, df_absent, df_aux, df_shrink]:
            if df is not None and not df.empty:
                existing_time_cols = [col for col in time_cols if col in df.columns]
                df[existing_time_cols] = df[existing_time_cols].apply(pd.to_numeric, errors='coerce').fillna(0)

        if df_volume.empty: return None, None, None, None, None

        # Merge de DataFrames para tener todo en una fila por fecha
        df_master = df_volume.copy()
        dfs_to_merge = {'_aht': df_aht, '_abs': df_absent, '_aux': df_aux, '_shr': df_shrink}
        for suffix, df in dfs_to_merge.items():
            if df is not None and not df.empty and 'Fecha' in df.columns:
                # Seleccionamos solo Fecha y las columnas de tiempo
                cols_to_keep = ['Fecha'] + [col for col in time_cols if col in df.columns]
                # Renombramos para evitar colisiones (ej: 08:00 -> 08:00_aht)
                df_temp = df[cols_to_keep].rename(columns={t: f"{t}{suffix}" for t in time_cols})
                # Hacemos merge left
                df_master = pd.merge(df_master, df_temp, on='Fecha', how='left')
        
        df_master.fillna(0, inplace=True)

        # Listas para construir los DataFrames finales
        dim_data, pre_data, log_data, efe_data = [], [], [], []

        # --- ACUMULADORES PARA KPIS PONDERADOS ---
        total_volumen_kpi = 0
        total_horas_planificadas_kpi = 0
        
        acc_dim_total = 0      # Ponderador para Absentismo
        acc_abs_weighted = 0   # Absentismo * Dimensionados
        
        acc_pres_total = 0     # Ponderador para Desconexiones (Shrinkage)
        acc_shr_weighted = 0   
        
        acc_log_total = 0      # Ponderador para Auxiliares
        acc_aux_weighted = 0

        for index, row in df_master.iterrows():
            base_row = {col: row[col] for col in index_cols if col in row}
            dim_row, pre_row, log_row, efe_row = base_row.copy(), base_row.copy(), base_row.copy(), base_row.copy()

            for col in time_cols:
                volume = row.get(col, 0)
                aht = row.get(f'{col}_aht', 0)
                abs_pct = row.get(f'{col}_abs', 0)
                shr_pct = row.get(f'{col}_shr', 0)
                aux_pct = row.get(f'{col}_aux', 0)

                # 1. CALCULAR EFECTIVOS (REQUERIDOS)
                efectivos = 0
                if service_type == 'INBOUND':
                    # Usamos tu función original vba_agents_required
                    # Nota: volume * 2 porque vba espera calls/hour y el intervalo es 30min
                    efectivos = float(vba_agents_required(
                        config["sla_objetivo"], 
                        config["sla_tiempo"], 
                        float(volume) * 2, 
                        float(aht)
                    ))
                elif service_type in ['OUTBOUND', 'BACKOFFICE']:
                    intervalo_seg = config.get("intervalo_seg", 1800)
                    if intervalo_seg > 0: 
                        workload_seg = float(volume) * float(aht)
                        efectivos = workload_seg / intervalo_seg

                # 2. APLICAR REDUCTORES INVERSOS
                # Logados = Efectivos / (1 - Aux)
                logados = efectivos / (1 - aux_pct) if (1 - aux_pct) > 0 else efectivos
                
                # Presentes = Logados / (1 - Shrink)
                presentes = logados / (1 - shr_pct) if (1 - shr_pct) > 0 else logados
                
                # Dimensionados = Presentes / (1 - Abs)
                dimensionados_raw = presentes / (1 - abs_pct) if (1 - abs_pct) > 0 else presentes
                dimensionados = math.ceil(dimensionados_raw)

                # Guardar en fila
                efe_row[col] = efectivos
                log_row[col] = logados
                pre_row[col] = presentes
                dim_row[col] = dimensionados

                # --- ACUMULAR PARA KPIS ---
                total_volumen_kpi += volume
                total_horas_planificadas_kpi += (dimensionados * 0.5) # 30 min

                acc_log_total += logados
                acc_aux_weighted += (logados * aux_pct)

                acc_pres_total += presentes
                acc_shr_weighted += (presentes * shr_pct)

                acc_dim_total += dimensionados
                acc_abs_weighted += (dimensionados * abs_pct)

            dim_data.append(dim_row)
            pre_data.append(pre_row)
            log_data.append(log_row)
            efe_data.append(efe_row)

        # Construir DataFrames finales
        df_dimensionados = pd.DataFrame(dim_data)
        df_presentes = pd.DataFrame(pre_data)
        df_logados = pd.DataFrame(log_data)
        df_efectivos = pd.DataFrame(efe_data)

        # Reordenar columnas
        for df in [df_dimensionados, df_presentes, df_logados, df_efectivos]:
            if not df.empty:
                final_cols_order = [col for col in index_cols + time_cols if col in df.columns]
                df = df[final_cols_order]
            # Limpieza final y redondeo a 2 decimales
            df.replace([np.inf, -np.inf], 0, inplace=True)
            df.fillna(0, inplace=True)
            
            # Redondear columnas numéricas
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            df[numeric_cols] = df[numeric_cols].round(2)

        # --- CALCULAR KPIS FINALES PONDERADOS ---
        avg_abs = (acc_abs_weighted / acc_dim_total * 100) if acc_dim_total > 0 else 0
        avg_shr = (acc_shr_weighted / acc_pres_total * 100) if acc_pres_total > 0 else 0
        avg_aux = (acc_aux_weighted / acc_log_total * 100) if acc_log_total > 0 else 0
        
        # FTE Promedio (Total Horas / (8h * Días))
        num_days = len(df_volume)
        fte_avg = (total_horas_planificadas_kpi / (8 * num_days)) if num_days > 0 else 0

        kpi_data = {
            'total_volumen': int(total_volumen_kpi),
            'total_horas_planificadas': round(total_horas_planificadas_kpi, 2),
            'fte_promedio': round(fte_avg, 2),
            'absentismo_pct': round(avg_abs, 2),
            'desconexiones_pct': round(avg_shr, 2),
            'auxiliares_pct': round(avg_aux, 2)
        }

        return df_dimensionados, df_presentes, df_logados, df_efectivos, kpi_data

    except Exception as e:
        traceback.print_exc()
        raise ValueError(f"No se pudo procesar la plantilla. Error: {e}")


def save_staffing_results(segment_id, config, all_sheets, df_dimensionados, df_efectivos, scenario_id=None):
    """
    Guarda los resultados en la base de datos.
    Soporta guardar en un escenario específico o en el oficial (si es None).
    """
    if df_dimensionados is None or df_dimensionados.empty: return
    
    # Asegurar tipo fecha
    if not pd.api.types.is_datetime64_any_dtype(df_dimensionados['Fecha']):
        df_dimensionados['Fecha'] = pd.to_datetime(df_dimensionados['Fecha'])
        
    min_date = df_dimensionados['Fecha'].min().date()
    max_date = df_dimensionados['Fecha'].max().date()
    
    # Borrar previos (Solo para este escenario)
    query = StaffingResult.query.filter(
        StaffingResult.segment_id == segment_id, 
        StaffingResult.result_date.between(min_date, max_date)
    )
    
    if scenario_id:
        query = query.filter(StaffingResult.scenario_id == scenario_id)
    else:
        # Si no viene escenario, intentamos buscar el oficial por defecto para no dejar huérfanos
        # (Aunque el controlador debería enviarlo siempre)
        query = query.filter(StaffingResult.scenario_id == None)
        
    query.delete(synchronize_session=False)
    
    all_dates = df_dimensionados['Fecha'].dt.date.unique()
    new_entries = []
    
    for fecha_obj in all_dates:
        reducers_data = _build_reducers_json(all_sheets, fecha_obj)
        
        new_entry = StaffingResult(
            result_date=fecha_obj, 
            segment_id=segment_id,
            scenario_id=scenario_id, # <--- GUARDAR ID AQUÍ
            agents_online=_row_to_json_string(df_efectivos, fecha_obj),
            agents_total=_row_to_json_string(df_dimensionados, fecha_obj),
            calls_forecast=_row_to_json_string(all_sheets.get('Volumen_a_gestionar'), fecha_obj),
            aht_forecast=_row_to_json_string(all_sheets.get('AHT_esperado'), fecha_obj),
            reducers_forecast=json.dumps(reducers_data),
            sla_target_percentage=config.get("sla_objetivo", 0.8), 
            sla_target_time=config.get("sla_tiempo", 20)
        )
        new_entries.append(new_entry)
        
    if new_entries:
        db.session.bulk_save_objects(new_entries)
        db.session.commit()

# ==============================================================================
# 2. FUNCIONES AUXILIARES (VBA PORT - SIN CAMBIOS EN LOGICA MATEMATICA)
# ==============================================================================

def vba_erlang_b(servers, intensity):
    if servers < 0 or intensity < 0: return 0
    max_iterate = int(servers); last = 1.0; b = 1.0
    for count in range(1, max_iterate + 1):
        b = (intensity * last) / (count + (intensity * last)); last = b
    return max(0, min(b, 1))

def vba_erlang_c(servers, intensity):
    if servers <= intensity: return 1.0
    b = vba_erlang_b(servers, intensity); denominator = (1 - (intensity / servers) * (1 - b))
    if denominator == 0: return 1.0
    return max(0, min(b / denominator, 1))

def vba_sla(agents, service_time, calls_per_hour, aht):
    if agents <= 0 or aht <= 0 or calls_per_hour < 0: return 1.0 if calls_per_hour == 0 else 0.0
    traffic_rate = (calls_per_hour * aht) / 3600.0
    if traffic_rate >= agents: return 0.0
    c = vba_erlang_c(agents, traffic_rate); exponent = (traffic_rate - agents) * (service_time / aht)
    try: sl_queued = 1 - c * math.exp(exponent)
    except OverflowError: sl_queued = 0
    return max(0, min(sl_queued, 1))

def vba_agents_required(target_sla, service_time, calls_per_hour, aht):
    if calls_per_hour <= 0 or aht <= 0: return 0
    traffic_rate = (calls_per_hour * aht) / 3600.0; num_agents = math.ceil(traffic_rate)
    if num_agents == 0 and traffic_rate > 0: num_agents = 1
    utilisation = traffic_rate / num_agents if num_agents > 0 else 0
    while utilisation >= 1.0:
        num_agents += 1; utilisation = traffic_rate / num_agents
    while True:
        current_sla = vba_sla(num_agents, service_time, calls_per_hour, aht)
        if current_sla >= target_sla: break
        num_agents += 1
        if num_agents > calls_per_hour + 100: break
    return num_agents

def _calculate_sl_capacity(num_agents, aht, sl_target, sl_time, interval_seconds=1800):
    if num_agents == 0 or aht == 0: return 0
    for traffic in np.arange(num_agents - 0.01, 0, -0.01):
        calls_per_hour_equivalent = (traffic * 3600) / aht
        sl = vba_sla(num_agents, sl_time, calls_per_hour_equivalent, aht)
        if sl >= sl_target: return math.floor((traffic * interval_seconds) / aht)
    return 0

def _normalize_sheets(all_sheets):
    master_time_labels = [(datetime.datetime.strptime("00:00", "%H:%M") + datetime.timedelta(minutes=30 * i)).strftime('%H:%M') for i in range(48)]
    id_cols = ['Fecha', 'Dia', 'Semana', 'Tipo']
    sheets_to_normalize = ['Volumen_a_gestionar', 'AHT_esperado', 'Absentismo_esperado', 'Desconexiones_esperadas', 'Auxiliares_esperados']
    normalized_sheets = {}
    
    for sheet_name in sheets_to_normalize:
        df = all_sheets.get(sheet_name)
        if df is None:
            normalized_sheets[sheet_name] = pd.DataFrame(columns=id_cols + master_time_labels)
            continue
            
        def normalize_time_header(col):
            if isinstance(col, (datetime.time, datetime.datetime)): return col.strftime('%H:%M')
            if isinstance(col, str) and ':' in col:
                try: return pd.to_datetime(col, errors='coerce').strftime('%H:%M')
                except (ValueError, TypeError): return col
            return str(col)
            
        df.rename(columns=normalize_time_header, inplace=True)
        id_data = df[[col for col in id_cols if col in df.columns]].copy()
        time_data = df[[col for col in df.columns if col in master_time_labels]]
        
        # Reindexar para asegurar que están todas las 48 columnas
        final_time_data = time_data.reindex(columns=master_time_labels, fill_value=0)
        final_df = pd.concat([id_data, final_time_data], axis=1)
        normalized_sheets[sheet_name] = final_df
        
    return normalized_sheets

def _build_reducers_json(all_sheets, fecha_obj):
    reducers_data = {"absenteeism": {}, "shrinkage": {}, "auxiliaries": {}}
    reducer_map = { "absenteeism": all_sheets.get('Absentismo_esperado'), "shrinkage": all_sheets.get('Desconexiones_esperadas'), "auxiliaries": all_sheets.get('Auxiliares_esperados') }
    time_cols = [(datetime.datetime.strptime("00:00", "%H:%M") + datetime.timedelta(minutes=30 * i)).strftime('%H:%M') for i in range(48)]
    
    for key, df_reducer in reducer_map.items():
        temp_dict = {}
        if df_reducer is not None and not df_reducer.empty:
            if 'Fecha' in df_reducer.columns:
                # Asegurar tipo fecha en el df
                if not pd.api.types.is_datetime64_any_dtype(df_reducer['Fecha']):
                    df_reducer['Fecha'] = pd.to_datetime(df_reducer['Fecha'], errors='coerce')
                
                reducer_row_df = df_reducer[df_reducer['Fecha'].dt.date == fecha_obj]
                if not reducer_row_df.empty:
                    reducer_row = reducer_row_df.iloc[0]
                    for t_col in time_cols:
                        val = reducer_row.get(t_col, 0)
                        numeric_val = pd.to_numeric(val, errors='coerce')
                        temp_dict[t_col] = 0.0 if pd.isna(numeric_val) else float(numeric_val)
        reducers_data[key] = temp_dict
    return reducers_data

def _row_to_json_string(df, date):
    if df is None or df.empty: return "{}"
    df_copy = df.copy()
    
    if 'Fecha' in df_copy.columns:
        if not pd.api.types.is_datetime64_any_dtype(df_copy['Fecha']):
            df_copy['Fecha'] = pd.to_datetime(df_copy['Fecha'], errors='coerce')
        row_df = df_copy[df_copy['Fecha'].dt.date == date]
    else: 
        row_df = df_copy
        
    if row_df.empty: return "{}"
    
    row_dict = row_df.iloc[0].to_dict()
    cleaned_dict = {}
    for k, v in row_dict.items():
        if pd.isna(v): cleaned_dict[k] = None
        elif isinstance(v, (np.generic, np.bool_)): cleaned_dict[k] = v.item()
        elif isinstance(v, pd.Timestamp): cleaned_dict[k] = v.strftime('%Y-%m-%d %H:%M:%S')
        else: cleaned_dict[k] = v
    return json.dumps(cleaned_dict)
