"""
Servicio de Forecasting (Legacy Wrapper).
Este módulo ahora actúa como un puente hacia la nueva implementación modular en services/forecasting/.
"""

import logging
from .forecasting_facade import ForecastingService as NewForecastingService

logger = logging.getLogger(__name__)

class ForecastingService:
    """
    Wrapper que mantiene la interfaz original pero delega la lógica a la nueva implementación.
    Esto permite una transición suave sin romper las rutas existentes.
    """

    def __init__(self):
        self._service = NewForecastingService()

    def analyze_intraday_distribution(self, historical_file, weeks_to_analyze):
        return self._service.analyze_intraday_distribution(historical_file, weeks_to_analyze)

    def analyze_holiday_distribution(self, historical_file, holidays_file):
        return self._service.analyze_holiday_distribution(historical_file, holidays_file)

    def build_weighted_curve(self, weights, day_of_week, all_weekly_data, labels):
        return self._service.build_weighted_curve(weights, day_of_week, all_weekly_data, labels)

    def analyze_specific_date_historically(self, historical_file, target_date_str):
        return self._service.analyze_specific_date_historically(historical_file, target_date_str)

    def analyze_specific_date_curve(self, historical_file, specific_date_str):
        return self._service.analyze_specific_date_curve(historical_file, specific_date_str)

    def calculate_monthly_forecast(self, historical_file, holidays_file, recency_weight, 
                                  manual_overrides, year_weights_dict):
        return self._service.calculate_monthly_forecast(
            historical_file, holidays_file, recency_weight, manual_overrides, year_weights_dict
        )

    def distribute_intramonth_forecast(self, monthly_volume_df, historical_file, holidays_file):
        return self._service.distribute_intramonth_forecast(monthly_volume_df, historical_file, holidays_file)

    def distribute_intraday_volume(self, forecast_file, holidays_file, curves_data):
        return self._service.distribute_intraday_volume(forecast_file, holidays_file, curves_data)

    def save_forecast_scenario(self, segment_id, name, timeframe_data, user_info=None):
        return self._service.save_forecast_scenario(segment_id, name, timeframe_data, user_info)

    def transform_hourly_to_half_hourly(self, output_rows, time_labels):
        return self._service.transform_hourly_to_half_hourly(output_rows, time_labels)

    def export_curve_to_excel(self, final_curve, labels):
        return self._service.export_curve_to_excel(final_curve, labels)

    def export_all_curves_to_excel(self, curves_by_day, time_labels):
        return self._service.export_all_curves_to_excel(curves_by_day, time_labels)

    def save_forecasting_curves(self, segment_id, name, curves_by_day, time_labels, 
                               user_info=None, weeks_analyzed=None, date_range=None):
        return self._service.save_forecasting_curves(
            segment_id, name, curves_by_day, time_labels, user_info, weeks_analyzed, date_range
        )

    def delete_curve(self, curve_id):
        return self._service.delete_curve(curve_id)

    def get_distributions_by_segment(self, segment_id):
        return self._service.get_distributions_by_segment(segment_id)

    def delete_distribution(self, dist_id):
        return self._service.delete_distribution(dist_id)

    def select_distribution(self, dist_id):
        return self._service.select_distribution(dist_id)

    def get_forecasting_curves_by_segment(self, segment_id):
        return self._service.get_forecasting_curves_by_segment(segment_id)

    def get_forecasting_curve_by_id(self, curve_id):
        return self._service.get_forecasting_curve_by_id(curve_id)

    def export_intraday_distribution_to_excel(self, output_rows, time_labels):
        return self._service.export_intraday_distribution_to_excel(output_rows, time_labels)

    def generate_expected_calls_from_curves(self, curve_id, start_date, end_date, daily_volumes=None):
        return self._service.generate_expected_calls_from_curves(curve_id, start_date, end_date, daily_volumes)

    def parse_expected_calls_file(self, file_source):
        return self._service.parse_expected_calls_file(file_source)
