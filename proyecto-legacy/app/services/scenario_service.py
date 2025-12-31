# app/services/scenario_service.py

from ..models import Scenario, StaffingResult, Schedule, Agent, db
from sqlalchemy import or_
import datetime

def get_or_create_official_scenario(segment_id):
    """
    Busca el escenario oficial del segmento. Si no existe, lo crea.
    """
    scen = Scenario.query.filter_by(segment_id=segment_id, is_official=True).first()
    if not scen:
        scen = Scenario(
            name="Oficial (Producción)", 
            segment_id=segment_id, 
            is_official=True,
            start_date=datetime.date(2020, 1, 1),
            end_date=datetime.date(2030, 12, 31)
        )
        db.session.add(scen)
        db.session.commit()
    return scen

def create_simulation_scenario(segment_id, name, base_scenario_id=None, start_date=None, end_date=None):
    """
    Crea un nuevo escenario de simulación.
    Clona Forecast y Turnos del escenario base para el rango de fechas.
    """
    print(f"--- Iniciando Creación de Simulación: {name} ---")
    
    # 1. Crear el Escenario Nuevo en BD
    new_scen = Scenario(
        name=name, 
        segment_id=segment_id, 
        is_official=False,
        start_date=start_date,
        end_date=end_date
    )
    db.session.add(new_scen)
    db.session.commit() 
    
    print(f"   > Escenario creado con ID: {new_scen.id}")

    if start_date and end_date:
        # -------------------------------------------------------
        # A. CLONAR FORECAST (StaffingResult)
        # -------------------------------------------------------
        base_staffing = StaffingResult.query.filter(
            StaffingResult.segment_id == segment_id,
            StaffingResult.result_date.between(start_date, end_date),
            or_(StaffingResult.scenario_id == base_scenario_id, StaffingResult.scenario_id == None)
        ).all()
        
        new_staffing = []
        for st in base_staffing:
            new_st = StaffingResult(
                result_date=st.result_date, 
                segment_id=st.segment_id, 
                scenario_id=new_scen.id,
                agents_online=st.agents_online, 
                agents_total=st.agents_total,
                calls_forecast=st.calls_forecast, 
                aht_forecast=st.aht_forecast,
                reducers_forecast=st.reducers_forecast,
                sla_target_percentage=st.sla_target_percentage, 
                sla_target_time=st.sla_target_time
            )
            new_staffing.append(new_st)
        
        if new_staffing:
            db.session.bulk_save_objects(new_staffing)
            print(f"   > Forecast clonado: {len(new_staffing)} días.")

        # -------------------------------------------------------
        # B. CLONAR TURNOS (Schedule) - CORRECCIÓN AGENTES NULL
        # -------------------------------------------------------
        
        # Paso 1: Identificar agentes REALES (False O None)
        # Esta es la corrección clave: or_(Agent.is_simulated == False, Agent.is_simulated == None)
        real_agents = Agent.query.filter(
            Agent.segment_id == segment_id,
            or_(Agent.is_simulated == False, Agent.is_simulated == None)
        ).all()
        
        real_agent_ids = [a.id for a in real_agents]
        print(f"   > Agentes reales encontrados: {len(real_agent_ids)}")
        
        if real_agent_ids:
            # Paso 2: Buscar turnos
            base_schedules = Schedule.query.filter(
                Schedule.agent_id.in_(real_agent_ids),
                Schedule.schedule_date.between(start_date, end_date),
                or_(Schedule.scenario_id == base_scenario_id, Schedule.scenario_id == None)
            ).all()
            
            print(f"   > Turnos encontrados para clonar: {len(base_schedules)}")
            
            new_schedules = []
            seen_keys = set()

            for sch in base_schedules:
                key = (sch.agent_id, sch.schedule_date)
                if key in seen_keys: continue
                seen_keys.add(key)

                new_sch = Schedule(
                    agent_id=sch.agent_id, 
                    schedule_date=sch.schedule_date, 
                    scenario_id=new_scen.id, # ASIGNAR AL NUEVO ESCENARIO
                    shift=sch.shift, 
                    hours=sch.hours, 
                    is_manual_edit=sch.is_manual_edit,
                    descanso1_he=sch.descanso1_he, descanso1_hs=sch.descanso1_hs,
                    descanso2_he=sch.descanso2_he, descanso2_hs=sch.descanso2_hs,
                    pvd1=sch.pvd1, pvd2=sch.pvd2, pvd3=sch.pvd3, pvd4=sch.pvd4,
                    pvd5=sch.pvd5, pvd6=sch.pvd6, pvd7=sch.pvd7, pvd8=sch.pvd8, 
                    pvd9=sch.pvd9, pvd10=sch.pvd10
                )
                new_schedules.append(new_sch)
            
            if new_schedules:
                db.session.bulk_save_objects(new_schedules)
                print(f"   > Turnos insertados en simulación: {len(new_schedules)}")
            
        db.session.commit()
        
    return new_scen

def promote_scenario_to_official(simulation_id):
    sim = Scenario.query.get(simulation_id)
    if not sim or sim.is_official: return False
    
    official = Scenario.query.filter_by(segment_id=sim.segment_id, is_official=True).first()
    if not official: return False
    
    start = sim.start_date
    end = sim.end_date
    if not start or not end: return False 

    # Limpiar Oficial en ese rango
    StaffingResult.query.filter(
        StaffingResult.scenario_id == official.id,
        StaffingResult.result_date.between(start, end)
    ).delete(synchronize_session=False)
    
    Schedule.query.filter(
        Schedule.scenario_id == official.id,
        Schedule.schedule_date.between(start, end)
    ).delete(synchronize_session=False)
    
    # Mover Simulación -> Oficial
    StaffingResult.query.filter_by(scenario_id=sim.id).update({'scenario_id': official.id})
    Schedule.query.filter_by(scenario_id=sim.id).update({'scenario_id': official.id})
    
    db.session.delete(sim)
    db.session.commit()
    return True