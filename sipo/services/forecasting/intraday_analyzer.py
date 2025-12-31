"""
Módulo de análisis de distribución intradía.
Contiene la lógica para analizar patrones de comportamiento por día de la semana.
"""

import pandas as pd
import numpy as np
import logging
from .excel_parser import ExcelParserUtils

logger = logging.getLogger(__name__)


class IntradayAnalyzer:
    """
    Analiza patrones de distribución intradía basados en datos históricos.
    Identifica tendencias, outliers y calcula pesos propuestos para cada semana.
    """

    def __init__(self):
        self.parser = ExcelParserUtils()

    def analyze_distribution(self, historical_file, weeks_to_analyze):
        """
        Analiza un archivo histórico para detectar patrones de comportamiento por día de la semana.
        
        Args:
            historical_file: Archivo Excel con datos históricos
            weeks_to_analyze (int): Número de semanas a analizar
            
        Returns:
            dict: Diccionario con weekly_data y labels
            
        Raises:
            ValueError: Si no se pueden procesar los datos
        """
        try:
            df = pd.read_excel(historical_file)
            df = self.parser.prepare_historical_dataframe(df)
            
            # Filtrar por semanas recientes
            max_date = df['Fecha'].max()
            if pd.isna(max_date):
                raise ValueError("No se encontraron fechas válidas en los datos.")
            
            weeks_ago_date = max_date - pd.to_timedelta((weeks_to_analyze * 7) - 1, unit='d')
            df_filtered = df[df['Fecha'] >= weeks_ago_date]

            if df_filtered.empty:
                raise ValueError(f"No se encontraron datos en el rango de las últimas {weeks_to_analyze} semanas.")
            
            # Crear tabla dinámica
            df_pivot = df_filtered.pivot_table(
                index='Fecha', 
                columns='Intervalo', 
                values='Llamadas Ofrecidas', 
                aggfunc='sum'
            ).fillna(0)
            
            time_labels = sorted([col for col in df_pivot.columns if ':' in str(col)])
            
            df_pivot.reset_index(inplace=True)
            df_pivot['day_of_week'] = df_pivot['Fecha'].dt.weekday
            df_pivot['week_number'] = df_pivot['Fecha'].dt.isocalendar().week
            
            weekly_data = self._process_weekly_data(df_pivot, time_labels)
                    
            return {"weekly_data": weekly_data, "labels": time_labels}
            
        except Exception as e:
            logger.error(f"Error en analyze_intraday_distribution: {e}")
            raise

    def _process_weekly_data(self, df_pivot, time_labels):
        """
        Procesa los datos semanales agrupados por día de la semana.
        
        Args:
            df_pivot (pd.DataFrame): DataFrame pivoteado con datos
            time_labels (list): Lista de etiquetas de tiempo
            
        Returns:
            dict: Datos semanales organizados por día
        """
        weekly_data = {i: [] for i in range(7)}
        
        for day_num in range(7):
            day_group_df = df_pivot[df_pivot['day_of_week'] == day_num].sort_values(
                by='Fecha', ascending=False
            )
            if day_group_df.empty:
                continue
            
            # Calcular curvas porcentuales
            day_curves = day_group_df[time_labels].div(
                day_group_df[time_labels].sum(axis=1), axis=0
            ).fillna(0)
            
            # Detección de outliers y cálculo de pesos
            is_outlier = self._detect_outliers(day_curves, day_group_df, time_labels)
            weights = self._calculate_weights(day_curves, is_outlier)
            
            # Preparar datos para el frontend
            for index, row in day_group_df.iterrows():
                intraday_raw_calls = row[time_labels].to_dict()
                total_calls = sum(intraday_raw_calls.values())
                intraday_percentages = {
                    k: (v / total_calls if total_calls > 0 else 0) 
                    for k, v in intraday_raw_calls.items()
                }
                
                weekly_data[day_num].append({
                    'week': int(row['week_number']),
                    'date': row['Fecha'].strftime('%d/%m/%Y'),
                    'total_calls': total_calls,
                    'is_outlier': bool(is_outlier.get(index, False)),
                    'proposed_weight': round(weights.get(index, 0)),
                    'intraday_dist': intraday_percentages,
                    'intraday_raw': intraday_raw_calls
                })
        
        return weekly_data

    def _detect_outliers(self, day_curves, day_group_df, time_labels):
        """
        Detecta outliers basándose en la desviación respecto a la mediana.
        
        Args:
            day_curves (pd.DataFrame): Curvas porcentuales del día
            day_group_df (pd.DataFrame): DataFrame del grupo del día
            time_labels (list): Lista de etiquetas de tiempo
            
        Returns:
            pd.Series: Serie booleana indicando outliers
        """
        is_outlier = pd.Series([False] * len(day_curves), index=day_curves.index)
        
        if len(day_curves) >= 2:
            valid_day_curves = day_curves[day_group_df[time_labels].sum(axis=1) > 0]
            if not valid_day_curves.empty:
                reference_curve = valid_day_curves.median()
                deviations = ((day_curves - reference_curve) ** 2).mean(axis=1)
                
                if len(deviations) >= 4:
                    q1, q3 = deviations.quantile(0.25), deviations.quantile(0.75)
                    iqr = q3 - q1
                    is_outlier = (deviations > q3 + 1.5 * iqr)
        
        return is_outlier

    def _calculate_weights(self, day_curves, is_outlier):
        """
        Calcula los pesos propuestos para cada semana.
        
        Lógica:
        1. Outliers reciben peso 0
        2. Semanas válidas reciben peso basado en:
           - Recencia (más reciente = más peso)
           - Similitud con la mediana (menor desviación = más peso)
        
        Args:
            day_curves (pd.DataFrame): Curvas porcentuales del día
            is_outlier (pd.Series): Serie indicando outliers
            
        Returns:
            pd.Series: Pesos calculados para cada semana
        """
        weights = pd.Series([0.0] * len(day_curves), index=day_curves.index)
        
        # Filtrar solo las semanas válidas (no outliers)
        valid_indices = [idx for idx, val in is_outlier.items() if not val]
        
        if valid_indices:
            valid_day_curves = day_curves.loc[valid_indices]
            
            if len(valid_day_curves) > 0:
                reference_curve = valid_day_curves.median()
                deviations = ((valid_day_curves - reference_curve) ** 2).mean(axis=1)
                
                # Normalizar desviaciones (invertir: menor desviación = mayor score)
                max_dev = deviations.max()
                if max_dev > 0:
                    similarity_scores = 1 - (deviations / max_dev)
                else:
                    similarity_scores = pd.Series([1.0] * len(valid_indices), index=valid_indices)
                
                # Factor de recencia (más reciente = mayor peso)
                recency_scores = pd.Series(
                    [i / (len(valid_indices) - 1) if len(valid_indices) > 1 else 1.0
                     for i in range(len(valid_indices))],
                    index=valid_indices
                )
                
                # Combinar scores: 60% similitud + 40% recencia
                combined_scores = (similarity_scores * 0.6) + (recency_scores * 0.4)
                
                # Normalizar a 100%
                total_score = combined_scores.sum()
                if total_score > 0:
                    for idx in valid_indices:
                        weights[idx] = (combined_scores[idx] / total_score) * 100.0
                else:
                    self._distribute_weights_equally(weights, valid_indices)
            else:
                self._distribute_weights_equally(weights, valid_indices)
        elif len(day_curves) > 0:
            # Si todos son outliers (caso raro), distribución equitativa
            weights = pd.Series([100.0 / len(day_curves)] * len(day_curves), index=day_curves.index)
        
        return weights

    def _distribute_weights_equally(self, weights, indices):
        """
        Distribuye pesos equitativamente entre los índices dados.
        
        Args:
            weights (pd.Series): Serie de pesos a modificar
            indices (list): Índices a los que asignar pesos
        """
        weight_per_valid = 100.0 / len(indices) if indices else 0
        for idx in indices:
            weights[idx] = weight_per_valid

    def analyze_specific_date_historically(self, historical_file, target_date_str):
        """
        Busca en el histórico el comportamiento de una fecha específica (día y mes).
        
        Args:
            historical_file: Archivo Excel con datos históricos
            target_date_str (str): Fecha objetivo para buscar coincidencias (DD-MM-YYYY)
            
        Returns:
            dict: Datos históricos encontrados para ese día/mes en años previos
        """
        try:
            df = pd.read_excel(historical_file)
            df = self.parser.prepare_historical_dataframe(df)

            try:
                target_dt = pd.to_datetime(target_date_str)
                target_month = target_dt.month
                target_day = target_dt.day
            except:
                raise ValueError("Formato de fecha objetivo inválido.")

            history_matches = df[
                (df['Fecha'].dt.month == target_month) & 
                (df['Fecha'].dt.day == target_day)
            ].copy()

            if history_matches.empty:
                raise ValueError(f"No se encontraron datos históricos para el día {target_day}/{target_month} en el archivo.")

            df_pivot = history_matches.pivot_table(index='Fecha', columns='Intervalo', values='Llamadas Ofrecidas', aggfunc='sum').fillna(0)
            time_labels = sorted([col for col in df_pivot.columns if ':' in str(col)])
            
            historical_data = []
            dias_es = {
                'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
                'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
            }
            
            for date_idx, row in df_pivot.iterrows():
                raw_calls = row[time_labels].to_dict()
                total_calls = sum(raw_calls.values())
                intraday_dist = {k: (v / total_calls if total_calls > 0 else 0) for k, v in raw_calls.items()}
                
                day_name_en = date_idx.strftime('%A')
                historical_data.append({
                    'date': date_idx.strftime('%Y-%m-%d'),
                    'year': date_idx.year,
                    'day_name': dias_es.get(day_name_en, day_name_en),
                    'total_calls': total_calls,
                    'intraday_dist': intraday_dist,
                    'intraday_raw': raw_calls
                })

            historical_data.sort(key=lambda x: x['year'], reverse=True)

            return {
                "historical_data": historical_data,
                "labels": time_labels,
                "target_date_display": f"{target_day}/{target_month}"
            }
        except Exception as e:
            logger.error(f"Error en analyze_specific_date_historically: {e}")
            raise

    def analyze_specific_date_curve(self, historical_file, specific_date_str):
        """
        Obtiene la curva exacta de una fecha pasada específica.
        
        Args:
            historical_file: Archivo Excel con datos históricos
            specific_date_str (str): Fecha específica (YYYY-MM-DD)
            
        Returns:
            dict: Datos de la curva para esa fecha
        """
        try:
            df = pd.read_excel(historical_file)
            df = self.parser.prepare_historical_dataframe(df)

            try:
                target_date = pd.to_datetime(specific_date_str).date()
            except:
                raise ValueError("Fecha específica inválida.")

            day_data = df[df['Fecha'].dt.date == target_date]

            if day_data.empty:
                raise ValueError(f"No se encontraron datos para la fecha {specific_date_str} en el archivo histórico.")

            grouped_data = day_data.groupby('Intervalo')['Llamadas Ofrecidas'].sum()
            
            total_volume = grouped_data.sum()
            if total_volume == 0:
                raise ValueError(f"El volumen para el día {specific_date_str} es 0.")

            curve_distribution = (grouped_data / total_volume).to_dict()
            time_labels = sorted(list(curve_distribution.keys()))
            
            return {
                "date": specific_date_str,
                "total_volume": total_volume,
                "curve": curve_distribution,
                "labels": time_labels
            }
        except Exception as e:
            logger.error(f"Error en analyze_specific_date_curve: {e}")
            raise
