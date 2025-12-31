# fix_scenarios.py
import sys
import datetime

print("--- 1. Script de curación iniciado ---")

try:
    from app import create_app, db
    from app.models import Segment, Scenario, StaffingResult, Schedule, Agent
    print("--- 2. Importaciones de Flask/SQLAlchemy exitosas ---")
except ImportError as e:
    print(f"!!! ERROR DE IMPORTACIÓN: {e}")
    print("Asegúrate de estar ejecutando esto desde la carpeta raíz del proyecto.")
    sys.exit(1)

app = create_app()

with app.app_context():
    print("--- 3. Conexión a Base de Datos establecida ---")
    
    # 1. Obtener Segmentos
    segments = Segment.query.all()
    print(f"--- 4. Se encontraron {len(segments)} segmentos en la base de datos ---")
    
    if len(segments) == 0:
        print("ADVERTENCIA: No hay segmentos. No hay nada que migrar.")
    
    count_staffing = 0
    count_schedules = 0

    for seg in segments:
        print(f"\nProcesando Segmento: {seg.name} (ID: {seg.id})...")
        
        # 2. Asegurar Escenario Oficial
        official = Scenario.query.filter_by(segment_id=seg.id, is_official=True).first()
        if not official:
            official = Scenario(name="Oficial (Producción)", segment_id=seg.id, is_official=True)
            # Fechas por defecto amplias para cubrir todo el histórico
            official.start_date = datetime.date(2020, 1, 1)
            official.end_date = datetime.date(2030, 12, 31)
            db.session.add(official)
            db.session.commit()
            print(f"   > Creado escenario Oficial (ID: {official.id})")
        else:
            print(f"   > Escenario Oficial ya existía (ID: {official.id})")
            # Asegurar que tenga fechas si estaba vacío
            if not official.start_date:
                official.start_date = datetime.date(2020, 1, 1)
                official.end_date = datetime.date(2030, 12, 31)
                db.session.commit()
                print("   > Fechas actualizadas en escenario oficial.")

        # 3. Mover Staffing Huérfano (NULL -> Oficial)
        updated_st = StaffingResult.query.filter(
            StaffingResult.segment_id == seg.id,
            StaffingResult.scenario_id == None
        ).update({StaffingResult.scenario_id: official.id}, synchronize_session=False)
        
        count_staffing += updated_st
        if updated_st > 0:
            print(f"   > Se asignaron {updated_st} registros de Forecast al Oficial.")

        # 4. Mover Schedules Huérfanos (NULL -> Oficial)
        # Buscamos agentes de este segmento
        agent_ids = [a.id for a in Agent.query.filter_by(segment_id=seg.id).all()]
        
        if agent_ids:
            updated_sch = Schedule.query.filter(
                Schedule.agent_id.in_(agent_ids),
                Schedule.scenario_id == None
            ).update({Schedule.scenario_id: official.id}, synchronize_session=False)
            
            count_schedules += updated_sch
            if updated_sch > 0:
                print(f"   > Se asignaron {updated_sch} turnos al Oficial.")
        
        db.session.commit()

    print("\n" + "="*40)
    print(f"RESUMEN FINAL:")
    print(f"Total Forecasts Migrados: {count_staffing}")
    print(f"Total Turnos Migrados:    {count_schedules}")
    print("="*40)