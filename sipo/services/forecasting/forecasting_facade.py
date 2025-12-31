"""
Fachada principal para el servicio de Forecasting.
Orquesta los diferentes módulos especializados para ofrecer una interfaz unificada.
"""

import logging
import io
import pandas as pd
from .excel_parser import ExcelParserUtils
from .intraday_analyzer import IntradayAnalyzer
from .holiday_analyzer import HolidayAnalyzer
from .monthly_forecaster import MonthlyForecaster
from .distribution_service import VolumeDistributor
from .curve_builder import CurveBuilder
from .curve_repository import CurveRepository
from .excel_exporter import ExcelExporter

logger = logging.getLogger(__name__)


class ForecastingService:
    """
    Fachada que orquesta todas las funcionalidades de forecasting.
    """

    def __init__(self):
        self.parser = ExcelParserUtils()
        self.intraday_analyzer = IntradayAnalyzer()
        self.holiday_analyzer = HolidayAnalyzer()
        self.monthly_forecaster = MonthlyForecaster()
        self.distributor = VolumeDistributor()
        self.curve_builder = CurveBuilder()
        self.repository = CurveRepository()
        self.exporter = ExcelExporter()

    # --- Métodos de Análisis ---

    def analyze_intraday_distribution(self, historical_file, weeks_to_analyze):
        """Analiza patrones de comportamiento por día de la semana."""
        return self.intraday_analyzer.analyze_distribution(historical_file, weeks_to_analyze)

    def analyze_holiday_distribution(self, historical_file, holidays_file):
        """Analiza patrones en días festivos."""
        return self.holiday_analyzer.analyze_distribution(historical_file, holidays_file)

    def analyze_specific_date_historically(self, historical_file, target_date_str):
        """Busca el comportamiento de una fecha específica en el histórico."""
        return self.intraday_analyzer.analyze_specific_date_historically(historical_file, target_date_str)

    def analyze_specific_date_curve(self, historical_file, specific_date_str):
        """Obtiene la curva exacta de una fecha específica."""
        return self.intraday_analyzer.analyze_specific_date_curve(historical_file, specific_date_str)

    # --- Métodos de Construcción ---

    def build_weighted_curve(self, weights, day_of_week, all_weekly_data, labels):
        """Construye una curva representativa basada en pesos."""
        return self.curve_builder.build_weighted_curve(weights, day_of_week, all_weekly_data, labels)

    # --- Métodos de Forecasting y Distribución ---

    def calculate_monthly_forecast(self, historical_file, holidays_file, recency_weight, 
                                  manual_overrides, year_weights_dict):
        """Genera proyección mensual."""
        return self.monthly_forecaster.calculate_forecast(
            historical_file, holidays_file, recency_weight, manual_overrides, year_weights_dict
        )

    def distribute_intramonth_forecast(self, monthly_volume_df, historical_file, holidays_file):
        """Distribuye volumen mensual a diario."""
        return self.distributor.distribute_intramonth(monthly_volume_df, historical_file, holidays_file)

    def distribute_intraday_volume(self, forecast_file, holidays_file, curves_data):
        """Aplica curvas horarias a un archivo de volumen diario."""
        return self.distributor.distribute_intraday(forecast_file, holidays_file, curves_data)

    def transform_hourly_to_half_hourly(self, output_rows, time_labels):
        """Transforma intervalos de 1h a 30m."""
        return self.distributor.transform_hourly_to_half_hourly(output_rows, time_labels)

    # --- Métodos de Persistencia ---

    def save_forecasting_curves(self, segment_id, name, curves_by_day, time_labels, 
                               user_info=None, weeks_analyzed=None, date_range=None):
        """Guarda curvas en la base de datos."""
        return self.repository.save_curves(
            segment_id, name, curves_by_day, time_labels, user_info, weeks_analyzed, date_range
        )

    def get_forecasting_curves_by_segment(self, segment_id):
        """Obtiene curvas guardadas para un segmento."""
        return self.repository.get_by_segment(segment_id)

    def get_forecasting_curve_by_id(self, curve_id):
        """Obtiene una curva específica por ID."""
        return self.repository.get_by_id(curve_id)

    def save_forecast_scenario(self, segment_id, name, timeframe_data, user_info=None):
        """Guarda el resultado como un escenario de dimensionamiento."""
        return self.repository.save_scenario(segment_id, name, timeframe_data, user_info)

    def delete_curve(self, curve_id):
        """Elimina una curva de forecasting."""
        return self.repository.delete(curve_id)

    def get_distributions_by_segment(self, segment_id):
        """Obtiene distribuciones guardadas para un segmento."""
        return self.repository.get_distributions_by_segment(segment_id)

    def delete_distribution(self, dist_id):
        """Elimina una distribución de forecasting."""
        return self.repository.delete_distribution(dist_id)

    def select_distribution(self, dist_id):
        """Selecciona una distribución de forecasting."""
        return self.repository.select_distribution(dist_id)

    def save_distribution(self, segment_id, start_date, end_date, output_rows, time_labels, user_info=None, curve_id=None):
        """Guarda el resultado de la distribución forecasting (llamadas esperadas)."""
        return self.repository.save_distribution(
            segment_id, start_date, end_date, output_rows, time_labels, user_info, curve_id
        )

    # --- Métodos de Utilería y Generación ---

    def generate_expected_calls_from_curves(self, curve_id, start_date, end_date, daily_volumes=None):
        """Genera llamadas esperadas usando curvas guardadas."""
        from models import ForecastingCurve
        curve = ForecastingCurve.query.get(curve_id)
        if not curve:
            raise ValueError(f"No se encontró la curva con ID {curve_id}")
        return self.distributor.generate_expected_calls_from_curves(curve, start_date, end_date, daily_volumes)

    def parse_expected_calls_file(self, file_source):
        """Lee un archivo de llamadas esperadas y extrae totales diarios."""
        try:
            with pd.ExcelFile(file_source) as xls:
                # Buscar hoja relevante
                sheet_name = next((s for s in xls.sheet_names if any(k in s.lower() for k in ['llamadas_esperadas', 'volumen', 'llamada', 'proyeccion', 'forecast'])), None)
                if not sheet_name:
                    sheet_name = xls.sheet_names[0]
                df = pd.read_excel(xls, sheet_name=sheet_name)
            
            logger.info(f"Hoja detectada para llamadas esperadas: {sheet_name}")
            
            # Preparar y normalizar (solo requerimos Fecha y Llamadas Ofrecidas para totales diarios)
            df = self.parser.prepare_historical_dataframe(df, required_cols=['Fecha', 'Llamadas Ofrecidas'])
            
            # Detectar si hay columnas de tiempo (formato pivot) que sumen al total
            # Si prepare_historical_dataframe ya hizo pivot_to_flat, no habrá columnas de tiempo
            time_cols = self.parser.detect_time_columns(df, exclude_cols=['Fecha'])
            
            if not time_cols:
                # Caso: Tabla plana (Fecha, Intervalo?, Llamadas)
                vol_col = 'Llamadas Ofrecidas'
                daily_volumes = df.groupby(df['Fecha'].dt.date)[vol_col].sum().to_dict()
            else:
                # Caso: Tabla pivot (Fecha, 00:00, 00:30...)
                df['Total_Calls'] = df[time_cols].sum(axis=1)
                daily_volumes = df.groupby(df['Fecha'].dt.date)['Total_Calls'].sum().to_dict()

            # Convertir a formato final asegurando que las llaves sean strings
            result = {}
            for date_val, vol in daily_volumes.items():
                if hasattr(date_val, 'strftime'):
                    date_str = date_val.strftime('%Y-%m-%d')
                else:
                    date_str = str(date_val)
                result[date_str] = float(vol)
            
            logger.info(f"Parseo exitoso: {len(result)} días encontrados")
            return result
        except Exception as e:
            logger.error(f"Error parseando archivo de llamadas esperadas: {e}", exc_info=True)
            raise

    # --- Métodos de Exportación ---

    def export_curve_to_excel(self, final_curve, labels):
        """Exporta una curva ponderada a Excel."""
        return self.exporter.export_curve(final_curve, labels)

    def export_all_curves_to_excel(self, curves_by_day, time_labels):
        """Exporta todas las curvas semanales a Excel."""
        return self.exporter.export_all_curves(curves_by_day, time_labels)

    def export_intraday_distribution_to_excel(self, output_rows, time_labels):
        """Exporta la distribución intradía distribuida a Excel."""
        return self.exporter.export_intraday_distribution(output_rows, time_labels)

    def export_intramonth_distribution_to_excel(self, df_result):
        """Exporta la distribución mensual/diaria a Excel."""
        return self.exporter.export_intramonth_distribution(df_result)

    def get_full_time_labels(self, interval=30):
        """Genera la lista completa de etiquetas de tiempo para un día."""
        labels = []
        for h in range(24):
            for m in [0, 30] if interval == 30 else [0]:
                labels.append(f"{h:02d}:{m:02d}")
        return labels
