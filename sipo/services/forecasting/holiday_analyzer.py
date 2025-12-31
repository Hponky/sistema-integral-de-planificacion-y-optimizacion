"""
Módulo de análisis de distribución para festivos.
Contiene la lógica para analizar patrones de comportamiento en días festivos.
"""

import pandas as pd
import numpy as np
import logging
from .excel_parser import ExcelParserUtils

logger = logging.getLogger(__name__)


class HolidayAnalyzer:
    """
    Analiza patrones de distribución para días festivos basado en datos históricos.
    """

    def __init__(self):
        self.parser = ExcelParserUtils()

    def analyze_distribution(self, historical_file, holidays_file):
        """
        Analiza un archivo histórico buscando fechas que coincidan con los festivos cargados.
        Agrupa los resultados por el nombre de la festividad.
        
        Args:
            historical_file: Archivo Excel con datos históricos
            holidays_file: Archivo Excel con fechas de festivos
            
        Returns:
            dict: Diccionario con holiday_data y labels
            
        Raises:
            ValueError: Si no se pueden procesar los datos
        """
        try:
            # 1. Cargar Festivos
            df_holidays = pd.read_excel(holidays_file)
            df_holidays = self.parser.find_header_and_normalize(
                df_holidays, 
                keywords=['fecha', 'date', 'festivo', 'nombre']
            )
            df_holidays.columns = [str(col).strip() for col in df_holidays.columns]
            
            # Normalizar nombres de columnas
            fecha_col_h = self.parser.detect_date_column(df_holidays)
            nombre_col = self._detect_holiday_name_column(df_holidays)
            
            df_holidays[fecha_col_h] = pd.to_datetime(
                df_holidays[fecha_col_h], dayfirst=True, errors='coerce'
            )
            df_holidays.dropna(subset=[fecha_col_h], inplace=True)
            
            # 2. Cargar Histórico
            df = pd.read_excel(historical_file)
            df = self.parser.prepare_historical_dataframe(df)
            
            # 3. Cruzar datos
            df['Fecha_join'] = df['Fecha'].dt.date
            df_holidays['Fecha_join'] = df_holidays[fecha_col_h].dt.date
            
            df_merged = pd.merge(
                df, 
                df_holidays[[nombre_col, 'Fecha_join']], 
                on='Fecha_join', 
                how='inner'
            )
            
            if df_merged.empty:
                return {"holiday_data": {}, "labels": []}
            
            # Crear tabla dinámica
            df_pivot = df_merged.pivot_table(
                index=['Fecha', nombre_col], 
                columns='Intervalo', 
                values='Llamadas Ofrecidas', 
                aggfunc='sum'
            ).fillna(0)
            
            time_labels = sorted([col for col in df_pivot.columns if ':' in str(col)])
            df_pivot.reset_index(inplace=True)
            
            holiday_data = self._process_holiday_data(df_pivot, nombre_col, time_labels)
                
            return {"holiday_data": holiday_data, "labels": time_labels}
            
        except Exception as e:
            logger.error(f"Error en analyze_holiday_distribution: {e}")
            raise

    def _detect_holiday_name_column(self, df):
        """
        Detecta la columna con el nombre del festivo.
        
        Args:
            df (pd.DataFrame): DataFrame de festivos
            
        Returns:
            str: Nombre de la columna detectada
        """
        for c in df.columns:
            col_lower = str(c).lower()
            if 'festividad' in col_lower or 'nombre' in col_lower or 'festivo' in col_lower:
                return c
        return 'Nombre de la festividad'

    def _process_holiday_data(self, df_pivot, nombre_col, time_labels):
        """
        Procesa los datos de festivos agrupados por nombre.
        
        Args:
            df_pivot (pd.DataFrame): DataFrame pivoteado con datos
            nombre_col (str): Nombre de la columna con el nombre del festivo
            time_labels (list): Lista de etiquetas de tiempo
            
        Returns:
            dict: Datos de festivos organizados por nombre
        """
        holiday_data = {}
        
        for holiday_name in df_pivot[nombre_col].unique():
            holiday_group_df = df_pivot[
                df_pivot[nombre_col] == holiday_name
            ].sort_values(by='Fecha', ascending=False)
            
            # Para simplificar, usamos pesos equitativos para festivos
            weight_per_instance = 100.0 / len(holiday_group_df) if not holiday_group_df.empty else 0
            
            instances = []
            for index, row in holiday_group_df.iterrows():
                intraday_raw_calls = row[time_labels].to_dict()
                total_calls = sum(intraday_raw_calls.values())
                intraday_percentages = {
                    k: (v / total_calls if total_calls > 0 else 0) 
                    for k, v in intraday_raw_calls.items()
                }
                
                instances.append({
                    'week': int(row['Fecha'].isocalendar().week),
                    'year': int(row['Fecha'].year),
                    'date': row['Fecha'].strftime('%d/%m/%Y'),
                    'total_calls': total_calls,
                    'is_outlier': False,
                    'proposed_weight': round(weight_per_instance),
                    'intraday_dist': intraday_percentages,
                    'intraday_raw': intraday_raw_calls
                })
            
            holiday_data[holiday_name] = instances
        
        return holiday_data
