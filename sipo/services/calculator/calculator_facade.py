"""
Fachada principal para el servicio de Dimensionamiento (Calculadora).
Orquesta el flujo de procesamiento, cálculo y generación de KPIs.
"""

import logging
from .data_processor import DimensioningDataProcessor
from .core_calculator import DimensioningCoreCalculator
from .kpi_service import DimensioningKPIService

logger = logging.getLogger(__name__)

class CalculatorServiceFacade:
    """
    Punto de entrada unificado para la lógica de dimensionamiento.
    """

    def __init__(self, erlang_strategy_service):
        self.processor = DimensioningDataProcessor()
        self.calculator = DimensioningCoreCalculator(erlang_strategy_service)
        self.kpi_service = DimensioningKPIService()
        self.strategy_service = erlang_strategy_service

    def process_full_dimensioning(self, config, all_sheets):
        """
        Ejecuta el flujo completo de cálculo:
        1. Normalización de hojas.
        2. Fusión de datos (Merge).
        3. Cálculo de requerimientos Erlang.
        4. Cálculo de KPIs.
        """
        try:
            # 1. Generar etiquetas de tiempo estándar (00:00, 00:30, ...)
            time_labels = [f"{i*30//60:02d}:{i*30%60:02d}" for i in range(48)]

            # 2. Preparar hojas
            sheets = self.processor.prepare_sheets(all_sheets)
            
            # 3. Mezclar datos
            df_master = self.processor.merge_data(sheets, config, time_labels)
            
            # 4. Calcular requerimientos
            df_dim, df_pre, df_log, df_efe = self.calculator.calculate_requirements(df_master, config, time_labels)
            
            # 5. Calcular KPIs
            kpis = self.kpi_service.calculate_global_kpis(df_master, time_labels, sheets, df_dim)
            
            return df_dim, df_pre, df_log, df_efe, kpis, sheets['calls'], sheets['aht']
            
        except Exception as e:
            logger.error(f"Error en process_full_dimensioning: {e}", exc_info=True)
            raise ValueError(str(e))

    def format_dataframe(self, df):
        """Formatea para visualización."""
        return self.calculator.format_results(df)

    def get_fallback_volume(self, segment_id, start_date, end_date, id_legal=None):
        """
        Intenta recuperar un volumen de llamadas (distribución) desde el módulo de Forecasting.
        Retorna (DataFrame, warning_message)
        """
        try:
            print(f"[DEBUG CALCULATOR] Iniciando fallback para SegmentID: {segment_id}, Fechas: {start_date} a {end_date}", flush=True)
            from services.forecasting.curve_repository import CurveRepository
            import pandas as pd
            import json
            import datetime
            
            repo = CurveRepository()
            
            # Ajustar tipos de fecha (asegurar que son objetos date para el repo)
            q_start = start_date
            q_end = end_date
            if isinstance(q_start, str):
                try: q_start = datetime.datetime.strptime(q_start, '%Y-%m-%d').date()
                except: pass
            if isinstance(q_end, str):
                try: q_end = datetime.datetime.strptime(q_end, '%Y-%m-%d').date()
                except: pass
                
            dist = repo.get_latest_distribution(segment_id, q_start, q_end, id_legal)
            
            if not dist:
                print(f"[DEBUG CALCULATOR] No se encontró ninguna distribución activa o coincidente para SegmentID {segment_id}", flush=True)
                return None, f"No hay una distribución marcada como 'Activa' en Forecasting para el segmento ID {segment_id}."
            
            print(f"[DEBUG CALCULATOR] Distribución encontrada: ID={dist.id}, Start={dist.start_date}, End={dist.end_date}, Seleccionada={dist.is_selected}", flush=True)
            
            # Parsear datos
            data_map = json.loads(dist.distribution_data)
            time_labels = json.loads(dist.time_labels)
            
            rows = []
            metadata_cols = set()
            
            for date_key, row_data in data_map.items():
                # Normalizar la fecha del key de forma robusta
                def smart_parse_key(val):
                    s = str(val).strip()
                    try:
                        # ISO?
                        if '-' in s and s.index('-') == 4:
                            return pd.to_datetime(s, dayfirst=False)
                        # ES?
                        return pd.to_datetime(s, dayfirst=True)
                    except:
                        return pd.to_datetime(s, errors='coerce')

                dt = smart_parse_key(date_key)
                if pd.isna(dt):
                    print(f"[DEBUG FALLBACK] No se pudo parsear fecha key: {date_key}", flush=True)
                    continue

                row = {'Fecha': dt}
                if isinstance(row_data, dict):
                    # Extraer metadata y volúmenes
                    for k, v in row_data.items():
                        if k not in time_labels and k != 'Fecha':
                            metadata_cols.add(k)
                        row[k] = v
                    # Asegurar que todos los time_labels estén
                    for t in time_labels:
                        if t not in row: row[t] = 0.0
                else:
                    # Formato antiguo (lista)
                    for i, t in enumerate(time_labels):
                        row[t] = row_data[i] if i < len(row_data) else 0.0
                
                rows.append(row)

            if not rows:
                 return pd.DataFrame(), "La distribución no contiene fechas válidas."

            df = pd.DataFrame(rows)
            # Asegurar que todas las columnas de tiempo existen
            for t in time_labels:
                if t not in df.columns: df[t] = 0.0

            df.sort_values('Fecha', inplace=True)
            
            # Reordenar columnas
            cols_order = ['Fecha'] + sorted(list(metadata_cols)) + time_labels
            df = df[[c for c in cols_order if c in df.columns]]
            
            # Volver a convertir Fecha a string para el resto de la app
            df['Fecha'] = df['Fecha'].dt.strftime('%Y-%m-%d')
            
            count = len(df)
            total_vol = sum(df[time_labels].sum())
            print(f"[DEBUG FALLBACK] Fallback completado. Filas: {count}, Volumen Total: {total_vol:.2f}", flush=True)
            
            msg = f"Se está utilizando la distribución de Forecasting (ID: {dist.id}) con {count} días de datos."
            return df, msg

        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.warning(f"Error recuperando fallback volume: {e}")
            return None, f"Error técnico recuperando volumen de Forecasting: {str(e)}"
