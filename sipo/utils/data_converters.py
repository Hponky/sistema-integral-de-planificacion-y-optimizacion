"""
Utilidades para conversión de datos entre formatos.
Maneja la conversión de DataFrames a JSON y viceversa.
"""

import pandas as pd
import numpy as np
import datetime
import json


def convert_dataframe_row_to_json(df: pd.DataFrame, date_obj: datetime.date) -> str:
    """
    Convierte una fila de DataFrame a una cadena JSON.
    
    Args:
        df: DataFrame con los datos
        date_obj: Fecha de la fila a convertir
        
    Returns:
        String JSON con los datos de la fila
    """
    df_copy = df.copy()
    df_copy['Fecha'] = pd.to_datetime(df_copy['Fecha'])
    
    # Convertir columnas a strings para evitar problemas con datetime
    new_columns = {}
    for col in df_copy.columns:
        if isinstance(col, (datetime.datetime, datetime.time, pd.Timestamp)):
            new_columns[col] = col.strftime('%H:%M') if hasattr(col, 'strftime') else str(col)
        else:
            new_columns[col] = str(col)
    
    df_copy = df_copy.rename(columns=new_columns)
    
    row_df = df_copy[df_copy['Fecha'].dt.date == date_obj]
    if row_df.empty:
        return "{}"
    
    row_df = row_df.replace({np.nan: None})
    row_dict = row_df.iloc[0].to_dict()
    
    # Procesar valores
    processed_dict = {}
    for k, v in row_dict.items():
        key_str = str(k)
        if pd.isna(v):
            processed_dict[key_str] = None
        elif isinstance(v, (datetime.datetime, datetime.time, pd.Timestamp)):
            processed_dict[key_str] = v.strftime('%H:%M') if isinstance(v, datetime.time) else v.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(v, np.generic):
            processed_dict[key_str] = v.item()
        else:
            processed_dict[key_str] = v
    
    return json.dumps(processed_dict)


def extract_reducers_data(all_sheets: dict, time_cols: list, date_obj: datetime.date) -> dict:
    """
    Extrae los datos de reductores para una fecha específica.
    
    Args:
        all_sheets: Diccionario con todas las hojas del Excel
        time_cols: Lista de columnas de tiempo
        date_obj: Fecha para la cual extraer los reductores
        
    Returns:
        Diccionario con los datos de reductores
    """
    reducers_data = {}
    reducer_sheets = {
        'absenteeism': all_sheets.get('Absentismo_esperado'),
        'auxiliaries': all_sheets.get('Auxiliares_esperados'),
        'shrinkage': all_sheets.get('Desconexiones_esperadas')
    }
    
    for key, df_reducer in reducer_sheets.items():
        temp_dict = {}
        if df_reducer is not None and not df_reducer.empty:
            df_reducer['Fecha'] = pd.to_datetime(df_reducer['Fecha'], errors='coerce')
            reducer_row = df_reducer[df_reducer['Fecha'].dt.date == date_obj]
            if not reducer_row.empty:
                for t_col in time_cols:
                    if t_col in reducer_row.columns:
                        val = reducer_row.iloc[0].get(t_col, 0)
                        numeric_val = pd.to_numeric(val, errors='coerce')
                        temp_dict[t_col] = 0.0 if pd.isna(numeric_val) else numeric_val
        reducers_data[key] = temp_dict
    
    return reducers_data


def load_dataframes_from_results(results: list) -> tuple:
    """
    Carga los DataFrames desde los resultados almacenados.
    
    Args:
        results: Lista de StaffingResult
        
    Returns:
        Tupla con (df_dim, df_efe, df_pre, df_log)
    """
    list_dim, list_efe, list_pre, list_log = [], [], [], []
    
    for res in results:
        # Dimensionados
        d_dim = json.loads(res.agents_total)
        d_dim['Fecha'] = res.result_date
        list_dim.append(d_dim)
        
        # Efectivos
        d_efe = json.loads(res.agents_online)
        d_efe['Fecha'] = res.result_date
        list_efe.append(d_efe)
        
        # Presentes
        if res.agents_present:
            d_pre = json.loads(res.agents_present)
            d_pre['Fecha'] = res.result_date
            list_pre.append(d_pre)
        
        # Logados
        if res.agents_logged:
            d_log = json.loads(res.agents_logged)
            d_log['Fecha'] = res.result_date
            list_log.append(d_log)
    
    df_dim = pd.DataFrame(list_dim)
    df_efe = pd.DataFrame(list_efe)
    df_pre = pd.DataFrame(list_pre) if list_pre else pd.DataFrame()
    df_log = pd.DataFrame(list_log) if list_log else pd.DataFrame()
    
    return df_dim, df_efe, df_pre, df_log


def calculate_kpis_from_reducers(results: list) -> dict:
    """
    Calcula los KPIs promedio desde los reductores almacenados.
    
    Args:
        results: Lista de StaffingResult
        
    Returns:
        Diccionario con los KPIs calculados
    """
    absentismo_vals, auxiliares_vals, desconexiones_vals = [], [], []
    
    for res in results:
        reducers = json.loads(res.reducers_forecast)
        for t_val in reducers.get('absenteeism', {}).values():
            absentismo_vals.append(t_val)
        for t_val in reducers.get('auxiliaries', {}).values():
            auxiliares_vals.append(t_val)
        for t_val in reducers.get('shrinkage', {}).values():
            desconexiones_vals.append(t_val)
    
    def calc_kpi(vals):
        vals = [v for v in vals if v > 0]
        return np.mean(vals) * 100 if vals else 0
    
    return {
        'absentismo_pct': calc_kpi(absentismo_vals),
        'auxiliares_pct': calc_kpi(auxiliares_vals),
        'desconexiones_pct': calc_kpi(desconexiones_vals)
    }
