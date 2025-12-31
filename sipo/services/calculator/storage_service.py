"""
Servicio de almacenamiento y recuperación de datos de dimensionamiento.
Maneja toda la lógica de persistencia en la base de datos.
"""

import pandas as pd
import json
import datetime
import io
from app import db
from models import DimensioningScenario


class StorageService:
    """Servicio para gestionar el almacenamiento de resultados de dimensionamiento."""
    
    @staticmethod
    def create_scenario(segment_id: int, config: dict, id_legal: str = None, username: str = None) -> DimensioningScenario:
        """
        Crea un nuevo escenario de dimensionamiento.
        
        Args:
            segment_id: ID del segmento
            config: Configuración del cálculo
            id_legal: ID legal del usuario (Active Directory)
            username: Nombre de usuario
            
        Returns:
            Objeto DimensioningScenario creado
        """
        new_scenario = DimensioningScenario(
            segment_id=segment_id,
            parameters=json.dumps(config, default=str),
            id_legal=id_legal,
            username=username
        )
        db.session.add(new_scenario)
        db.session.flush()
        return new_scenario
    
    @staticmethod
    def save_calculation_results(
        scenario_id: int,
        df_dimensionados: pd.DataFrame,
        df_presentes: pd.DataFrame,
        df_logados: pd.DataFrame,
        df_efectivos: pd.DataFrame,
        kpi_data: dict,
        df_calls: pd.DataFrame = None,
        df_aht: pd.DataFrame = None
    ) -> None:
        """
        Guarda los resultados del cálculo en el escenario existente.
        """
        scenario = DimensioningScenario.query.get(scenario_id)
        if not scenario:
            raise ValueError(f"Escenario {scenario_id} no encontrado")
            
        def df_to_json(df):
            if df is None or df.empty:
                return "[]"
            df_copy = df.copy()
            if 'Fecha' in df_copy.columns:
                df_copy['Fecha'] = df_copy['Fecha'].apply(lambda x: x.strftime('%Y-%m-%d') if isinstance(x, (datetime.date, datetime.datetime)) else str(x))
            return df_copy.to_json(orient='records')

        scenario.agents_total = df_to_json(df_dimensionados)
        scenario.agents_present = df_to_json(df_presentes)
        scenario.agents_logged = df_to_json(df_logados)
        scenario.agents_online = df_to_json(df_efectivos)
        
        if df_calls is not None:
            scenario.calls_forecast = df_to_json(df_calls)
        if df_aht is not None:
            scenario.aht_forecast = df_to_json(df_aht)
            
        scenario.kpis_data = json.dumps(kpi_data)
        
        db.session.commit()
    
    @staticmethod
    def get_scenario_history(id_legal: str, limit: int = 20) -> list:
        """
        Obtiene el historial de escenarios para un usuario.
        
        Args:
            id_legal: ID legal del usuario
            limit: Número máximo de resultados
            
        Returns:
            Lista de diccionarios con información de los escenarios
        """
        scenarios = DimensioningScenario.query.filter_by(id_legal=id_legal)\
            .order_by(DimensioningScenario.created_at.desc())\
            .limit(limit)\
            .all()
        
        history_data = []
        for scenario in scenarios:
            params = json.loads(scenario.parameters)
            history_data.append({
                'id': scenario.id,
                'created_at': scenario.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'segment_name': scenario.segment.name,
                'campaign_name': scenario.segment.campaign.name,
                'start_date': params.get('start_date'),
                'end_date': params.get('end_date'),
                'sla_objetivo': params.get('sla_objetivo'),
                'sla_tiempo': params.get('sla_tiempo'),
                'nda': params.get('nda_objetivo') or params.get('nda') or params.get('sla_objetivo')  # NDA objetivo
            })
        
        return history_data
    
    @staticmethod
    def get_scenario_details(scenario_id: int) -> dict:
        """
        Obtiene los detalles completos de un escenario.
        
        Args:
            scenario_id: ID del escenario
            
        Returns:
            Diccionario con los resultados formateados
            
        Raises:
            ValueError: Si no se encuentra el escenario
        """
        from .calculator_service import CalculatorService
        
        scenario = DimensioningScenario.query.get(scenario_id)
        if not scenario:
            raise ValueError(f"Escenario {scenario_id} no encontrado")
        
        # Helper para cargar JSON a DataFrame
        def json_to_df(json_str):
            if not json_str or json_str == "[]":
                return pd.DataFrame()
            return pd.read_json(io.StringIO(json_str), orient='records')

        import io
        
        df_dim = json_to_df(scenario.agents_total)
        df_efe = json_to_df(scenario.agents_online)
        df_pre = json_to_df(scenario.agents_present)
        df_log = json_to_df(scenario.agents_logged)
        
        kpi_data = json.loads(scenario.kpis_data) if scenario.kpis_data else {}
        
        from .calculator_service import CalculatorService
        service = CalculatorService()
        
        # Formatear resultados
        results_dict = {
            "scenario_id": scenario.id,
            "dimensionados": service.format_and_calculate_simple(df_dim).to_dict(orient='split') if not df_dim.empty else {},
            "efectivos": service.format_and_calculate_simple(df_efe).to_dict(orient='split') if not df_efe.empty else {},
            "presentes": service.format_and_calculate_simple(df_pre).to_dict(orient='split') if not df_pre.empty else {},
            "logados": service.format_and_calculate_simple(df_log).to_dict(orient='split') if not df_log.empty else {},
            "kpis": kpi_data
        }
        
        # Limpieza de index
        for key in results_dict:
            if isinstance(results_dict[key], dict) and 'index' in results_dict[key]:
                del results_dict[key]['index']
        
        return results_dict
    
    @staticmethod
    def delete_scenario(scenario_id: int) -> None:
        """
        Elimina un escenario.
        
        Args:
            scenario_id: ID del escenario a eliminar
            
        Raises:
            ValueError: Si no se encuentra el escenario
        """
        scenario = DimensioningScenario.query.get(scenario_id)
        if not scenario:
            raise ValueError(f"Escenario {scenario_id} no encontrado")
        
        db.session.delete(scenario)
        db.session.commit()
