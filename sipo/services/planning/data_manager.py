"""
Módulo para la gestión y preparación de datos de planificación.
Maneja el parseo de agentes, ausencias y la carga de escenarios de dimensionamiento.
"""

import os
import json
import logging
import pandas as pd
from datetime import datetime
from flask import current_app
from services.scheduler.input_parser import InputParser # Updated import

logger = logging.getLogger(__name__)

class PlanningDataManager:
    def __init__(self):
        self.parser = InputParser()

    def parse_agents_with_absences(self, agents_file, absences_file, fictitious_agents_json=None, country_override=None):
        """
        Parse agentes de Excel, inyecta ficticios y mezcla con archivo de ausencias.
        """
        agents = []
        
        # 1. Parsear agentes de Excel
        if agents_file and agents_file.filename != '':
            temp_dir = os.path.join(current_app.instance_path, 'planning_temp')
            os.makedirs(temp_dir, exist_ok=True)
            temp_path = os.path.join(temp_dir, f"temp_{int(datetime.now().timestamp())}_agents.xlsx")
            agents_file.save(temp_path)
            
            try:
                agents = self.parser.parse_excel(temp_path, country_override=country_override)
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        
        # 2. Inyectar agentes ficticios
        if fictitious_agents_json:
            try:
                fictitious_agents = json.loads(fictitious_agents_json)
                agents.extend(fictitious_agents)
            except Exception as e:
                logger.error(f"Error parseando agentes ficticios: {e}")

        # 3. Parsear y mezclar ausencias
        if absences_file and absences_file.filename != '':
            try:
                from werkzeug.utils import secure_filename
                abs_filename = secure_filename(absences_file.filename)
                abs_path = os.path.join(current_app.instance_path, abs_filename)
                absences_file.save(abs_path)
                
                absences_map = self.parser.parse_absences(abs_path)
                
                # Normalizar DNI para el cruce
                def normalize(d):
                    s = str(d).strip().upper()
                    if s.endswith('.0'): s = s[:-2]
                    return s.lstrip('0')
                
                norm_absences_map = {normalize(k): v for k, v in absences_map.items()}
                
                for agent in agents:
                    dni = normalize(agent.get("dni", ""))
                    if dni and dni in norm_absences_map:
                        if "absences" not in agent: agent["absences"] = []
                        agent["absences"].extend(norm_absences_map[dni])
                
                if os.path.exists(abs_path): os.remove(abs_path)
            except Exception as e:
                logger.error(f"Error procesando archivo de ausencias: {e}")

        return agents

    def load_scenario_requirements(self, scenario_id):
        """
        Carga requerimientos, llamadas y AHT de un escenario de dimensionamiento.
        Retorna (requirements_data, calls_data, aht_data, sla_params)
        """
        from models import DimensioningScenario
        from services.scheduler.metrics_calculator import DimensioningCalculator
        
        requirements_data = {}
        calls_data = {}
        aht_data = {}
        sla_params = {}
        
        try:
            scenario = DimensioningScenario.query.get(scenario_id)
            if not scenario:
                return {}, {}, {}, {}

            # Parsear parámetros (SLA, NDA, Tiempo)
            if scenario.parameters:
                try: 
                    params = json.loads(scenario.parameters)
                    sla_params['sla_objetivo'] = float(params.get('sla_objetivo'))
                    sla_params['sla_tiempo'] = int(params.get('sla_tiempo'))
                    sla_params['nda_objetivo'] = float(params.get('nda_objetivo') or params.get('sla_objetivo'))
                    sla_params['intervalo'] = int(params.get('intervalo', 30))
                    
                    # Extraer país de la campaña
                    country_raw = 'ES'
                    if scenario.segment and scenario.segment.campaign:
                        country_raw = str(scenario.segment.campaign.country or 'ES').upper()
                    
                    if "COL" in country_raw or "BOG" in country_raw or "MED" in country_raw:
                        country = 'CO'
                    elif "ESP" in country_raw or "SPA" in country_raw or "MAD" in country_raw or "BAR" in country_raw or "ES" == country_raw:
                        country = 'ES'
                    else:
                        country = 'ES' # Default

                    sla_params['country'] = country
                except Exception as e:
                    logger.error(f"Error parseando parámetros del escenario: {e}")
            
            # Helper para parsear los blobs de datos
            def parse_blob(blob_str):
                if not blob_str: return {}
                try: data = json.loads(blob_str)
                except: return {}
                
                res = {}
                
                def get_index_from_time(t_str):
                    s = str(t_str).strip()
                    if ' ' in s: s = s.split(' ')[-1]
                    if ':' in s:
                        try:
                            parts = s.split(':')
                            h, m = int(parts[0]), int(parts[1])
                            return (h * 60 + m) // 30
                        except: pass
                    try: 
                        idx = int(float(s))
                        if 0 <= idx < 48: return idx
                    except: pass
                    return None

                def smart_parse_date(val):
                    if not val: return None
                    s = str(val).strip()
                    try:
                        if '-' in s and s.index('-') == 4:
                            return pd.to_datetime(s, dayfirst=False).strftime('%Y-%m-%d')
                        return pd.to_datetime(s, dayfirst=True).strftime('%Y-%m-%d')
                    except:
                        try: return pd.to_datetime(s).strftime('%Y-%m-%d')
                        except: return str(s).split(' ')[0]

                if isinstance(data, list):
                    for row in data:
                        fecha_str = smart_parse_date(row.get('Fecha'))
                        if not fecha_str: continue
                        vals = [0.0] * 48
                        ignore = ['Fecha', 'Dia', 'Semana', 'Tipo', 'id', 'agent_id', 'total', 'Intervalo', 'Dia Semana', 'Nombre', 'Servicio']
                        for k, v in row.items():
                            if k in ignore or str(k).startswith('_'): continue
                            idx = get_index_from_time(k)
                            if idx is not None:
                                try: vals[idx] = float(v or 0)
                                except: pass
                        res[fecha_str] = vals
                elif isinstance(data, dict):
                    for d_key, col_data in data.items():
                        if d_key.startswith('_') or d_key == 'Intervalo': continue
                        fecha_str = smart_parse_date(d_key)
                        if not fecha_str: continue
                        vals = [0.0] * 48
                        if isinstance(col_data, dict):
                            for t_key, val in col_data.items():
                                idx = get_index_from_time(t_key)
                                if idx is not None:
                                    try: vals[idx] = float(val or 0)
                                    except: pass
                        elif isinstance(col_data, list):
                            for i, val in enumerate(col_data):
                                if i < 48:
                                    try: vals[i] = float(val or 0)
                                    except: pass
                        res[fecha_str] = vals
                return res

            requirements_data = parse_blob(scenario.agents_online)
            calls_data = parse_blob(scenario.calls_forecast)
            aht_data = parse_blob(scenario.aht_forecast)
            
            # Recalcular requerimientos basados en NDA si es necesario
            if calls_data and sla_params.get('nda_objetivo'):
                calc = DimensioningCalculator()
                nda_target = sla_params['nda_objetivo']
                sla_time = sla_params.get('sla_tiempo', 20)
                
                for date_str, calls_list in calls_data.items():
                    # Fallback de AHT: si no hay datos o es todo cero, usar 300s
                    aht_list = aht_data.get(date_str, [300.0] * 48)
                    if sum(aht_list or []) <= 0:
                        aht_list = [300.0] * 48
                        
                    req_list = [
                        calc.calculate_required_agents(float(calls_list[i]), float(aht_list[i]), sl_target=nda_target, sl_time=sla_time, is_nda=True)
                        if float(calls_list[i]) > 0 else 0.0
                        for i in range(48)
                    ]
                    requirements_data[date_str] = req_list

            if requirements_data and not calls_data:
                calls_data = requirements_data
                
        except Exception as e:
            logger.error(f"Error cargando datos del escenario {scenario_id}: {e}")
            
        return requirements_data, calls_data, aht_data, sla_params

    def prepare_forecast_input(self, requirements_data, calls_data=None, aht_data=None):
        """
        Prepara el formato de entrada de forecast para el DimensioningCalculator.
        """
        forecast_input = {}
        dates = list(requirements_data.keys())
        if calls_data: 
            dates = list(set(dates + list(calls_data.keys())))
        
        for d_str in dates:
            forecast_input[d_str] = {}
            reqs = requirements_data.get(d_str, [0]*48)
            calls = calls_data.get(d_str, reqs) if calls_data else reqs
            ahts = aht_data.get(d_str, [300]*48) if aht_data else [300]*48
            
            for i in range(48):
                c_val = calls[i] if i < len(calls) else 0
                a_val = ahts[i] if i < len(ahts) else 300
                r_val = reqs[i] if i < len(reqs) else 0
                forecast_input[d_str][i] = {'calls': c_val, 'aht': a_val, 'required': r_val}
                
        return forecast_input
