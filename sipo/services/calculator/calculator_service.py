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
from .strategies.strategy_context import StrategyContext


class CalculatorService:
    """
    Proporciona métodos para realizar cálculos de dimensionamiento de agentes
    basados en la metodología Erlang y procesar plantillas de datos.
    """

    def __init__(self):
        """
        Inicializa el servicio con el contexto de estrategias y la fachada.
        """
        self.strategy_context = StrategyContext()
        from .calculator_facade import CalculatorServiceFacade
        self._facade = CalculatorServiceFacade(self)

    def vba_erlang_b(self, servers, intensity):
        """
        Calcula la probabilidad de bloqueo (Erlang B) usando la estrategia correspondiente.
        """
        return self.strategy_context.calculate('erlang_b', servers, intensity)

    def vba_erlang_c(self, servers, intensity):
        """
        Calcula la probabilidad de espera (Erlang C) usando la estrategia correspondiente.
        """
        return self.strategy_context.calculate('erlang_c', servers, intensity)

    def vba_sla(self, agents, service_time, calls_per_hour, aht):
        """
        Calcula el Nivel de Servicio (SLA) usando la estrategia correspondiente.
        """
        return self.strategy_context.calculate('sla', agents, service_time, calls_per_hour, aht)

    def vba_agents_required(self, target_sla, service_time, calls_per_hour, aht):
        """
        Calcula el número de agentes requeridos usando la estrategia correspondiente.
        """
        return self.strategy_context.calculate('agents_required', target_sla, service_time, calls_per_hour, aht)

    @staticmethod
    def procesar_plantilla_unica(config, all_sheets):
        """
        Punto de entrada legacy que delega a la fachada.
        """
        instance = CalculatorService()
        return instance._facade.process_full_dimensioning(config, all_sheets)

    @staticmethod
    def format_and_calculate_simple(df):
        """
        Delega el formato a la fachada.
        """
        instance = CalculatorService()
        return instance._facade.format_dataframe(df)

    @staticmethod
    def get_fallback_volume(segment_id, start_date, end_date, id_legal=None):
        """
        Delega la recuperación de volumen fallback a la fachada.
        """
        instance = CalculatorService()
        return instance._facade.get_fallback_volume(segment_id, start_date, end_date, id_legal)

    @staticmethod
    def _format_dataframe_columns(df, time_cols_reference):
        """
        Mantenido por compatibilidad si es llamado externamente.
        """
        if df is None or df.empty:
            return df

        original_columns = df.columns
        formatted_columns = []
        for col in original_columns:
            col_str = str(col).strip()
            if isinstance(col, (datetime.time, datetime.datetime)) or 'datetime' in str(type(col)):
                if hasattr(col, 'strftime'):
                    formatted_columns.append(col.strftime('%H:%M'))
                else:
                    formatted_columns.append(col_str)
            elif ':' in col_str:
                try:
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
