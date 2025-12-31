# migrar_escenarios.py
import sys
print("--- Script iniciado ---") # Si no ves esto, el archivo no se está ejecutando

try:
    from app import create_app, db
    from app.models import Segment, Scenario, StaffingResult, Schedule, Agent
except ImportError as e:
    print(f"Error de importación: {e}")
    sys.exit(1)

app = create_app()

with app.app_context():
    print("Conexión a base de datos establecida.")
    
    # Obtener todos los segmentos
    segments = Segment.query.all()
    print(f"Se encontraron {len(segments)} segmentos para procesar.")

    for seg in segments:
        print(f"\nProcesando segmento: {seg.name} (ID: {seg.id})")
        
        # 1. Buscar o Crear Escenario Oficial para este segmento
        official = Scenario.query.filter_by(segment_id=seg.id, is_official=True).first()
        if not official:
            official = Scenario(name="Oficial (Producción)", segment_id=seg.id, is_official=True)
            db.session.add(official)
            db.session.commit()
            print(f"   -> Creado escenario Oficial (ID: {official.id})")
        else:
            print(f"   -> Escenario Oficial existente (ID: {official.id})")
        
        # 2. Asignar Forecasts (StaffingResult) huérfanos
        updated_staffing = StaffingResult.query.filter(
            StaffingResult.segment_id == seg.id,
            StaffingResult.scenario_id == None
        ).update({StaffingResult.scenario_id: official.id}, synchronize_session=False)
        
        print(f"   -> Forecasts migrados: {updated_staffing}")
        
        # 3. Asignar Horarios (Schedule) huérfanos
        # Obtenemos los IDs de los agentes de este segmento
        agent_ids = [a.id for a in Agent.query.filter_by(segment_id=seg.id).all()]
        
        updated_schedules = 0
        if agent_ids:
            updated_schedules = Schedule.query.filter(
                Schedule.agent_id.in_(agent_ids),
                Schedule.scenario_id == None
            ).update({Schedule.scenario_id: official.id}, synchronize_session=False)
        
        print(f"   -> Turnos migrados: {updated_schedules}")

        db.session.commit()

    print("\n=== MIGRACIÓN COMPLETADA EXITOSAMENTE ===")