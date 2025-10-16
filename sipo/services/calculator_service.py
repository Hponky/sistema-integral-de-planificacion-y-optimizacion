"""
Módulo de servicio para la lógica de cálculo de dimensionamiento de agentes.
Contiene las funciones de cálculo basadas en Erlang y el procesamiento de plantillas.
"""

import math
import numpy as np
import pandas as pd
import io
import datetime
import json

class CalculatorService:
    """
    Proporciona métodos para realizar cálculos de dimensionamiento de agentes
    basados en la metodología Erlang y procesar plantillas de datos.
    """

    @staticmethod
    def vba_erlang_b(servers, intensity):
        """
        Calcula la probabilidad de bloqueo (Erlang B).
        Adaptado de la lógica VBA.
        """
        if servers < 0 or intensity < 0:
            return 0
        max_iterate = int(servers)
        last = 1.0
        b = 1.0
        for count in range(1, max_iterate + 1):
            b = (intensity * last) / (count + (intensity * last))
            last = b
        return max(0, min(b, 1))

    @staticmethod
    def vba_erlang_c(servers, intensity):
        """
        Calcula la probabilidad de espera (Erlang C).
        Adaptado de la lógica VBA.
        """
        if servers <= intensity:
            return 1.0
        b = CalculatorService.vba_erlang_b(servers, intensity)
        denominator = (1 - (intensity / servers) * (1 - b))
        if denominator == 0:
            return 1.0
        c = b / denominator
        return max(0, min(c, 1))

    @staticmethod
    def vba_sla(agents, service_time, calls_per_hour, aht):
        """
        Calcula el Nivel de Servicio (SLA) basado en Erlang C.
        Adaptado de la lógica VBA.
        """
        if agents <= 0 or aht <= 0 or calls_per_hour < 0:
            return 1.0 if calls_per_hour == 0 else 0.0
        
        traffic_rate = (calls_per_hour * aht) / 3600.0
        
        if traffic_rate >= agents:
            return 0.0
        
        c = CalculatorService.vba_erlang_c(agents, traffic_rate)
        
        exponent = (traffic_rate - agents) * (service_time / aht)
        try:
            sl_queued = 1 - c * math.exp(exponent)
        except OverflowError:
            sl_queued = 0
            
        return max(0, min(sl_queued, 1))

    @staticmethod
    def vba_agents_required(target_sla, service_time, calls_per_hour, aht):
        """
        Calcula el número de agentes requeridos para alcanzar un SLA objetivo.
        Adaptado de la lógica VBA.
        """
        if calls_per_hour <= 0 or aht <= 0:
            return 0
        
        traffic_rate = (calls_per_hour * aht) / 3600.0
        num_agents = math.ceil(traffic_rate)
        
        if num_agents == 0 and traffic_rate > 0:
            num_agents = 1
        
        # Asegurarse de que la utilización no sea >= 1.0 inicialmente
        # Esto es para evitar bucles infinitos si traffic_rate es muy alto
        while num_agents > 0 and traffic_rate / num_agents >= 1.0:
            num_agents += 1
            
        # Si num_agents es 0 después de los ajustes, y traffic_rate es > 0, establecerlo en 1
        if num_agents == 0 and traffic_rate > 0:
            num_agents = 1

        # Bucle para encontrar el número mínimo de agentes que cumplen el SLA
        while True:
            current_sla = CalculatorService.vba_sla(num_agents, service_time, calls_per_hour, aht)
            if current_sla >= target_sla:
                break
            num_agents += 1
            # Límite de seguridad para evitar bucles infinitos en casos extremos
            if num_agents > calls_per_hour + 1000: # Aumentado el límite para mayor robustez
                break
        return num_agents

    @staticmethod
    def _format_dataframe_columns(df, time_cols_reference):
        """
        Formatea las columnas de un DataFrame, especialmente las de tiempo,
        para asegurar consistencia.
        """
        if df is None or df.empty:
            return df

        original_columns = df.columns
        formatted_columns = []
        for col in original_columns:
            col_str = str(col).strip()
            # Si es un objeto datetime, formatearlo a HH:MM
            if isinstance(col, (datetime.time, datetime.datetime)) or 'datetime' in str(type(col)):
                if hasattr(col, 'strftime'):
                    formatted_columns.append(col.strftime('%H:%M'))
                else:
                    formatted_columns.append(col_str)
            # Si contiene dos puntos, probablemente es una hora
            elif ':' in col_str:
                try:
                    # Intenta convertir a datetime y luego formatear a HH:MM
                    dt_obj = pd.to_datetime(col_str, errors='coerce')
                    if pd.notna(dt_obj):
                        formatted_columns.append(dt_obj.strftime('%H:%M'))
                    else:
                        formatted_columns.append(col_str)
                except (ValueError, TypeError):
                    formatted_columns.append(col_str)
            else:
                formatted_columns.append(col_str)
        
        df.columns = formatted_columns
        return df

    @staticmethod
    def procesar_plantilla_unica(config, all_sheets):
        """
        Procesa una plantilla Excel con datos de llamadas, AHT y reductores
        para calcular el dimensionamiento de agentes.

        Args:
            config (dict): Diccionario de configuración con 'sla_objetivo', 'sla_tiempo',
                          'start_date', 'end_date', etc.
            all_sheets (dict): Diccionario de DataFrames de pandas, donde las claves son los nombres de las hojas.

        Returns:
            tuple: (df_dimensionados, df_presentes, df_logados, df_efectivos, kpi_data)
                   DataFrames con los resultados y un diccionario con KPIs.
        Raises:
            ValueError: Si faltan hojas requeridas o hay errores en el procesamiento.
        """
        try:
            # Mapeo de hojas para compatibilidad con el sistema legacy
            # El sistema legacy usa "Volumen_a_gestionar" pero también acepta "Llamadas_esperadas" o "Llamadas_Esperadas"
            if 'Volumen_a_gestionar' in all_sheets:
                calls_sheet_name = 'Volumen_a_gestionar'
            elif 'Llamadas_esperadas' in all_sheets:
                calls_sheet_name = 'Llamadas_esperadas'
            elif 'Llamadas_Esperadas' in all_sheets:
                calls_sheet_name = 'Llamadas_Esperadas'
            else:
                raise ValueError("No se encontró la hoja de volumen. Debe llamarse 'Volumen_a_gestionar', 'Llamadas_esperadas' o 'Llamadas_Esperadas'")
            
            required_sheets = {
                'calls': calls_sheet_name,
                'aht': 'AHT_esperado',
                'absenteeism': 'Absentismo_esperado',
                'auxiliaries': 'Auxiliares_esperados',
                'shrinkage': 'Desconexiones_esperadas'
            }

            for key, name in required_sheets.items():
                if name not in all_sheets:
                    raise ValueError(f"Falta la hoja requerida: '{name}'")
            
            df_calls = all_sheets[required_sheets['calls']]
            df_aht = all_sheets[required_sheets['aht']]
            df_absent = all_sheets[required_sheets['absenteeism']]
            df_aux = all_sheets[required_sheets['auxiliaries']]
            df_shrink = all_sheets[required_sheets['shrinkage']]

            # Formatear columnas de tiempo para todos los DataFrames
            # Primero, obtener una referencia de columnas de tiempo de df_calls
            df_calls['Fecha'] = pd.to_datetime(df_calls['Fecha'], errors='coerce')
            df_calls.dropna(subset=['Fecha'], inplace=True)
            
            # Filtrar por rango de fechas si se proporciona
            if 'start_date' in config and 'end_date' in config:
                start_date = pd.to_datetime(config['start_date'])
                end_date = pd.to_datetime(config['end_date'])
                df_calls = df_calls[(df_calls['Fecha'] >= start_date) & (df_calls['Fecha'] <= end_date)]
                
            if df_calls.empty:
                return None, None, None, None, {} # Retornar valores vacíos si no hay datos válidos

            index_cols = ['Fecha', 'Dia', 'Semana', 'Tipo']
            # Identificar columnas de tiempo y formatearlas como strings HH:MM
            time_cols_reference = []
            for col in df_calls.columns:
                if col not in index_cols:
                    # Si es un objeto datetime, formatearlo a HH:MM
                    if isinstance(col, (datetime.time, datetime.datetime)) or 'datetime' in str(type(col)):
                        time_str = col.strftime('%H:%M') if hasattr(col, 'strftime') else str(col)
                        time_cols_reference.append(time_str)
                    else:
                        time_cols_reference.append(str(col))
            
            # Renombrar las columnas de tiempo en df_calls para que coincidan con los strings formateados
            old_time_cols = [col for col in df_calls.columns if col not in index_cols]
            for old_col, new_col in zip(old_time_cols, time_cols_reference):
                df_calls.rename(columns={old_col: new_col}, inplace=True)

            all_dfs_to_format = {
                'df_calls': df_calls,
                'df_aht': df_aht,
                'df_absent': df_absent,
                'df_aux': df_aux,
                'df_shrink': df_shrink
            }

            # Formatear las columnas de tiempo en todos los DataFrames
            for df_key, df_val in all_dfs_to_format.items():
                all_dfs_to_format[df_key] = CalculatorService._format_dataframe_columns(df_val, time_cols_reference)
            
            df_calls = all_dfs_to_format['df_calls']
            df_aht = all_dfs_to_format['df_aht']
            df_absent = all_dfs_to_format['df_absent']
            df_aux = all_dfs_to_format['df_aux']
            df_shrink = all_dfs_to_format['df_shrink']

            # Asegurarse de que 'Fecha' sea datetime para todos los DFs antes de merge
            for df_name, df in [('df_aht', df_aht), ('df_absent', df_absent), ('df_aux', df_aux), ('df_shrink', df_shrink)]:
                if df is not None and not df.empty:
                    df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
                    df.dropna(subset=['Fecha'], inplace=True) # Eliminar filas con fechas inválidas
                    
                    # Filtrar por rango de fechas si se proporciona
                    if 'start_date' in config and 'end_date' in config:
                        start_date = pd.to_datetime(config['start_date'])
                        end_date = pd.to_datetime(config['end_date'])
                        df = df[(df['Fecha'] >= start_date) & (df['Fecha'] <= end_date)]
                    
                    # Asignar el DataFrame filtrado de nuevo a la variable correspondiente
                    if df_name == 'df_aht':
                        df_aht = df
                    elif df_name == 'df_absent':
                        df_absent = df
                    elif df_name == 'df_aux':
                        df_aux = df
                    elif df_name == 'df_shrink':
                        df_shrink = df

            # Lógica de merge y cálculo de agentes
            df_master = df_calls.copy()
            dfs_to_merge = {'_aht': df_aht, '_abs': df_absent, '_aux': df_aux, '_shr': df_shrink}
            
            for suffix, df in dfs_to_merge.items():
                if df is not None and not df.empty:
                    # Asegurarse de que solo las columnas de tiempo y Fecha se usen para el merge
                    cols_to_keep = ['Fecha'] + [col for col in time_cols_reference if col in df.columns]
                    df_temp = df[cols_to_keep].rename(columns={t: f"{t}{suffix}" for t in time_cols_reference})
                    df_master = pd.merge(df_master, df_temp, on='Fecha', how='left')
            
            df_master.fillna(0, inplace=True)

            dim_data, pre_data, log_data, efe_data = [], [], [], []
            for index, row in df_master.iterrows():
                base_row = {col: row[col] for col in index_cols};
                dim_row, pre_row, log_row, efe_row = base_row.copy(), base_row.copy(), base_row.copy(), base_row.copy()
                
                for col in time_cols_reference:
                    calls = row.get(col, 0)
                    aht = row.get(f'{col}_aht', 0)
                    abs_pct = row.get(f'{col}_abs', 0)
                    shr_pct = row.get(f'{col}_shr', 0)
                    aux_pct = row.get(f'{col}_aux', 0)

                    # Asegurarse de que los porcentajes sean válidos (entre 0 y 1)
                    abs_pct = max(0.0, min(1.0, abs_pct))
                    shr_pct = max(0.0, min(1.0, shr_pct))
                    aux_pct = max(0.0, min(1.0, aux_pct))

                    efectivos = float(CalculatorService.vba_agents_required(config["sla_objetivo"], config["sla_tiempo"], calls * 2, aht))
                    
                    # Evitar división por cero
                    logados = efectivos / (1 - aux_pct) if (1 - aux_pct) > 0 else efectivos
                    presentes = logados / (1 - abs_pct) if (1 - abs_pct) > 0 else logados
                    dimensionados = presentes / (1 - shr_pct) if (1 - shr_pct) > 0 else presentes
                    
                    dim_row[col] = dimensionados
                    pre_row[col] = presentes
                    log_row[col] = logados
                    efe_row[col] = efectivos
                
                dim_data.append(dim_row)
                pre_data.append(pre_row)
                log_data.append(log_row)
                efe_data.append(efe_row)

            final_cols_order = index_cols + time_cols_reference
            df_dimensionados = pd.DataFrame(dim_data)[final_cols_order]
            df_presentes = pd.DataFrame(pre_data)[final_cols_order]
            df_logados = pd.DataFrame(log_data)[final_cols_order]
            df_efectivos = pd.DataFrame(efe_data)[final_cols_order]
            
            # Cálculo de KPIs
            absent_values = df_absent[time_cols_reference].values.flatten()
            aux_values = df_aux[time_cols_reference].values.flatten()
            shrink_values = df_shrink[time_cols_reference].values.flatten()

            absent_values_non_zero = absent_values[absent_values != 0]
            aux_values_non_zero = aux_values[aux_values != 0]
            shrink_values_non_zero = shrink_values[shrink_values != 0]

            absentismo_promedio = np.mean(absent_values_non_zero) if absent_values_non_zero.size > 0 else 0
            auxiliares_promedio = np.mean(aux_values_non_zero) if aux_values_non_zero.size > 0 else 0
            desconexiones_promedio = np.mean(shrink_values_non_zero) if shrink_values_non_zero.size > 0 else 0
            
            kpi_data = {
                'absentismo_pct': absentismo_promedio * 100,
                'auxiliares_pct': auxiliares_promedio * 100,
                'desconexiones_pct': desconexiones_promedio * 100
            }

            for df in [df_dimensionados, df_presentes, df_logados, df_efectivos]:
                df.replace([np.inf, -np.inf], 0, inplace=True)
                df.fillna(0, inplace=True)
                
            return df_dimensionados, df_presentes, df_logados, df_efectivos, kpi_data
        
        except Exception as e:
            import traceback; traceback.print_exc()
            raise ValueError(f"No se pudo procesar la plantilla. Error: {e}")

    @staticmethod
    def format_and_calculate_simple(df):
        """
        Formatea un DataFrame de resultados para su visualización,
        calculando totales de horas.
        """
        df_display = df.copy()
        index_cols = ['Fecha', 'Dia', 'Semana', 'Tipo']
        time_cols = [col for col in df_display.columns if col not in index_cols]
        
        # Asegurarse de que las columnas de tiempo sean numéricas antes de redondear
        for col in time_cols:
            df_display[col] = pd.to_numeric(df_display[col], errors='coerce').fillna(0)

        df_display[time_cols] = df_display[time_cols].round(1)
        df_display['Horas-Totales'] = df_display[time_cols].sum(axis=1) / 2.0 # Asumiendo intervalos de 30 min
        
        if 'Fecha' in df_display.columns:
            df_display['Fecha'] = pd.to_datetime(df_display['Fecha']).dt.strftime('%d/%m/%Y')
        
        return df_display