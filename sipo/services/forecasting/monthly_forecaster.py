"""
Módulo de pronóstico mensual.
Contiene la lógica para generar proyecciones mensuales basadas en datos históricos.
"""

import pandas as pd
import numpy as np
import datetime
from calendar import monthrange
import logging
from .excel_parser import ExcelParserUtils

logger = logging.getLogger(__name__)


class MonthlyForecaster:
    """
    Genera proyecciones mensuales basadas en patrones históricos y tendencias.
    """

    def __init__(self):
        self.parser = ExcelParserUtils()

    def calculate_forecast(self, historical_file, holidays_file, recency_weight, 
                          manual_overrides, year_weights_dict):
        """
        Genera una proyección mensual basada en históricos.
        
        Args:
            historical_file: Archivo Excel con datos históricos
            holidays_file: Archivo Excel con festivos (opcional)
            recency_weight (float): Peso para datos recientes (0-1)
            manual_overrides (dict): Sobrescrituras manuales
            year_weights_dict (dict): Pesos por año
            
        Returns:
            dict: Diccionario con pivot, forecast y metadata
            
        Raises:
            ValueError: Si no se pueden procesar los datos
        """
        try:
            # 1. Cargar Festivos
            holidays_set = self._load_holidays(holidays_file)

            # 2. Cargar Histórico
            df, vol_col = self._load_historical_data(historical_file)
            
            # Filtrar meses incompletos
            df = self._filter_incomplete_months(df)
            
            if df.empty:
                raise ValueError("No se encontraron datos de meses completos en el archivo histórico.")

            # 3. Agrupar por Mes
            df_monthly = self._aggregate_monthly(df, vol_col, holidays_set)
            
            acwd_pivot = df_monthly.pivot_table(index='year', columns='month', values='acwd').fillna(0)
            calls_pivot = df_monthly.pivot_table(index='year', columns='month', values=vol_col).fillna(0)

            # 4. Aplicar Manual Overrides
            self._apply_manual_overrides(acwd_pivot, calls_pivot, manual_overrides, holidays_set)
            
            # 5. Calcular Crecimiento MoM
            avg_historical_mom_growth = self._calculate_mom_growth(acwd_pivot, year_weights_dict)
            
            # 6. Proyección
            last_real_date = df['Fecha'].max()
            current_year = last_real_date.year
            last_real_month = last_real_date.month
            target_year = current_year + 1
            
            projected_acwd_pivot = self._project_acwd(
                acwd_pivot, avg_historical_mom_growth, recency_weight,
                current_year, last_real_month, target_year
            )

            # 7. Convertir a Volumen
            final_calls_pivot = self._convert_to_volume(
                calls_pivot, projected_acwd_pivot, holidays_set,
                current_year, last_real_month, target_year, manual_overrides
            )

            # 8. Formatear resultado
            return self._format_result(
                final_calls_pivot, current_year, target_year, last_real_month
            )
            
        except Exception as e:
            logger.error(f"Error en calculate_monthly_forecast: {e}")
            raise

    def _load_holidays(self, holidays_file):
        """Carga el conjunto de fechas festivas."""
        holidays_set = set()
        if holidays_file:
            df_holidays = pd.read_excel(holidays_file)
            df_holidays = self.parser.find_header_and_normalize(df_holidays)
            df_holidays.columns = [str(c).strip() for c in df_holidays.columns]
            fecha_col = self.parser.detect_date_column(df_holidays)
            holidays_set = set(
                pd.to_datetime(df_holidays[fecha_col], dayfirst=True, errors='coerce').dt.date
            )
        return holidays_set

    def _load_historical_data(self, historical_file):
        """Carga y normaliza el archivo histórico."""
        df = pd.read_excel(historical_file)
        df = self.parser.find_header_and_normalize(df)
        df.columns = [str(col).strip() for col in df.columns]
        
        fecha_col = self.parser.detect_date_column(df)
        df[fecha_col] = pd.to_datetime(df[fecha_col], dayfirst=True, errors='coerce')
        df.dropna(subset=[fecha_col], inplace=True)
        
        vol_col = self.parser.detect_volume_column(df, exclude_cols=[fecha_col])
        if not vol_col:
            vol_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]
        
        df[vol_col] = pd.to_numeric(df[vol_col], errors='coerce').fillna(0)
        df.rename(columns={fecha_col: 'Fecha'}, inplace=True)
        
        return df, vol_col

    def _filter_incomplete_months(self, df):
        """Elimina el último mes si está incompleto."""
        if not df.empty:
            last_data_point_date = df['Fecha'].max()
            if last_data_point_date.day != last_data_point_date.days_in_month:
                df = df[~(
                    (df['Fecha'].dt.year == last_data_point_date.year) & 
                    (df['Fecha'].dt.month == last_data_point_date.month)
                )]
        return df

    def _aggregate_monthly(self, df, vol_col, holidays_set):
        """Agrupa datos diarios por mes y calcula ACWD."""
        df_monthly = df.groupby(pd.Grouper(key='Fecha', freq='ME'))[vol_col].sum().reset_index()
        df_monthly['year'] = df_monthly['Fecha'].dt.year
        df_monthly['month'] = df_monthly['Fecha'].dt.month
        df_monthly['working_days'] = df_monthly.apply(
            lambda row: self._get_working_days(row['year'], row['month'], holidays_set), 
            axis=1
        )
        df_monthly['acwd'] = df_monthly.apply(
            lambda row: row[vol_col] / row['working_days'] if row['working_days'] > 0 else 0, 
            axis=1
        )
        return df_monthly

    def _get_working_days(self, year, month, holidays):
        """Calcula el número de días laborables en un mes."""
        days_in_month = monthrange(year, month)[1]
        return sum(
            1 for day in range(1, days_in_month + 1) 
            if datetime.date(year, month, day).weekday() < 5 
            and datetime.date(year, month, day) not in holidays
        )

    def _apply_manual_overrides(self, acwd_pivot, calls_pivot, manual_overrides, holidays_set):
        """Aplica sobrescrituras manuales a los pivotes."""
        if manual_overrides:
            for key, value in manual_overrides.items():
                try:
                    year, month = map(int, key.split('-'))
                    workdays = self._get_working_days(year, month, holidays_set)
                    if year in acwd_pivot.index and month in acwd_pivot.columns:
                        acwd_pivot.loc[year, month] = float(value) / workdays if workdays > 0 else 0
                        calls_pivot.loc[year, month] = float(value)
                except (ValueError, KeyError):
                    continue

    def _calculate_mom_growth(self, acwd_pivot, year_weights_dict):
        """Calcula el crecimiento MoM promedio ponderado."""
        mom_growth_pivot = acwd_pivot.pct_change(axis='columns')
        mom_growth_pivot.replace([np.inf, -np.inf], np.nan, inplace=True)
        invalid_growth_mask = (acwd_pivot == 0) | (acwd_pivot.shift(1, axis='columns') == 0)
        mom_growth_pivot[invalid_growth_mask] = np.nan
        
        full_years_mom_growth = mom_growth_pivot[mom_growth_pivot.index < mom_growth_pivot.index.max()]
        
        year_weights_dict = {int(k): v for k, v in year_weights_dict.items() if v > 0}
        
        if year_weights_dict and not full_years_mom_growth.empty:
            valid_years = {year for year in year_weights_dict.keys() if year in full_years_mom_growth.index}
            if valid_years:
                weights_series = pd.Series(year_weights_dict)
                avg_historical_mom_growth = full_years_mom_growth.apply(
                    lambda col: self._weighted_nan_average(col, weights_series), axis=0
                )
            else:
                avg_historical_mom_growth = full_years_mom_growth.mean()
        else:
            if not full_years_mom_growth.empty:
                weights_series = pd.Series(
                    np.linspace(0.1, 1, len(full_years_mom_growth.index)), 
                    index=full_years_mom_growth.index
                )
                avg_historical_mom_growth = full_years_mom_growth.apply(
                    lambda col: self._weighted_nan_average(col, weights_series), axis=0
                )
            else:
                avg_historical_mom_growth = pd.Series(0, index=range(1, 13))
                
        avg_historical_mom_growth.fillna(0, inplace=True)
        return avg_historical_mom_growth

    def _weighted_nan_average(self, series, weights):
        """Calcula promedio ponderado ignorando NaN."""
        valid_indices = series.notna()
        if not valid_indices.any():
            return 0
        valid_series = series[valid_indices]
        valid_weights = weights.reindex(valid_series.index).fillna(0)
        if valid_weights.sum() == 0:
            return valid_series.mean() if not valid_series.empty else 0
        return np.average(valid_series, weights=valid_weights)

    def _project_acwd(self, acwd_pivot, avg_historical_mom_growth, recency_weight,
                      current_year, last_real_month, target_year):
        """Proyecta el ACWD para los meses futuros."""
        projected_acwd_pivot = acwd_pivot.copy().replace(np.nan, 0)
        if current_year not in projected_acwd_pivot.index:
            projected_acwd_pivot.loc[current_year] = 0
        if target_year not in projected_acwd_pivot.index:
            projected_acwd_pivot.loc[target_year] = 0

        # Proyectar año actual
        for m in range(last_real_month + 1, 13):
            projected_acwd = self._calculate_projected_acwd(
                projected_acwd_pivot, current_year, m, 
                avg_historical_mom_growth, recency_weight
            )
            projected_acwd_pivot.loc[current_year, m] = projected_acwd

        # Proyectar target year
        for m in range(1, 13):
            prev_month, prev_year = (m - 1, target_year) if m > 1 else (12, current_year)
            projected_acwd = self._calculate_projected_acwd_for_target(
                projected_acwd_pivot, prev_year, prev_month, m,
                avg_historical_mom_growth, recency_weight, current_year, target_year
            )
            projected_acwd_pivot.loc[target_year, m] = projected_acwd
        
        return projected_acwd_pivot

    def _calculate_projected_acwd(self, pivot, year, month, avg_growth, recency_weight):
        """Calcula el ACWD proyectado para un mes específico."""
        previous_month_acwd = pivot.loc[year, month - 1]
        m_minus_2_acwd = pivot.loc[year, month - 2] if month > 1 else 0
        recent_mom_growth = (previous_month_acwd - m_minus_2_acwd) / m_minus_2_acwd if m_minus_2_acwd > 0 else 0
        historical_mom_growth = avg_growth.get(month, 0)
        combined_growth = (recent_mom_growth * recency_weight) + (historical_mom_growth * (1 - recency_weight))
        projected_acwd = previous_month_acwd * (1 + combined_growth)
        return projected_acwd if projected_acwd > 0 else 0

    def _calculate_projected_acwd_for_target(self, pivot, prev_year, prev_month, month,
                                             avg_growth, recency_weight, current_year, target_year):
        """Calcula el ACWD proyectado para el año objetivo."""
        previous_month_acwd = pivot.loc[prev_year, prev_month]
        m_minus_2_month, m_minus_2_year = (prev_month - 1, prev_year) if prev_month > 1 else (11, current_year)
        try:
            m_minus_2_acwd = pivot.loc[m_minus_2_year, m_minus_2_month]
        except KeyError:
            m_minus_2_acwd = 0
        recent_mom_growth = (previous_month_acwd - m_minus_2_acwd) / m_minus_2_acwd if m_minus_2_acwd > 0 else 0
        historical_mom_growth = avg_growth.get(month, 0)
        combined_growth = (recent_mom_growth * recency_weight) + (historical_mom_growth * (1 - recency_weight))
        projected_acwd = previous_month_acwd * (1 + combined_growth)
        return projected_acwd if projected_acwd > 0 else 0

    def _convert_to_volume(self, calls_pivot, projected_acwd_pivot, holidays_set,
                           current_year, last_real_month, target_year, manual_overrides):
        """Convierte ACWD proyectado a volumen de llamadas."""
        final_calls_pivot = calls_pivot.copy().replace(np.nan, 0)
        if target_year not in final_calls_pivot.index:
            final_calls_pivot.loc[target_year] = 0
        
        for year in [current_year, target_year]:
            for month in range(1, 13):
                if year == current_year and month <= last_real_month and f"{year}-{month}" not in manual_overrides:
                    continue
                acwd = projected_acwd_pivot.loc[year, month]
                workdays = self._get_working_days(year, month, holidays_set)
                final_calls_pivot.loc[year, month] = acwd * workdays
        
        return final_calls_pivot

    def _format_result(self, final_calls_pivot, current_year, target_year, last_real_month):
        """Formatea el resultado final."""
        final_pivot_json = {
            str(year): {str(month): val for month, val in row.items()} 
            for year, row in final_calls_pivot.to_dict(orient='index').items()
        }
        current_year_forecast_json = {
            str(m): final_calls_pivot.loc[current_year, m] 
            for m in range(1, 13) if m > last_real_month
        }
        forecast_json = {
            str(m): final_calls_pivot.loc[target_year, m] 
            for m in range(1, 13)
        }
            
        return {
            'pivot': final_pivot_json,
            'current_year_forecast': current_year_forecast_json,
            'forecast': forecast_json,
            'target_year': target_year,
            'current_year': current_year,
            'last_real_month': last_real_month
        }
