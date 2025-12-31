"""
Módulo para el cálculo de KPIs globales de dimensionamiento.
"""

import numpy as np
import pandas as pd

class DimensioningKPIService:
    """
    Calcula métricas agregadas como AHT promedio ponderado y porcentajes de reductores.
    """

    def calculate_global_kpis(self, df_master, time_labels, processed_sheets, df_dim=None):
        """
        Calcula los KPIs finales basados en los datos mezclados y resultados de dimensionamiento.
        """
        kpis = {}
        
        # 1. Promedios de reductores
        for key, suffix in [('absentismo', 'abs'), ('auxiliares', 'aux'), ('desconexiones', 'shr')]:
            # Filtrar solo columnas que existan
            cols = [f'{c}_{suffix}' for c in time_labels if f'{c}_{suffix}' in df_master.columns]
            if not cols:
                kpis[f'{key}_pct'] = 0.0
                continue
                
            values = df_master[cols].values.flatten()
            non_zero = values[values != 0]
            kpis[f'{key}_pct'] = float(np.mean(non_zero) * 100) if non_zero.size > 0 else 0.0

        # 2. Volumen y AHT
        total_weighted_aht = 0
        total_calls = 0
        
        for col in time_labels:
            if col in df_master.columns:
                calls_col = pd.to_numeric(df_master[col], errors='coerce').fillna(0)
                total_calls += calls_col.sum()
                
                aht_col_name = f'{col}_aht'
                if aht_col_name in df_master.columns:
                    aht_col = pd.to_numeric(df_master[aht_col_name], errors='coerce').fillna(0)
                    total_weighted_aht += (calls_col * aht_col).sum()
            else:
                # Si el intervalo no existe, se asume volumen 0
                pass
        
        kpis['total_volumen'] = int(total_calls)
        kpis['aht_promedio'] = round(total_weighted_aht / total_calls, 1) if total_calls > 0 else 0.0

        # 3. Horas y FTE (Basado en Dimensionados)
        if df_dim is not None and not df_dim.empty:
            # Seleccionar solo las columnas de tiempo para el cálculo de horas
            time_data = df_dim[time_labels]
            # Cada intervalo es de 30 min (0.5 horas). La suma de agentes en los intervalos / 2 = horas totales.
            total_man_hours = (time_data.sum().sum() * 0.5)
            kpis['total_horas_planificadas'] = round(total_man_hours, 2)
            
            # FTE Promedio: Horas totales / (8 horas * número de días)
            num_days = len(df_dim)
            if num_days > 0:
                kpis['fte_promedio'] = round(total_man_hours / (8 * num_days), 2)
            else:
                kpis['fte_promedio'] = 0.0
        
        return kpis


