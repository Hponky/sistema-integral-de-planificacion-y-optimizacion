# app/services/agent_loader_service.py

import pandas as pd
import io
from ..models import Agent, SchedulingRule
from .. import db

def load_agents_from_excel(file_storage):
    """
    Procesa un archivo Excel de agentes (en formato FileStorage de Flask)
    y los crea o actualiza en la base de datos.
    """
    try:
        # 1. Cargar las reglas de la BD en un mapa para acceso rápido
        # Se crea una clave única combinando las horas y el tipo de regla (L-V o Rotativo)
        rules_map = {
            f"{int(rule.weekly_hours)}_{'LV' if rule.min_full_weekends_off_per_month == 0 else 'ROT'}": rule.id
            for rule in SchedulingRule.query.all()
        }

        if not rules_map:
            raise ValueError("No se encontraron reglas de planificación en la base de datos. Por favor, créalas primero.")

        # 2. Leer el archivo Excel desde el objeto en memoria que llega de la petición
        df = pd.read_excel(io.BytesIO(file_storage.read()))

        agents_processed = 0
        agents_created = 0
        agents_updated = 0
        warnings = []

        # 3. Iterar y procesar cada agente del archivo Excel
        for index, row in df.iterrows():
            # Se convierte a string y se eliminan espacios para evitar errores
            identificacion = str(row['identificacion']).strip()
            contract_hours = int(row['contrato'])

            # Lógica para determinar si el agente tiene disponibilidad de fin de semana
            sabado_window = row.get('ventana_sabado')
            domingo_window = row.get('ventana_domingo')
            has_weekend = (pd.notna(sabado_window) and str(sabado_window).strip() not in ['-', 'LIBRE', '']) or \
                          (pd.notna(domingo_window) and str(domingo_window).strip() not in ['-', 'LIBRE', ''])
            
            rule_type = 'ROT' if has_weekend else 'LV'
            lookup_key = f"{contract_hours}_{rule_type}"
            rule_id = rules_map.get(lookup_key)

            if not rule_id:
                warning_msg = f"Advertencia: No se encontró regla para {contract_hours}h tipo {rule_type} para el agente {row['nombre_completo']}."
                print(warning_msg)
                warnings.append(warning_msg)
                continue

            # 4. Busca al agente por su identificación para ver si existe
            agent = Agent.query.filter_by(identificacion=identificacion).first()
            if not agent:
                agent = Agent(identificacion=identificacion)
                db.session.add(agent)
                agents_created += 1
            else:
                agents_updated += 1
            
            # 5. Asigna (o actualiza) todos los datos del agente desde el Excel
            agent.nombre_completo = row['nombre_completo']
            agent.centro = row['centro']
            agent.turno_sugerido = str(row.get('turno_sugerido', ''))
            agent.ventana_lunes = str(row.get('ventana_lunes', ''))
            agent.ventana_martes = str(row.get('ventana_martes', ''))
            agent.ventana_miercoles = str(row.get('ventana_miercoles', ''))
            agent.ventana_jueves = str(row.get('ventana_jueves', ''))
            agent.ventana_viernes = str(row.get('ventana_viernes', ''))
            agent.ventana_sabado = str(row.get('ventana_sabado', ''))
            agent.ventana_domingo = str(row.get('ventana_domingo', ''))
            
            # --- ASIGNACIÓN CLAVE DEL ID DE LA REGLA ---
            agent.scheduling_rule_id = rule_id
            agents_processed += 1

        # 6. Guarda todos los cambios en la base de datos
        db.session.commit()

        final_message = f"Proceso completado. Agentes procesados: {agents_processed} (Nuevos: {agents_created}, Actualizados: {agents_updated})."
        if warnings:
            final_message += f" Se encontraron {len(warnings)} advertencias (revisar consola del servidor)."

        return final_message
        
    except Exception as e:
        # Si algo falla, revierte los cambios para no dejar la base de datos a medias
        db.session.rollback()
        # Re-lanza la excepción para que la ruta de la API la capture y muestre el error
        raise e