# app/services/breaks_service.py

import datetime
import random
import io
import pandas as pd
from sqlalchemy.orm import joinedload
from sqlalchemy import not_
from collections import defaultdict

from .. import db
from ..models import Agent, Schedule, Segment
from ..constants import VALID_AUSENCIA_CODES

def assign_breaks_to_schedule(segment_id, start_date, end_date):
    """
    Calcula y asigna descansos y PVDs a los turnos existentes.
    """
    segment = Segment.query.options(joinedload(Segment.campaign)).get(segment_id)
    if not segment:
        return {"error": "Segmento no encontrado"}

    # Filtrar turnos válidos (no libres, no ausencias)
    schedules_to_update = Schedule.query.join(Agent).filter(
        Agent.segment_id == segment_id,
        Schedule.schedule_date.between(start_date, end_date),
        Schedule.shift != 'LIBRE',
        not_(Schedule.shift.in_(VALID_AUSENCIA_CODES))
    ).all()
    
    updated_count = 0

    for schedule in schedules_to_update:
        # 1. Limpiar descansos previos
        schedule.descanso1_he = None; schedule.descanso1_hs = None
        schedule.descanso2_he = None; schedule.descanso2_hs = None
        for i in range(1, 11): setattr(schedule, f'pvd{i}', None)

        # 2. Analizar el turno
        shift_parts = schedule.shift.split('/')
        pvd_idx = 1
        descanso_idx = 1

        for part in shift_parts:
            part = part.strip()
            if '-' not in part: continue

            try:
                # Parsear horas inicio y fin
                start_str, end_str = part.split('-')
                hora_inicio = datetime.datetime.strptime(start_str.strip(), "%H:%M")
                
                end_dt_str = end_str.strip()
                if end_dt_str == '24:00':
                    hora_fin = datetime.datetime.strptime('23:59', '%H:%M') + datetime.timedelta(minutes=1)
                else:
                    hora_fin = datetime.datetime.strptime(end_dt_str, '%H:%M')

                # Calcular duración del tramo
                part_duration_hours = (hora_fin - hora_inicio).total_seconds() / 3600
                if part_duration_hours < 0: part_duration_hours += 24 

            except ValueError:
                continue

            duracion_redondeada = round(part_duration_hours)
            descanso_inicio = None
            descanso_fin = None
            
            # --- LÓGICA DE PAUSAS (ESPAÑA) ---
            if segment.campaign.country == 'España' or True: 
                descanso_duracion = 0
                
                if 4 <= duracion_redondeada <= 5:
                    descanso_duracion = 10
                elif 6 <= duracion_redondeada <= 8:
                    descanso_duracion = 20
                elif 9 <= duracion_redondeada <= 10:
                    descanso_duracion = 30
                
                # ASIGNAR DESCANSO PRINCIPAL
                if descanso_duracion > 0 and descanso_idx <= 2:
                    ventana_min = hora_inicio + datetime.timedelta(hours=2)
                    ventana_max = min(
                        hora_inicio + datetime.timedelta(hours=4, minutes=30), 
                        hora_fin - datetime.timedelta(hours=1)
                    )
                    
                    if ventana_max > ventana_min:
                        rand_seconds = random.random() * (ventana_max - ventana_min).total_seconds()
                        descanso_inicio = (ventana_min + datetime.timedelta(seconds=rand_seconds)).replace(second=0, microsecond=0)
                        descanso_fin = descanso_inicio + datetime.timedelta(minutes=descanso_duracion)
                        
                        setattr(schedule, f'descanso{descanso_idx}_he', descanso_inicio.strftime('%H:%M'))
                        setattr(schedule, f'descanso{descanso_idx}_hs', descanso_fin.strftime('%H:%M'))
                        descanso_idx += 1

                # ASIGNAR PVDs
                num_pvd = duracion_redondeada
                if num_pvd > 0:
                    pvd_hora = hora_inicio + datetime.timedelta(minutes=45 + random.randint(0, 20))
                    
                    for _ in range(num_pvd):
                        if pvd_idx > 10: break
                        
                        pvd_hora_floored = pvd_hora.replace(second=0, microsecond=0)
                        
                        # Evitar solapamiento
                        if descanso_inicio and \
                           max(pvd_hora_floored, descanso_inicio) < min(pvd_hora_floored + datetime.timedelta(minutes=5), descanso_fin):
                            pvd_hora = descanso_fin + datetime.timedelta(minutes=10)
                            continue

                        if (pvd_hora_floored + datetime.timedelta(minutes=5)) < hora_fin:
                            setattr(schedule, f'pvd{pvd_idx}', pvd_hora_floored.strftime('%H:%M'))
                            pvd_idx += 1
                        
                        pvd_hora = pvd_hora_floored + datetime.timedelta(minutes=50 + random.randint(0, 15))

        updated_count += 1
    
    db.session.commit()
    return {"message": f"Proceso completado. Se asignaron descansos a {updated_count} turnos."}

def get_break_distribution_data(segment_id, start_date, end_date):
    """
    Obtiene los datos para la tabla y la gráfica de distribución de descansos.
    """
    all_schedules = Schedule.query.join(Agent).filter(
        Agent.segment_id == segment_id,
        Schedule.schedule_date.between(start_date, end_date)
    ).options(joinedload(Schedule.agent)).order_by(Agent.nombre_completo, Schedule.schedule_date).all()
    
    table_data = []
    total_work_hours = 0
    total_break_minutes = 0
    
    time_labels = [(datetime.datetime.strptime("00:00", "%H:%M") + datetime.timedelta(minutes=5 * i)).strftime('%H:%M') for i in range(288)]
    chart_data_by_day = defaultdict(lambda: {"coverage": [0]*288, "breaks": [0]*288, "pvds": [0]*288})

    for schedule in all_schedules:
        if schedule.shift in VALID_AUSENCIA_CODES or schedule.shift == 'LIBRE': 
            continue
        
        total_work_hours += schedule.hours
        shift_parts = schedule.shift.split('/')
        day_str = schedule.schedule_date.strftime('%Y-%m-%d')
        
        all_breaks = []
        if schedule.descanso1_he and schedule.descanso1_hs:
            all_breaks.append({'start': schedule.descanso1_he, 'end': schedule.descanso1_hs})
        if schedule.descanso2_he and schedule.descanso2_hs:
            all_breaks.append({'start': schedule.descanso2_he, 'end': schedule.descanso2_hs})
        
        all_pvds = [getattr(schedule, f'pvd{j}') for j in range(1, 11) if getattr(schedule, f'pvd{j}')]

        for part in shift_parts:
            if '-' not in part: continue
            try:
                start_s, end_s = part.strip().split('-')
                h_ini = datetime.datetime.strptime(start_s.strip(), "%H:%M")
                h_fin_str = end_s.strip()
                h_fin = datetime.datetime.strptime('23:59', '%H:%M') + datetime.timedelta(minutes=1) if h_fin_str == '24:00' else datetime.datetime.strptime(h_fin_str, '%H:%M')
                if (h_fin - h_ini).total_seconds() < 0: h_fin += datetime.timedelta(days=1)
            except: continue

            start_idx = int((h_ini.hour * 60 + h_ini.minute) / 5)
            end_idx = int((h_fin.hour * 60 + h_fin.minute) / 5)
            for i in range(start_idx, min(end_idx, 288)):
                chart_data_by_day[day_str]["coverage"][i] += 1

            part_break_start, part_break_end = None, None
            for b in all_breaks:
                bs = datetime.datetime.strptime(b['start'], "%H:%M")
                be = datetime.datetime.strptime(b['end'], "%H:%M")
                if h_ini <= bs < h_fin:
                    part_break_start, part_break_end = b['start'], b['end']
                    total_break_minutes += (be - bs).total_seconds() / 60
                    b_start_idx = int((bs.hour * 60 + bs.minute) / 5)
                    b_end_idx = int((be.hour * 60 + be.minute) / 5)
                    for k in range(b_start_idx, min(b_end_idx, 288)):
                        chart_data_by_day[day_str]["breaks"][k] += 1
                    break
            
            part_pvds_dict = {}
            p_count = 1
            for p in all_pvds:
                if not p: continue
                pt = datetime.datetime.strptime(p, "%H:%M")
                if h_ini <= pt < h_fin:
                    part_pvds_dict[f'pvd{p_count}'] = p
                    p_count += 1
                    total_break_minutes += 5
                    p_idx = int((pt.hour * 60 + pt.minute) / 5)
                    if p_idx < 288: chart_data_by_day[day_str]["pvds"][p_idx] += 1
            
            table_data.append({
                "unique_id": f"{schedule.id}-{part}", 
                "schedule_id": schedule.id,
                "dni": schedule.agent.identificacion, 
                "nombre": schedule.agent.nombre_completo,
                "fecha": schedule.schedule_date.strftime('%d/%m/%Y'), 
                "turno": part,
                "horas": f"{(h_fin-h_ini).total_seconds()/3600:.2f}", 
                "inicio_descanso": part_break_start, 
                "fin_descanso": part_break_end, 
                **{f'pvd{j}': part_pvds_dict.get(f'pvd{j}', None) for j in range(1, 11)}
            })

    kpi_data = {"total_work_hours": total_work_hours, "total_break_minutes": total_break_minutes}
    
    return {
        "table_data": table_data, 
        "chart_data": {"labels": time_labels, "days": chart_data_by_day}, 
        "kpi_data": kpi_data
    }

def update_manual_break(data):
    """
    Actualiza los descansos de un registro específico desde el modal.
    """
    schedule = Schedule.query.get(data.get('schedule_id'))
    if not schedule:
        raise ValueError("Registro no encontrado")
    
    schedule.descanso1_he = data.get('inicio_descanso').strip() or None
    schedule.descanso1_hs = data.get('fin_descanso').strip() or None
    
    for i in range(1, 11):
        setattr(schedule, f'pvd{i}', data.get(f'pvd{i}', '').strip() or None)
        
    db.session.commit()
    return {"message": "Descansos actualizados correctamente."}

def generate_breaks_excel(segment_id, start_date, end_date):
    """
    Genera un Excel con el detalle de descansos para descargar.
    """
    schedules = Schedule.query.join(Agent).filter(
        Agent.segment_id == segment_id,
        Schedule.schedule_date.between(start_date, end_date)
    ).options(joinedload(Schedule.agent)).order_by(Schedule.schedule_date, Agent.nombre_completo).all()

    data = []
    for s in schedules:
        if s.shift == 'LIBRE' or s.shift in VALID_AUSENCIA_CODES: continue
        
        row = {
            'Fecha': s.schedule_date.strftime('%Y-%m-%d'),
            'DNI': s.agent.identificacion,
            'Nombre': s.agent.nombre_completo,
            'Turno': s.shift,
            'Descanso 1 Inicio': s.descanso1_he,
            'Descanso 1 Fin': s.descanso1_hs,
            'Descanso 2 Inicio': s.descanso2_he,
            'Descanso 2 Fin': s.descanso2_hs
        }
        for i in range(1, 11):
            val = getattr(s, f'pvd{i}')
            if val: row[f'PVD {i}'] = val
        
        data.append(row)

    df = pd.DataFrame(data)
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Descansos')
    writer.close()
    output.seek(0)
    
    return output