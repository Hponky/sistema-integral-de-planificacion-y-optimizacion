# app/services/forecasting_service.py

"""
Servicio UNIFICADO para toda la lógica de negocio relacionada con Forecasting.
Incluye:
1. Análisis de Distribución Intradía (Patrones semanales).
2. Construcción de Curvas Ponderadas.
3. Forecasting Mensual (Proyección a largo plazo).
4. Distribución Intra-Mes (Desglose de volumen mensual a diario).
5. Aplicación de Curvas Intradía (Volumen diario a intervalos).
"""

import pandas as pd
import numpy as np
import datetime
import json
import io
from calendar import monthrange

# ==============================================================================
# 1. ANÁLISIS DE DISTRIBUCIÓN INTRADÍA (PATRONES SEMANALES)
# ==============================================================================

def analyze_intraday_distribution(historical_file, weeks_to_analyze):
    """
    Analiza un archivo histórico para detectar patrones de comportamiento por día de la semana.
    Devuelve datos semanales, detección de outliers y pesos sugeridos.
    """
    df = pd.read_excel(historical_file)
    df.columns = [str(col).strip() for col in df.columns]

    # Detección y normalización de formato (Tabla plana vs Pivote)
    required_cols = ['Fecha', 'Intervalo', 'Llamadas Ofrecidas']
    if not all(col in df.columns for col in required_cols):
        id_cols = [col for col in df.columns if col.lower() in ['fecha', 'dia', 'semana', 'tipo']]
        time_cols = [col for col in df.columns if ':' in str(col)]
        
        if not id_cols or not time_cols:
            raise ValueError("El archivo debe contener 'Fecha', 'Intervalo' y 'Llamadas Ofrecidas' o un formato de tabla pivote con horas.")
            
        # Convertir de pivote a tabla plana
        df = pd.melt(df, id_vars=id_cols, value_vars=time_cols, var_name='Intervalo', value_name='Llamadas Ofrecidas')

    # Limpieza de datos
    df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
    df.dropna(subset=['Fecha'], inplace=True)
    df['Llamadas Ofrecidas'] = pd.to_numeric(df['Llamadas Ofrecidas'], errors='coerce').fillna(0)
    
    # Normalizar formato de intervalo (HH:MM)
    def format_interval(x):
        try:
            if isinstance(x, (datetime.time, datetime.datetime)): return x.strftime('%H:%M')
            return pd.to_datetime(str(x).split(' ')[-1]).strftime('%H:%M')
        except (ValueError, TypeError): return "00:00"
    
    df['Intervalo'] = df['Intervalo'].apply(format_interval)
    
    # Filtrar por semanas recientes
    max_date = df['Fecha'].max()
    if pd.isna(max_date):
        raise ValueError("No se encontraron fechas válidas en los datos.")
    
    weeks_ago_date = max_date - pd.to_timedelta((weeks_to_analyze * 7) - 1, unit='d')
    df_filtered = df[df['Fecha'] >= weeks_ago_date]

    if df_filtered.empty: 
        raise ValueError(f"No se encontraron datos en el rango de las últimas {weeks_to_analyze} semanas.")
    
    # Crear tabla dinámica
    df_pivot = df_filtered.pivot_table(index='Fecha', columns='Intervalo', values='Llamadas Ofrecidas', aggfunc='sum').fillna(0)
    time_labels = sorted([col for col in df_pivot.columns if ':' in str(col)])
    
    df_pivot.reset_index(inplace=True)
    df_pivot['day_of_week'] = df_pivot['Fecha'].dt.weekday
    df_pivot['week_number'] = df_pivot['Fecha'].dt.isocalendar().week
    
    weekly_data = {i: [] for i in range(7)}
    
    # Calcular estadísticas por día de la semana
    for day_num in range(7):
        day_group_df = df_pivot[df_pivot['day_of_week'] == day_num].sort_values(by='Fecha', ascending=False)
        if day_group_df.empty: continue
        
        # Calcular curvas porcentuales
        day_curves = day_group_df[time_labels].div(day_group_df[time_labels].sum(axis=1), axis=0).fillna(0)
        
        # Detección de Outliers (Desviación respecto a la mediana)
        is_outlier = pd.Series([False]*len(day_curves), index=day_curves.index)
        if len(day_curves) >= 2:
            valid_day_curves = day_curves[day_group_df[time_labels].sum(axis=1) > 0]
            if not valid_day_curves.empty:
                reference_curve = valid_day_curves.median()
                deviations = ((day_curves - reference_curve)**2).mean(axis=1)
                
                if len(deviations) >= 4:
                    q1, q3 = deviations.quantile(0.25), deviations.quantile(0.75)
                    iqr = q3 - q1
                    is_outlier = (deviations > q3 + 1.5 * iqr)

        # Calcular pesos propuestos (inverso de la desviación)
        weights = pd.Series([0.0]*len(day_curves), index=day_curves.index)
        if len(day_curves) > 0:
             # Por defecto, peso equitativo si no hay lógica compleja de outlier activada
             weights = pd.Series([100.0/len(day_curves)]*len(day_curves), index=day_curves.index)
        
        # Preparar datos para el frontend
        for index, row in day_group_df.iterrows():
            intraday_raw_calls = row[time_labels].to_dict()
            total_calls = sum(intraday_raw_calls.values())
            intraday_percentages = {k: (v / total_calls if total_calls > 0 else 0) for k, v in intraday_raw_calls.items()}
            
            weekly_data[day_num].append({
                'week': int(row['week_number']), 
                'date': row['Fecha'].strftime('%d/%m/%Y'), 
                'total_calls': total_calls, 
                'is_outlier': bool(is_outlier.get(index, False)), 
                'proposed_weight': round(weights.get(index, 0)), 
                'intraday_dist': intraday_percentages, 
                'intraday_raw': intraday_raw_calls
            })
            
    return {"weekly_data": weekly_data, "labels": time_labels}


def build_weighted_curve(weights, day_of_week, all_weekly_data, labels):
    """
    Construye una única curva representativa basada en los pesos seleccionados por el usuario.
    """
    data_for_day = all_weekly_data.get(str(day_of_week), [])
    if not data_for_day:
        raise ValueError("No hay datos para el día seleccionado.")
        
    weighted_calls = {label: 0 for label in labels}
    total_weight = sum(float(w) for w in weights.values())
    
    if total_weight == 0:
        raise ValueError("La suma de los pesos es cero. No se puede calcular la curva.")

    for week_data in data_for_day:
        weight = float(weights.get(str(week_data['week']), 0)) / total_weight
        if weight > 0:
            for label in labels:
                weighted_calls[label] += week_data['intraday_raw'].get(label, 0) * weight
    
    total_weighted_calls = sum(weighted_calls.values())
    if total_weighted_calls == 0:
        # Retornar curva plana si todo es 0
        final_distribution = {label: 0 for label in labels}
    else:
        final_distribution = {label: (calls / total_weighted_calls) for label, calls in weighted_calls.items()}
    
    return {"final_curve": final_distribution}


def analyze_specific_date_historically(historical_file, target_date_str):
    """
    Busca en el histórico el comportamiento de una fecha específica (ej. 25 de Diciembre) 
    en todos los años disponibles en el archivo.
    Retorna las curvas de esos días pasados para que el usuario decida cuál usar.
    """
    # 1. Cargar y Limpiar Datos (Misma lógica robusta que analyze_intraday)
    df = pd.read_excel(historical_file)
    df.columns = [str(col).strip() for col in df.columns]

    # Normalización de formato
    required_cols = ['Fecha', 'Intervalo', 'Llamadas Ofrecidas']
    if not all(col in df.columns for col in required_cols):
        id_cols = [col for col in df.columns if col.lower() in ['fecha', 'dia', 'semana', 'tipo']]
        time_cols = [col for col in df.columns if ':' in str(col)]
        if not id_cols or not time_cols:
            raise ValueError("El archivo debe contener 'Fecha', 'Intervalo' y 'Llamadas Ofrecidas' o un formato de tabla pivote.")
        df = pd.melt(df, id_vars=id_cols, value_vars=time_cols, var_name='Intervalo', value_name='Llamadas Ofrecidas')

    df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
    df.dropna(subset=['Fecha'], inplace=True)
    df['Llamadas Ofrecidas'] = pd.to_numeric(df['Llamadas Ofrecidas'], errors='coerce').fillna(0)
    
    # Normalizar intervalos
    def format_interval(x):
        try:
            if isinstance(x, (datetime.time, datetime.datetime)): return x.strftime('%H:%M')
            return pd.to_datetime(str(x).split(' ')[-1]).strftime('%H:%M')
        except: return "00:00"
    df['Intervalo'] = df['Intervalo'].apply(format_interval)

    # 2. Filtrar por Mes y Día
    try:
        target_dt = pd.to_datetime(target_date_str)
        target_month = target_dt.month
        target_day = target_dt.day
    except:
        raise ValueError("Formato de fecha objetivo inválido.")

    # Filtramos todas las fechas del histórico que coincidan en Mes y Día
    history_matches = df[
        (df['Fecha'].dt.month == target_month) & 
        (df['Fecha'].dt.day == target_day)
    ].copy()

    if history_matches.empty:
        raise ValueError(f"No se encontraron datos históricos para el día {target_day}/{target_month} en el archivo.")

    # 3. Crear Pivote y Calcular Curvas
    df_pivot = history_matches.pivot_table(index='Fecha', columns='Intervalo', values='Llamadas Ofrecidas', aggfunc='sum').fillna(0)
    time_labels = sorted([col for col in df_pivot.columns if ':' in str(col)])
    
    historical_data = []
    
    for date_idx, row in df_pivot.iterrows():
        raw_calls = row[time_labels].to_dict()
        total_calls = sum(raw_calls.values())
        
        # Calcular distribución porcentual
        intraday_dist = {k: (v / total_calls if total_calls > 0 else 0) for k, v in raw_calls.items()}
        
        historical_data.append({
            'date': date_idx.strftime('%Y-%m-%d'),
            'year': date_idx.year,
            'day_name': date_idx.strftime('%A'), # Nombre del día (Lunes, Martes...)
            'total_calls': total_calls,
            'intraday_dist': intraday_dist,
            'intraday_raw': raw_calls
        })

    # Ordenar por año descendente (más reciente primero)
    historical_data.sort(key=lambda x: x['year'], reverse=True)

    return {
        "historical_data": historical_data,
        "labels": time_labels,
        "target_date_display": f"{target_day}/{target_month}"
    }


def analyze_specific_date_curve(historical_file, specific_date_str):
    """
    Obtiene la curva exacta de una fecha pasada específica (ej: '2023-04-05').
    Útil cuando el usuario sabe que el festivo móvil cayó ese día exacto el año pasado.
    """
    # 1. Cargar y Limpiar (Misma rutina estándar)
    df = pd.read_excel(historical_file)
    df.columns = [str(col).strip() for col in df.columns]

    # Normalización de formato
    required_cols = ['Fecha', 'Intervalo', 'Llamadas Ofrecidas']
    if not all(col in df.columns for col in required_cols):
        id_cols = [col for col in df.columns if col.lower() in ['fecha', 'dia', 'semana', 'tipo']]
        time_cols = [col for col in df.columns if ':' in str(col)]
        if not id_cols or not time_cols:
            raise ValueError("Formato de archivo no reconocido.")
        df = pd.melt(df, id_vars=id_cols, value_vars=time_cols, var_name='Intervalo', value_name='Llamadas Ofrecidas')

    df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
    df.dropna(subset=['Fecha'], inplace=True)
    df['Llamadas Ofrecidas'] = pd.to_numeric(df['Llamadas Ofrecidas'], errors='coerce').fillna(0)
    
    def format_interval(x):
        try:
            if isinstance(x, (datetime.time, datetime.datetime)): return x.strftime('%H:%M')
            return pd.to_datetime(str(x).split(' ')[-1]).strftime('%H:%M')
        except: return "00:00"
    df['Intervalo'] = df['Intervalo'].apply(format_interval)

    # 2. Filtrar la fecha exacta solicitada
    try:
        target_date = pd.to_datetime(specific_date_str).date()
    except:
        raise ValueError("Fecha específica inválida.")

    day_data = df[df['Fecha'].dt.date == target_date]

    if day_data.empty:
        raise ValueError(f"No se encontraron datos para la fecha {specific_date_str} en el archivo histórico.")

    # 3. Agrupar y calcular curva
    # Agrupamos por intervalo por si hay múltiples filas para la misma fecha/hora (ej. skills separados)
    grouped_data = day_data.groupby('Intervalo')['Llamadas Ofrecidas'].sum()
    
    total_volume = grouped_data.sum()
    if total_volume == 0:
        raise ValueError(f"El volumen para el día {specific_date_str} es 0.")

    # Calcular porcentajes
    curve_distribution = (grouped_data / total_volume).to_dict()
    
    # Ordenar etiquetas de tiempo
    time_labels = sorted(list(curve_distribution.keys()))
    
    # Retornamos estructura lista para ser usada por 'generate_forecast_template' o visualizada
    return {
        "date": specific_date_str,
        "total_volume": total_volume,
        "curve": curve_distribution,
        "labels": time_labels
    }


def export_curve_to_excel(final_curve, labels):
    """
    Genera un archivo Excel en memoria con la curva resultante.
    """
    df = pd.DataFrame([final_curve])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Curva_Ponderada')
    output.seek(0)
    return output


# ==============================================================================
# 2. FORECASTING MENSUAL (Lógica Completa)
# ==============================================================================

def calculate_monthly_forecast(historical_file, holidays_file, recency_weight, manual_overrides, year_weights_str):
    """
    Genera una proyección mensual basada en históricos, ajustando por días laborables (AcWD)
    y crecimiento interanual/reciente.
    """
    # 1. Cargar Festivos
    df_holidays = pd.read_excel(holidays_file)
    holidays_set = set(pd.to_datetime(df_holidays['Fecha'], dayfirst=True, errors='coerce').dt.date)

    def get_working_days(year, month, holidays):
        days_in_month = monthrange(year, month)[1]
        return sum(1 for day in range(1, days_in_month + 1) if datetime.date(year, month, day).weekday() < 5 and datetime.date(year, month, day) not in holidays)

    # 2. Cargar Histórico
    df = pd.read_excel(historical_file)
    df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce')
    df.dropna(subset=['Fecha'], inplace=True)
    # Buscar columna de volumen dinámicamente
    vol_col = next((c for c in df.columns if 'llamada' in str(c).lower() or 'volumen' in str(c).lower()), None)
    if not vol_col: vol_col = df.columns[1] # Fallback a la segunda columna
    
    df[vol_col] = pd.to_numeric(df[vol_col], errors='coerce').fillna(0)
    
    # Eliminar mes incompleto si existe
    if not df.empty:
        last_data_point_date = df['Fecha'].max()
        if last_data_point_date.day != last_data_point_date.days_in_month:
            df = df[~((df['Fecha'].dt.year == last_data_point_date.year) & (df['Fecha'].dt.month == last_data_point_date.month))]
    
    if df.empty:
        raise ValueError("No se encontraron datos de meses completos en el archivo histórico.")

    # 3. Agrupar por Mes
    df_monthly = df.groupby(pd.Grouper(key='Fecha', freq='M'))[vol_col].sum().reset_index()
    df_monthly['year'] = df_monthly['Fecha'].dt.year
    df_monthly['month'] = df_monthly['Fecha'].dt.month
    df_monthly['working_days'] = df_monthly.apply(lambda row: get_working_days(row['year'], row['month'], holidays_set), axis=1)
    
    # Calcular Average Calls per Working Day (ACWD)
    df_monthly['acwd'] = df_monthly.apply(lambda row: row[vol_col] / row['working_days'] if row['working_days'] > 0 else 0, axis=1)

    acwd_pivot = df_monthly.pivot_table(index='year', columns='month', values='acwd').fillna(0)
    calls_pivot = df_monthly.pivot_table(index='year', columns='month', values=vol_col).fillna(0)

    # 4. Aplicar Overrides Manuales (si existen)
    if manual_overrides:
        for key, value in manual_overrides.items():
            try:
                year, month = map(int, key.split('-'))
                workdays = get_working_days(year, month, holidays_set)
                if year in acwd_pivot.index and month in acwd_pivot.columns:
                    acwd_pivot.loc[year, month] = float(value) / workdays if workdays > 0 else 0
                    calls_pivot.loc[year, month] = float(value)
            except (ValueError, KeyError): continue
    
    # 5. Calcular Crecimiento Mes a Mes (MoM)
    mom_growth_pivot = acwd_pivot.pct_change(axis='columns')
    mom_growth_pivot.replace([np.inf, -np.inf], np.nan, inplace=True)
    # Limpiar crecimientos inválidos (divisiones por cero anteriores)
    invalid_growth_mask = (acwd_pivot == 0) | (acwd_pivot.shift(1, axis='columns') == 0)
    mom_growth_pivot[invalid_growth_mask] = np.nan
    
    # Usar años completos solamente para el promedio histórico
    full_years_mom_growth = mom_growth_pivot[mom_growth_pivot.index < mom_growth_pivot.index.max()]
    
    # 6. Ponderación de Años Históricos
    year_weights_dict = json.loads(year_weights_str) if year_weights_str else {}
    year_weights_dict = {int(k): v for k, v in year_weights_dict.items() if v > 0}
    
    def weighted_nan_average(series, weights):
        valid_indices = series.notna()
        if not valid_indices.any(): return 0
        valid_series = series[valid_indices]
        valid_weights = weights.reindex(valid_series.index).fillna(0)
        if valid_weights.sum() == 0: return valid_series.mean() if not valid_series.empty else 0
        return np.average(valid_series, weights=valid_weights)
        
    if year_weights_dict and not full_years_mom_growth.empty:
        valid_years = {year for year in year_weights_dict.keys() if year in full_years_mom_growth.index}
        if valid_years:
            weights_series = pd.Series(year_weights_dict)
            avg_historical_mom_growth = full_years_mom_growth.apply(lambda col: weighted_nan_average(col, weights_series), axis=0)
        else:
            avg_historical_mom_growth = full_years_mom_growth.mean()
    else:
        # Si no hay pesos manuales, dar más peso a años recientes por defecto
        if not full_years_mom_growth.empty:
            weights_series = pd.Series(np.linspace(0.1, 1, len(full_years_mom_growth.index)), index=full_years_mom_growth.index)
            avg_historical_mom_growth = full_years_mom_growth.apply(lambda col: weighted_nan_average(col, weights_series), axis=0)
        else:
            avg_historical_mom_growth = pd.Series(0, index=range(1, 13))
            
    avg_historical_mom_growth.fillna(0, inplace=True)
    
    # 7. Proyección
    last_real_date = df['Fecha'].max()
    current_year = last_real_date.year
    last_real_month = last_real_date.month
    target_year = current_year + 1
    
    projected_acwd_pivot = acwd_pivot.copy().replace(np.nan, 0)
    if current_year not in projected_acwd_pivot.index: projected_acwd_pivot.loc[current_year] = 0
    if target_year not in projected_acwd_pivot.index: projected_acwd_pivot.loc[target_year] = 0

    # Proyectar resto del año actual
    for m in range(last_real_month + 1, 13):
        previous_month_acwd = projected_acwd_pivot.loc[current_year, m - 1]
        # Crecimiento reciente (últimos 2 meses)
        m_minus_2_acwd = projected_acwd_pivot.loc[current_year, m - 2] if m > 1 else 0
        recent_mom_growth = (previous_month_acwd - m_minus_2_acwd) / m_minus_2_acwd if m_minus_2_acwd > 0 else 0
        
        historical_mom_growth = avg_historical_mom_growth.get(m, 0)
        
        # Mezcla: Recency vs History
        combined_growth = (recent_mom_growth * recency_weight) + (historical_mom_growth * (1 - recency_weight))
        projected_acwd = previous_month_acwd * (1 + combined_growth)
        projected_acwd_pivot.loc[current_year, m] = projected_acwd if projected_acwd > 0 else 0
    
    # Proyectar año objetivo
    for m in range(1, 13):
        prev_month, prev_year = (m - 1, target_year) if m > 1 else (12, current_year)
        previous_month_acwd = projected_acwd_pivot.loc[prev_year, prev_month]
        
        # Crecimiento reciente (arrastrado del año anterior si es Enero)
        m_minus_2_month, m_minus_2_year = (prev_month - 1, prev_year) if prev_month > 1 else (11, current_year)
        try: m_minus_2_acwd = projected_acwd_pivot.loc[m_minus_2_year, m_minus_2_month]
        except KeyError: m_minus_2_acwd = 0
        
        recent_mom_growth = (previous_month_acwd - m_minus_2_acwd) / m_minus_2_acwd if m_minus_2_acwd > 0 else 0
        historical_mom_growth = avg_historical_mom_growth.get(m, 0)
        
        combined_growth = (recent_mom_growth * recency_weight) + (historical_mom_growth * (1 - recency_weight))
        projected_acwd = previous_month_acwd * (1 + combined_growth)
        projected_acwd_pivot.loc[target_year, m] = projected_acwd if projected_acwd > 0 else 0

    # 8. Convertir ACWD de vuelta a Volumen Total
    final_calls_pivot = calls_pivot.copy().replace(np.nan, 0)
    if target_year not in final_calls_pivot.index: final_calls_pivot.loc[target_year] = 0
    
    for year in [current_year, target_year]:
        for month in range(1, 13):
            # No sobrescribir historia real, a menos que sea un override
            if year == current_year and month <= last_real_month and f"{year}-{month}" not in manual_overrides:
                 continue
            
            acwd = projected_acwd_pivot.loc[year, month]
            workdays = get_working_days(year, month, holidays_set)
            total_calls = acwd * workdays
            final_calls_pivot.loc[year, month] = total_calls

    # 9. Formatear salida JSON
    final_pivot_json = {str(year): {str(month): val for month, val in row.items()} for year, row in final_calls_pivot.to_dict(orient='index').items()}
    current_year_forecast_json = {str(m): final_calls_pivot.loc[current_year, m] for m in range(1, 13) if m > last_real_month}
    forecast_json = {str(m): final_calls_pivot.loc[target_year, m] for m in range(1, 13)}
        
    return {
        'pivot': final_pivot_json, 
        'current_year_forecast': current_year_forecast_json,
        'forecast': forecast_json, 
        'target_year': target_year,
        'current_year': current_year, 
        'last_real_month': last_real_month
    }


# ==============================================================================
# 3. DISTRIBUCIÓN INTRA-MES (MÓDULO NUEVO)
# ==============================================================================

def distribute_intramonth_forecast(monthly_volume_df, historical_file, holidays_file):
    """
    Distribuye un volumen mensual dado (en monthly_volume_df) a nivel diario
    basándose en el peso histórico de cada día del mes (Seasonality Intra-mes).
    """
    # 1. Cargar Histórico para aprender pesos
    df_hist = pd.read_excel(historical_file)
    df_hist.columns = [str(col).strip() for col in df_hist.columns]
    vol_col = next((c for c in df_hist.columns if 'fecha' not in str(c).lower()), None)
    
    df_hist['Fecha'] = pd.to_datetime(df_hist['Fecha'], errors='coerce', dayfirst=True)
    df_hist.dropna(subset=['Fecha'], inplace=True)
    df_hist[vol_col] = pd.to_numeric(df_hist[vol_col], errors='coerce').fillna(0)

    # 2. Cargar Festivos
    holidays_set = set()
    if holidays_file:
        try:
            df_hol = pd.read_excel(holidays_file)
            holidays_set = set(pd.to_datetime(df_hol['Fecha'], dayfirst=True).dt.date)
        except: pass

    result_rows = []

    # 3. Iterar sobre cada mes objetivo
    for _, row_req in monthly_volume_df.iterrows():
        target_year = int(row_req['año'])
        target_month = int(row_req['mes'])
        target_volume = float(row_req['volumen'])

        # Filtrar datos históricos de ESE mes (de todos los años)
        df_hist['Month'] = df_hist['Fecha'].dt.month
        df_hist['Day'] = df_hist['Fecha'].dt.day
        hist_month_data = df_hist[df_hist['Month'] == target_month]
        
        if hist_month_data.empty:
            # Si no hay historia, distribución plana
            _, days_in_month = monthrange(target_year, target_month)
            daily_weights = {d: 1/days_in_month for d in range(1, days_in_month + 1)}
        else:
            # Calcular peso promedio por día (1, 2, 3... 31)
            daily_avgs = hist_month_data.groupby('Day')[vol_col].mean()
            daily_weights = (daily_avgs / daily_avgs.sum()).to_dict()

        # Generar fechas del mes objetivo
        _, num_days = monthrange(target_year, target_month)
        distributed_total = 0
        month_rows = []

        for day_num in range(1, num_days + 1):
            current_date = datetime.date(target_year, target_month, day_num)
            
            # Obtener peso (default 0 si el día histórico no existió, ej: 31 de un mes corto)
            weight = daily_weights.get(day_num, 0)
            
            # Calcular volumen
            vol_for_day = round(target_volume * weight)
            distributed_total += vol_for_day
            
            month_rows.append({
                "Fecha": current_date.strftime('%Y-%m-%d'),
                "Volumen": vol_for_day,
                "EsFestivo": current_date in holidays_set
            })

        # Ajuste de redondeo (distribuir la diferencia al día con más volumen)
        diff = target_volume - distributed_total
        if diff != 0 and month_rows:
            month_rows.sort(key=lambda x: x['Volumen'], reverse=True)
            month_rows[0]['Volumen'] += diff
            month_rows.sort(key=lambda x: x['Fecha']) # Reordenar cronológicamente

        result_rows.extend(month_rows)

    return pd.DataFrame(result_rows)


# ==============================================================================
# 4. DISTRIBUCIÓN INTRADÍA (APLICACIÓN DE CURVAS A DIARIO)
# ==============================================================================

def distribute_intraday_volume(forecast_file, holidays_file, curves_data):
    """
    Aplica las curvas horarias (definidas en curves_data) a un archivo de volumen diario.
    Soporta lógica de prioridad: Fecha Exacta > Festivo > Día Semana.
    """
    curves_to_use = curves_data.get('curves', {})
    time_labels = curves_data.get('labels', [])
    
    # Cargar Festivos
    holidays_set = set()
    if holidays_file:
        try:
            df_h = pd.read_excel(holidays_file)
            holidays_set = set(pd.to_datetime(df_h['Fecha'], dayfirst=True).dt.date)
        except: pass

    # Cargar Forecast Diario
    df = pd.read_excel(forecast_file)
    df.columns = [str(c).strip() for c in df.columns]
    vol_col = next((c for c in df.columns if 'fecha' not in str(c).lower()), None)
    
    df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce', dayfirst=True)
    df.dropna(subset=['Fecha'], inplace=True)
    
    output_rows = []
    day_map = {0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves', 4: 'Viernes', 5: 'Sábado', 6: 'Domingo'}

    for _, row in df.iterrows():
        date_obj = row['Fecha']
        vol = float(row[vol_col]) if pd.notna(row[vol_col]) else 0
        
        if vol <= 0: continue

        date_str = date_obj.strftime('%Y-%m-%d')
        is_holiday = date_obj.date() in holidays_set
        weekday_str = str(date_obj.weekday())

        # --- LÓGICA DE PRIORIDAD ---
        curve_key = None
        # 1. Fecha Específica (ej: '2025-12-25')
        if date_str in curves_to_use: 
            curve_key = date_str
        # 2. Festivo Genérico
        elif is_holiday and 'holiday' in curves_to_use: 
            curve_key = 'holiday'
        # 3. Día de la Semana
        elif weekday_str in curves_to_use: 
            curve_key = weekday_str
        
        if not curve_key: 
            continue # No hay curva aplicable, saltamos el día

        curve = curves_to_use[curve_key]
        
        # Crear fila base
        new_row = {
            'Fecha': date_obj, 
            'Dia': day_map.get(date_obj.weekday()), 
            'Semana': date_obj.isocalendar()[1], 
            'Tipo': 'FESTIVO' if is_holiday else 'N'
        }
        
        # Distribuir volumen
        sum_dist = 0
        for t in time_labels:
            val = round(vol * curve.get(t, 0))
            new_row[t] = val
            sum_dist += val
        
        # Ajuste de redondeo (al pico)
        diff = round(vol - sum_dist)
        if diff != 0:
            # Encontrar intervalo con mayor peso en la curva para sumar/restar la diferencia
            peak_interval = max(curve, key=curve.get)
            new_row[peak_interval] += diff
            
        output_rows.append(new_row)
        
    return output_rows, time_labels


def transform_hourly_to_half_hourly(output_rows, time_labels):
    """
    Detecta si los datos generados están en horas (ej: 08:00, 09:00) y los 
    convierte a 30 minutos (08:00, 08:30) dividiendo el volumen a la mitad.
    """
    if not output_rows or not time_labels or len(time_labels) < 2:
        return output_rows, time_labels

    # Detección simple: diferencia de 1 hora entre los dos primeros labels
    try:
        t1 = datetime.datetime.strptime(time_labels[0], '%H:%M')
        t2 = datetime.datetime.strptime(time_labels[1], '%H:%M')
        is_hourly = (t2 - t1).total_seconds() == 3600
    except:
        is_hourly = False

    if not is_hourly:
        return output_rows, time_labels # Ya es 30 min o irregular, devolver tal cual

    # Transformación
    new_rows = []
    new_labels = []

    # Generar headers de 30 min
    for lbl in time_labels:
        t = datetime.datetime.strptime(lbl, '%H:%M')
        new_labels.append(t.strftime('%H:%M'))
        new_labels.append((t + datetime.timedelta(minutes=30)).strftime('%H:%M'))
    new_labels = sorted(list(set(new_labels)))

    for row in output_rows:
        # Copiar metadata
        new_r = {k:v for k,v in row.items() if ':' not in str(k)}
        
        for lbl in time_labels:
            vol = row.get(lbl, 0)
            v1 = vol // 2
            v2 = vol - v1 # El resto va a la segunda media hora
            
            t_start = datetime.datetime.strptime(lbl, '%H:%M')
            lbl_30 = (t_start + datetime.timedelta(minutes=30)).strftime('%H:%M')
            
            new_r[lbl] = v1
            new_r[lbl_30] = v2
            
        new_rows.append(new_r)
        
    return new_rows, new_labels