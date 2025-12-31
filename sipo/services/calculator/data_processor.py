"""
Módulo para el procesamiento y normalización de datos de dimensionamiento.
Maneja la carga de Excel, detección de cabeceras y mezcla de hojas.
"""

import pandas as pd
import datetime
import logging

logger = logging.getLogger(__name__)

class DimensioningDataProcessor:
    """
    Se encarga de limpiar, normalizar y fusionar los datos provenientes de Excel.
    """

    @staticmethod
    def _robust_date_parsing(df, config):
        """
        Aplica parseo de fechas detectando el formato para evitar swaps incorrectos.
        """
        if 'Fecha' not in df.columns or df.empty:
            return df
            
        def smart_parse(val):
            if pd.isna(val): return val
            if isinstance(val, (datetime.datetime, pd.Timestamp)):
                return val.replace(hour=0, minute=0, second=0, microsecond=0)
            
            s = str(val).strip()
            try:
                # Si parece ISO (YYYY-MM-DD), no usar dayfirst
                if '-' in s and s.index('-') == 4:
                    dt = pd.to_datetime(s, dayfirst=False)
                else:
                    # Si parece ES (DD/MM/YYYY), usar dayfirst
                    dt = pd.to_datetime(s, dayfirst=True)
                return dt.normalize()
            except:
                try: 
                    return pd.to_datetime(s, errors='coerce').normalize()
                except:
                    return pd.NaT

        df['Fecha'] = df['Fecha'].apply(smart_parse)
        df.dropna(subset=['Fecha'], inplace=True)
        
        if df.empty or 'start_date' not in config or 'end_date' not in config:
            return df
            
        # Rango solicitado (usar dayfirst=True para la config del frontend)
        start = pd.to_datetime(config['start_date'], dayfirst=True)
        end = pd.to_datetime(config['end_date'], dayfirst=True)
        
        # Detectar si las fechas están masivamente fuera de rango y corregir swap si es necesario
        mask_in_range = (df['Fecha'] >= start) & (df['Fecha'] <= end)
        if mask_in_range.sum() < len(df) * 0.3: 
            def try_swap_month_day(dt):
                if pd.isna(dt): return dt
                try:
                    if dt.day <= 12:
                        new_dt = datetime.datetime(dt.year, dt.day, dt.month, dt.hour, dt.minute)
                        if start <= new_dt <= end:
                            return new_dt
                except: pass
                return dt
            df['Fecha'] = df['Fecha'].apply(try_swap_month_day)
            
        return df

    @staticmethod
    def normalize_df(df_raw, header_keywords=None):
        """
        Busca la fila de encabezado y normaliza los nombres de las columnas.
        """
        if df_raw is None or df_raw.empty:
            return df_raw
        
        if header_keywords is None:
            header_keywords = ['fecha', 'date', 'day', 'volumen', 'calls', 'aht', 'promedio', 'media', 'llamadas']
            
        header_found = False
        df = df_raw.copy()
        
        # Si 'fecha' ya está en las columnas, no buscamos más
        if not any(k in [str(c).lower() for c in df.columns] for k in ['fecha', 'date']):
            # Buscar en las primeras 15 filas
            for i in range(min(15, len(df_raw))):
                row_vals = [str(v).lower().strip() for v in df_raw.iloc[i].values]
                if any(k in row_vals for k in header_keywords):
                    new_cols = df_raw.iloc[i].values
                    df = df_raw.iloc[i+1:].copy()
                    df.columns = new_cols
                    header_found = True
                    break
        
        # Limpieza de nombres de columnas
        df.columns = [str(c).strip() for c in df.columns]
        
        # Estandarizar columna Fecha y metadatos comunes (ES/EN)
        rename_map = {}
        for c in df.columns:
            c_low = str(c).lower()
            if c_low in ['fecha', 'date']: rename_map[c] = 'Fecha'
            elif c_low in ['día', 'dia', 'day']: rename_map[c] = 'Dia'
            elif c_low in ['semana', 'week']: rename_map[c] = 'Semana'
            elif c_low in ['tipo', 'type']: rename_map[c] = 'Tipo'
        
        if rename_map:
            df.rename(columns=rename_map, inplace=True)
            
        return df

    def prepare_sheets(self, all_sheets):
        """
        Mapea y normaliza todas las hojas necesarias de forma flexible.
        """
        # Normalizar llaves para búsqueda insensible a mayúsculas/espacios
        # Mantenemos las hojas originales en un diccionario con llaves limpias
        normalized_sheets = {str(k).strip().lower(): all_sheets[k] for k in all_sheets}
        print(f"[DEBUG PROCESSOR] Hojas detectadas: {list(all_sheets.keys())}", flush=True)

        def get_sheet_by_name(possible_names):
            for name in possible_names:
                if name.strip().lower() in normalized_sheets:
                    return normalized_sheets[name.strip().lower()]
            return None

        # Mapeo de búsqueda
        mapping_rules = {
            'calls': ['Distribucion_Intraday', 'Volumen_a_gestionar', 'distribucion_intradia', 'Llamadas_esperadas', 'Llamadas_Esperadas'],
            'aht': ['AHT_esperado', 'aht', 'AHT esperado'],
            'absenteeism': ['Absentismo_esperado', 'absentismo', 'Absentismo esperado'],
            'auxiliaries': ['Auxiliares_esperados', 'auxiliares', 'Auxiliares esperados'],
            'shrinkage': ['Desconexiones_esperadas', 'desconexiones', 'desconexión', 'desconecion', 'Desconexiones esperadas']
        }

        processed = {}
        for key, possible_names in mapping_rules.items():
            df_sheet = get_sheet_by_name(possible_names)
            if df_sheet is None:
                # Si es 'calls', puede ser None si se usará el fallback de forecasting
                # Pero el processor debe fallar si no tiene datos para procesar después
                raise ValueError(f"Falta la hoja requerida. Se buscó alguna de estas: {possible_names}")
            
            processed[key] = self.normalize_df(df_sheet)
            
        return processed

    def merge_data(self, processed_sheets, config, time_labels):
        """
        Filtra por fechas y mezcla todas las hojas en un solo DataFrame maestro.
        """
        df_calls = processed_sheets['calls']
        
        # Convertir Fecha con lógica robusta para todas las hojas
        df_calls = self._robust_date_parsing(df_calls, config)

        if df_calls.empty:
            raise ValueError("No se pudieron leer las fechas válidas en la hoja de volumen (Llamadas).")

        # Filtrar por rango
        if 'start_date' in config and 'end_date' in config:
            start = pd.to_datetime(config['start_date'], dayfirst=True)
            end = pd.to_datetime(config['end_date'], dayfirst=True)
            df_calls = df_calls[(df_calls['Fecha'] >= start) & (df_calls['Fecha'] <= end)]
            
            if df_calls.empty:
                raise ValueError(f"No hay datos de volumen para el rango seleccionado ({config['start_date']} a {config['end_date']}). Verifique el formato de fecha.")

        # Función de normalización ultra-robusta (HH:MM)
        def normalize_time_header(col):
            # Si ya es datetime o time, formatear directamente
            if isinstance(col, (datetime.time, datetime.datetime)):
                return col.strftime('%H:%M')
            
            # Si es string o número, intentar parsear con pandas
            col_str = str(col).strip()
            if col_str == "" or col_str.lower() in ['fecha', 'dia', 'semana', 'tipo']:
                return col_str
                
            try:
                # pandas to_datetime maneja casi cualquier formato de fecha/hora de Excel
                dt = pd.to_datetime(col_str, errors='coerce')
                if pd.notnull(dt):
                    return dt.strftime('%H:%M')
            except:
                pass
            return col_str

        # Normalizar columnas de calls
        index_cols = ['Fecha', 'Dia', 'Semana', 'Tipo']
        df_calls.columns = [normalize_time_header(c) if str(c) not in index_cols else c for c in df_calls.columns]
        
        # Merge con el resto de hojas
        df_master = df_calls.copy()
        time_cols = [c for c in df_master.columns if c not in index_cols]
        total_calls = df_master[time_cols].sum().sum()
        print(f"[DEBUG MERGE] LÓGICA DE VOLUMEN: Filas={len(df_master)}, VOLUMEN TOTAL={total_calls:.2f}", flush=True)
        print(f"[DEBUG MERGE] Iniciando merge masivo. Filas base (Llamadas): {len(df_master)}", flush=True)
        
        suffixes = {'aht': '_aht', 'absenteeism': '_abs', 'auxiliaries': '_aux', 'shrinkage': '_shr'}
        
        for key, suffix in suffixes.items():
            if key in processed_sheets:
                df = processed_sheets[key]
                if df is not None and not df.empty:
                    print(f"[DEBUG MERGE] Procesando hoja '{key}'. Filas: {len(df)}", flush=True)
                    # Aplicar la misma lógica robusta de fechas
                    df = self._robust_date_parsing(df, config)
                    
                    # Normalizar columnas en la hoja secundaria
                    df.columns = [normalize_time_header(c) if str(c) not in index_cols else c for c in df.columns]
                    
                    # Sincronizar solo columnas que existan en el maestro (tiempo real)
                    cols_to_keep = ['Fecha'] + [t for t in time_labels if t in df.columns]
                    df_temp = df[cols_to_keep].rename(columns={t: f"{t}{suffix}" for t in time_labels if t in df.columns})
                    # Asegurar duplicados de fecha (tomar el último)
                    df_temp = df_temp.drop_duplicates(subset=['Fecha'], keep='last')
                    
                    df_master = pd.merge(df_master, df_temp, on='Fecha', how='left')
                    print(f"[DEBUG MERGE] Hoja '{key}' fusionada exitosamente. Filas maestro: {len(df_master)}", flush=True)

        print(f"[DEBUG MERGE] Merge completado. Filas finales: {len(df_master)}", flush=True)
        return df_master.fillna(0)
