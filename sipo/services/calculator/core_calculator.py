"""
Módulo central para los cálculos de dimensionamiento.
Implementa el bucle de cálculo Erlang y la asignación de categorías de agentes.
"""

import pandas as pd
import numpy as np

class DimensioningCoreCalculator:
    """
    Realiza los cálculos matemáticos pesados basados en Erlang.
    """

    def __init__(self, calculation_strategy):
        """
        Args:
            calculation_strategy (CalculatorService): El servicio que contiene las estrategias Erlang.
        """
        self.calc = calculation_strategy

    def calculate_requirements(self, df_master, config, time_labels):
        """
        Recorre el DataFrame maestro y calcula agentes para cada intervalo.
        """
        index_cols = ['Fecha', 'Dia', 'Semana', 'Tipo']
        dim_data, pre_data, log_data, efe_data = [], [], [], []
        
        # Intervalo y factor de llamadas (ajustado a config)
        interval_min = config.get("intervalo", 30)
        calls_factor = 60.0 / interval_min

        target_level = config.get("nda_objetivo") or config.get("sla_objetivo", 0.8)
        service_time = config.get("sla_tiempo", 20)

        for _, row in df_master.iterrows():
            base_row = {col: row[col] for col in index_cols if col in row}
            dim_row, pre_row, log_row, efe_row = base_row.copy(), base_row.copy(), base_row.copy(), base_row.copy()
            
            for col in time_labels:
                calls = row.get(col, 0)
                aht = row.get(f'{col}_aht', 0)
                abs_pct = max(0.0, min(1.0, row.get(f'{col}_abs', 0)))
                shr_pct = max(0.0, min(1.0, row.get(f'{col}_shr', 0)))
                aux_pct = max(0.0, min(1.0, row.get(f'{col}_aux', 0)))

                if calls == 0:
                    efectivos = 0.0
                elif aht <= 0:
                    # Si hay llamadas pero el AHT es 0, no se puede calcular Erlang. 
                    # Usamos un valor mínimo o registramos advertencia.
                    print(f"[WARNING] AHT de 0 detectado para {row.get('Fecha')} {col}. Usando fallback de 1s para evitar error.", flush=True)
                    efectivos = float(self.calc.vba_agents_required(target_level, service_time, calls * calls_factor, 1))
                else:
                    # Cálculo Erlang
                    efectivos = float(self.calc.vba_agents_required(target_level, service_time, calls * calls_factor, aht))
                
                # Cascada de reductores
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

        # Crear DataFrames y asegurar orden de columnas solo con las que existen
        df_res_dim = pd.DataFrame(dim_data)
        df_res_pre = pd.DataFrame(pre_data)
        df_res_log = pd.DataFrame(log_data)
        df_res_efe = pd.DataFrame(efe_data)

        order = [c for c in (index_cols + time_labels) if c in df_res_dim.columns]
        
        return (
            df_res_dim[order],
            df_res_pre[order],
            df_res_log[order],
            df_res_efe[order]
        )

    def format_results(self, df):
        """
        Formatea un DataFrame para visualización con totales.
        """
        df_display = df.copy()
        index_cols = ['Fecha', 'Dia', 'Semana', 'Tipo']
        time_cols = [col for col in df_display.columns if col not in index_cols]
        
        for col in time_cols:
            df_display[col] = pd.to_numeric(df_display[col], errors='coerce').fillna(0)

        df_display[time_cols] = df_display[time_cols].round(1)
        # Horas totales: promedio de agentes por el número de intervalos (cada uno de 30m)
        df_display['Horas-Totales'] = (df_display[time_cols].sum(axis=1) / (len(time_cols) / (60/30) if len(time_cols) > 0 else 1)).round(1)
        
        if 'Fecha' in df_display.columns:
            df_display['Fecha'] = pd.to_datetime(df_display['Fecha'], dayfirst=True).dt.strftime('%d/%m/%Y')
        
        return df_display
