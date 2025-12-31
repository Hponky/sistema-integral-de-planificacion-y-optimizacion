"""
Módulo de distribución de volumen.
Contiene la lógica para distribuir volúmenes mensuales a diarios e intradía.
"""

import pandas as pd
import numpy as np
import datetime
from calendar import monthrange
import logging
from .excel_parser import ExcelParserUtils

logger = logging.getLogger(__name__)


class VolumeDistributor:
    """
    Distribuye volúmenes de llamadas desde niveles mensuales a diarios e intradía.
    """

    def __init__(self):
        self.parser = ExcelParserUtils()

    def distribute_intramonth(self, monthly_volume_df, historical_file, holidays_file):
        """
        Distribuye volumen mensual a diario basado en estacionalidad histórica.
        
        Args:
            monthly_volume_df (pd.DataFrame): DataFrame con año, mes y volumen
            historical_file: Archivo Excel con datos históricos
            holidays_file: Archivo Excel con festivos (opcional)
            
        Returns:
            pd.DataFrame: DataFrame con distribución diaria
            
        Raises:
            ValueError: Si no se pueden procesar los datos
        """
        try:
            # Cargar histórico
            df_hist = pd.read_excel(historical_file)
            df_hist = self.parser.find_header_and_normalize(df_hist)
            df_hist.columns = [str(col).strip() for col in df_hist.columns]
            
            fecha_col = self.parser.detect_date_column(df_hist)
            vol_col = self.parser.detect_volume_column(df_hist, exclude_cols=[fecha_col])
            if not vol_col:
                vol_col = next((c for c in df_hist.columns if c != fecha_col), df_hist.columns[0])
            
            df_hist[fecha_col] = pd.to_datetime(df_hist[fecha_col], errors='coerce', dayfirst=True)
            df_hist.dropna(subset=[fecha_col], inplace=True)
            df_hist[vol_col] = pd.to_numeric(df_hist[vol_col], errors='coerce').fillna(0)
            df_hist.rename(columns={fecha_col: 'Fecha'}, inplace=True)

            holidays_set = self._load_holidays(holidays_file)

            result_rows = []

            for _, row_req in monthly_volume_df.iterrows():
                target_year = int(row_req['año'])
                target_month = int(row_req['mes'])
                target_volume = float(row_req['volumen'])

                df_hist['Month'] = df_hist['Fecha'].dt.month
                df_hist['Day'] = df_hist['Fecha'].dt.day
                hist_month_data = df_hist[df_hist['Month'] == target_month]
                
                daily_weights = self._calculate_daily_weights(
                    hist_month_data, vol_col, target_year, target_month
                )

                month_rows = self._distribute_to_days(
                    target_year, target_month, target_volume, 
                    daily_weights, holidays_set
                )

                result_rows.extend(month_rows)

            return pd.DataFrame(result_rows)
            
        except Exception as e:
            logger.error(f"Error en distribute_intramonth_forecast: {e}")
            raise

    def distribute_intraday(self, forecast_file, holidays_file, curves_data):
        """
        Aplica curvas horarias a un archivo de volumen diario.
        
        Args:
            forecast_file: Archivo Excel con volúmenes diarios
            holidays_file: Archivo Excel con festivos (opcional)
            curves_data (dict): Diccionario con curves y labels
            
        Returns:
            tuple: (output_rows, time_labels)
            
        Raises:
            ValueError: Si no se pueden procesar los datos
        """
        try:
            curves_to_use = curves_data.get('curves', {})
            time_labels = curves_data.get('labels', [])
            
            holidays_set = self._load_holidays(holidays_file)

            df = pd.read_excel(forecast_file)
            df = self.parser.find_header_and_normalize(df)
            df.columns = [str(c).strip() for c in df.columns]
            
            fecha_col = self.parser.detect_date_column(df)
            vol_col = self.parser.detect_volume_column(df, exclude_cols=[fecha_col])
            
            if not vol_col:
                vol_col = next((c for c in df.columns if c != fecha_col), None)

            df[fecha_col] = pd.to_datetime(df[fecha_col], errors='coerce', dayfirst=True)
            df.dropna(subset=[fecha_col], inplace=True)
            
            output_rows = self._apply_curves_to_days(
                df, fecha_col, vol_col, curves_to_use, time_labels, holidays_set
            )
                
            return output_rows, time_labels
            
        except Exception as e:
            logger.error(f"Error en distribute_intraday_volume: {e}")
            raise

    def _load_holidays(self, holidays_file):
        """Carga el conjunto de fechas festivas."""
        holidays_set = set()
        if holidays_file:
            try:
                df_h = pd.read_excel(holidays_file)
                df_h = self.parser.find_header_and_normalize(df_h)
                df_h.columns = [str(c).strip() for c in df_h.columns]
                f_col = self.parser.detect_date_column(df_h)
                if f_col in df_h.columns:
                    holidays_set = set(
                        pd.to_datetime(df_h[f_col], dayfirst=True, errors='coerce').dt.date
                    )
            except:
                pass
        return holidays_set

    def _calculate_daily_weights(self, hist_month_data, vol_col, target_year, target_month):
        """Calcula los pesos diarios basados en datos históricos."""
        if hist_month_data.empty:
            _, days_in_month = monthrange(target_year, target_month)
            return {d: 1/days_in_month for d in range(1, days_in_month + 1)}
        else:
            daily_avgs = hist_month_data.groupby('Day')[vol_col].mean()
            return (daily_avgs / daily_avgs.sum()).to_dict()

    def _distribute_to_days(self, target_year, target_month, target_volume, 
                           daily_weights, holidays_set):
        """Distribuye el volumen mensual a días individuales."""
        _, num_days = monthrange(target_year, target_month)
        distributed_total = 0
        month_rows = []

        for day_num in range(1, num_days + 1):
            current_date = datetime.date(target_year, target_month, day_num)
            weight = daily_weights.get(day_num, 0)
            vol_for_day = round(target_volume * weight)
            distributed_total += vol_for_day
            
            month_rows.append({
                "Fecha": current_date.strftime('%Y-%m-%d'),
                "Volumen": vol_for_day,
                "EsFestivo": current_date in holidays_set
            })

        # Ajustar diferencia de redondeo
        diff = target_volume - distributed_total
        if diff != 0 and month_rows:
            month_rows.sort(key=lambda x: x['Volumen'], reverse=True)
            month_rows[0]['Volumen'] += diff
            month_rows.sort(key=lambda x: x['Fecha'])

        return month_rows

    def _apply_curves_to_days(self, df, fecha_col, vol_col, curves_to_use, 
                              time_labels, holidays_set):
        """Aplica las curvas intradía a cada día."""
        output_rows = []
        day_map = {
            0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 
            3: 'Jueves', 4: 'Viernes', 5: 'Sábado', 6: 'Domingo'
        }

        for _, row in df.iterrows():
            date_obj = row[fecha_col]
            vol = float(row[vol_col]) if vol_col in row and pd.notna(row[vol_col]) else 0
            
            if vol <= 0:
                continue

            date_str = date_obj.strftime('%Y-%m-%d')
            is_holiday = date_obj.date() in holidays_set
            weekday_str = str(date_obj.weekday())

            # Determinar qué curva usar
            curve_key = None
            if date_str in curves_to_use:
                curve_key = date_str
            elif is_holiday and 'holiday' in curves_to_use:
                curve_key = 'holiday'
            elif weekday_str in curves_to_use:
                curve_key = weekday_str
            
            if not curve_key:
                continue

            curve = curves_to_use[curve_key]
            
            new_row = {
                'Fecha': date_obj,
                'Dia': day_map.get(date_obj.weekday()),
                'Semana': date_obj.isocalendar()[1],
                'Tipo': 'FESTIVO' if is_holiday else 'N'
            }
            
            # Aplicar curva
            sum_dist = 0
            for t in time_labels:
                val = round(vol * curve.get(t, 0))
                new_row[t] = val
                sum_dist += val
            
            # Ajustar diferencia de redondeo
            diff = round(vol - sum_dist)
            if diff != 0:
                peak_interval = max(curve, key=curve.get)
                new_row[peak_interval] += diff
                
            output_rows.append(new_row)
        
        return output_rows

    def transform_hourly_to_half_hourly(self, output_rows, time_labels):
        """
        Convierte datos de 1h a 30m si es necesario.
        
        Args:
            output_rows (list): Lista de diccionarios con datos
            time_labels (list): Lista de etiquetas de tiempo
            
        Returns:
            tuple: (output_rows, time_labels) transformados
        """
        if not output_rows or not time_labels:
            return output_rows, time_labels
        
        # Detectar si el intervalo es de 1 hora
        if len(time_labels) >= 2:
            first_minutes = int(time_labels[0].split(':')[0]) * 60 + int(time_labels[0].split(':')[1])
            second_minutes = int(time_labels[1].split(':')[0]) * 60 + int(time_labels[1].split(':')[1])
            interval_minutes = second_minutes - first_minutes
            
            if interval_minutes == 60:
                # Transformar a 30 minutos
                new_time_labels = []
                for label in time_labels:
                    hour = int(label.split(':')[0])
                    new_time_labels.append(f"{hour:02d}:00")
                    new_time_labels.append(f"{hour:02d}:30")
                
                new_output_rows = []
                for row in output_rows:
                    new_row = {k: v for k, v in row.items() if k not in time_labels}
                    for label in time_labels:
                        hour = int(label.split(':')[0])
                        hourly_value = row.get(label, 0)
                        half_value = hourly_value / 2
                        new_row[f"{hour:02d}:00"] = round(half_value)
                        new_row[f"{hour:02d}:30"] = round(half_value)
                        
                        # Ajustar por redondeo
                        if new_row[f"{hour:02d}:00"] + new_row[f"{hour:02d}:30"] != hourly_value:
                            new_row[f"{hour:02d}:00"] += hourly_value - (new_row[f"{hour:02d}:00"] + new_row[f"{hour:02d}:30"])
                    
                    new_output_rows.append(new_row)
                
                return new_output_rows, new_time_labels
        
        return output_rows, time_labels

    def generate_expected_calls_from_curves(self, curve_model, start_date, end_date, daily_volumes=None):
        """
        Genera datos de llamadas esperadas para el calculador usando curvas guardadas.
        Retorna formato ancho (wide) compatible con el Excel solicitado.
        
        Args:
            curve_model: Instancia del modelo ForecastingCurve
            start_date (str): Fecha de inicio
            end_date (str): Fecha de fin
            daily_volumes (dict): Volúmenes diarios opcionales
            
        Returns:
            pd.DataFrame: DataFrame con distribución en formato ancho
        """
        try:
            import json
            
            # Parsear fechas
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            
            # Generar rango de fechas
            date_range = pd.date_range(start=start_dt, end=end_dt, freq='D')
            
            # Obtener etiquetas de tiempo
            time_labels = json.loads(curve_model.time_labels) if isinstance(curve_model.time_labels, str) else curve_model.time_labels
            
            # Mapeo de días de la semana
            days_map = {0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves', 4: 'Viernes', 5: 'Sábado', 6: 'Domingo'}
            
            # Preparar datos
            result_rows = []
            
            for date in date_range:
                day_of_week = date.weekday()
                day_curve = curve_model.get_curve_for_day(day_of_week)
                
                if not day_curve:
                    logger.warning(f"No hay curva definida para el día {day_of_week}")
                    continue
                
                # Obtener volumen diario
                date_str_iso = date.strftime('%Y-%m-%d')
                daily_volume = daily_volumes.get(date_str_iso, 1000) if daily_volumes else 1000
                
                # Construir fila
                row = {
                    'Fecha': date,
                    'Dia': days_map.get(day_of_week, ''),
                    'Semana': date.isocalendar()[1],
                    'Tipo': 'N'
                }
                
                # Distribuir volumen
                for time_label in time_labels:
                    percentage = day_curve.get(time_label, 0)
                    calls = round(daily_volume * percentage)
                    row[time_label] = calls
                    
                result_rows.append(row)
            
            df = pd.DataFrame(result_rows)
            
            # Asegurar orden de columnas
            cols = ['Fecha', 'Dia', 'Semana', 'Tipo'] + sorted(time_labels)
            cols = [c for c in cols if c in df.columns]
            df = df[cols]
            
            return df
            
        except Exception as e:
            logger.error(f"Error generando llamadas esperadas desde curvas: {e}")
            raise
