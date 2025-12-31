# app/api_routes.py

from flask import Blueprint, request, jsonify, session, send_file, current_app
import pandas as pd
import numpy as np
import io
import datetime
from datetime import timedelta
import json
import traceback
from collections import defaultdict
import math
import random 
from werkzeug.security import generate_password_hash
from sqlalchemy import or_, not_, and_
from sqlalchemy.orm import joinedload
import functools

# --- IMPORTACIÓN DE SERVICIOS ---
from .services import staffing_service, scheduling_service, forecasting_service, breaks_service

from . import db
from .models import (
    User, Segment, StaffingResult, ActualsData, Agent, Schedule, 
    SchedulingRule, MonthlyForecast, Campaign, Absence, BreakRule,
    ShiftChangeRequest, Scenario
)
from .constants import VALID_AUSENCIA_CODES
from .services.agent_loader_service import load_agents_from_excel

# --- 1. DEFINICIÓN ÚNICA DEL BLUEPRINT ---
bp = Blueprint('api', __name__, url_prefix='/api')

# --- 2. DECORADOR DE AUTORIZACIÓN ---
def api_login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Sesión expirada o no autorizada."}), 401
        return view(**kwargs)
    return wrapped_view

@bp.before_request
@api_login_required
def before_request():
    pass

# --- 3. FUNCIONES DE AYUDA ---
def _format_and_calculate_simple(df_frac):
    if df_frac is None or df_frac.empty: return pd.DataFrame()
    df_display = df_frac.copy()
    
    time_cols_format = [col for col in df_display.columns if ':' in str(col)]
    
    # Redondeo de los valores de intervalo para limpieza visual
    df_display[time_cols_format] = df_display[time_cols_format].round(2)
    
    # CÁLCULO DEL TOTAL REDONDEADO A 2 DECIMALES
    df_display['Horas-Totales'] = (df_frac[time_cols_format].sum(axis=1) / 2.0).round(2)
    
    if 'Fecha' in df_display.columns:
        df_display['Fecha'] = pd.to_datetime(df_display['Fecha']).dt.strftime('%d/%m/%Y')
        
    return df_display

def _transform_hourly_to_half_hourly(output_rows, time_labels):
    if not output_rows or not time_labels or len(time_labels) < 2: return output_rows, time_labels
    try:
        t1 = datetime.datetime.strptime(time_labels[0], '%H:%M'); t2 = datetime.datetime.strptime(time_labels[1], '%H:%M')
        is_hourly = (t2 - t1).total_seconds() == 3600
    except (ValueError, IndexError): is_hourly = False
    if not is_hourly: return output_rows, time_labels
    transformed_rows, new_time_labels = [], []
    for row in output_rows:
        new_row = {'Fecha': row['Fecha'], 'Dia': row['Dia'], 'Semana': row['Semana'], 'Tipo': row['Tipo']}
        for hour_label in time_labels:
            volume = row.get(hour_label, 0)
            half_volume_1 = volume // 2; half_volume_2 = volume - half_volume_1
            t = datetime.datetime.strptime(hour_label, '%H:%M')
            half_hour_label = (t + datetime.timedelta(minutes=30)).strftime('%H:%M')
            new_row[hour_label] = half_volume_1; new_row[half_hour_label] = half_volume_2
        transformed_rows.append(new_row)
    for hour_label in time_labels:
        t = datetime.datetime.strptime(hour_label, '%H:%M')
        half_hour_label = (t + datetime.timedelta(minutes=30)).strftime('%H:%M')
        new_time_labels.extend([hour_label, half_hour_label])
    return transformed_rows, sorted(list(set(new_time_labels)))


# ==============================================================================
# SECCIÓN: GESTIÓN DE ABSENTISMOS
# ==============================================================================

@bp.route('/upload_absences_file', methods=['POST'])
def upload_absences_file():
    try:
        if 'ausencias_excel_file' not in request.files:
            return jsonify({"error": "Falta el archivo."}), 400
        
        file = request.files['ausencias_excel_file']
        segment_id = request.form.get('segment_id')

        if not segment_id: return jsonify({"error": "Falta segmento."}), 400

        try:
            df = pd.read_excel(file)
        except Exception:
            return jsonify({"error": "Archivo corrupto o formato inválido."}), 400
            
        df.columns = [str(c).strip().upper() for c in df.columns]

        # Detección de columnas
        col_dni = next((c for c in df.columns if c == 'DNI'), None)
        col_nie = next((c for c in df.columns if 'CODIGO EMPLEADO' in c), None)
        col_inc = next((c for c in df.columns if 'NOMBRE INCIDEN' in c or 'NOMBRE ABSENTISMO' in c), None)
        col_start = next((c for c in df.columns if 'FECHA INICIO' in c), None)
        col_end = next((c for c in df.columns if 'FECHA FIN' in c), None)

        if not col_inc or not col_start:
            return jsonify({"error": "No se encontraron columnas de Incidencia o Fecha Inicio."}), 400

        Absence.query.filter_by(segment_id=segment_id).delete()
        
        agents = Agent.query.filter_by(segment_id=segment_id).all()
        valid_ids = {}
        for a in agents:
            clean_id = str(a.identificacion).strip().upper().replace('.0', '')
            valid_ids[clean_id] = a.id
        
        new_absences = []
        count = 0
        SAFE_FUTURE_DATE = datetime.date(2027, 12, 31)

        for index, row in df.iterrows():
            agent_id = None
            val_dni = str(row[col_dni]).strip().upper().replace('.0', '') if col_dni and pd.notna(row[col_dni]) else None
            val_nie = str(row[col_nie]).strip().upper().replace('.0', '') if col_nie and pd.notna(row[col_nie]) else None
            
            if val_dni: agent_id = valid_ids.get(val_dni)
            if not agent_id and val_nie: agent_id = valid_ids.get(val_nie)
            
            if not agent_id: continue

            raw_name = str(row[col_inc]).strip().upper()
            code = None

            if "VACACIO" in raw_name: code = "VAC"
            elif any(x in raw_name for x in ["ENFERMEDAD", "ACCIDENTE", "HOSPITAL", "BAJA", "IT "]): code = "BMED"
            elif any(x in raw_name for x in ["MATERNIDAD", "LACTANCIA", "EMBARAZO"]): code = "LICMATER"
            elif any(x in raw_name for x in ["PATERNIDAD", "PARENTAL"]): code = "LICPATER"
            elif any(x in raw_name for x in ["FALTA", "AUSENCIA", "PERMISO", "SANCION"]): code = "AUSENCIA"
            
            if not code: continue 

            try:
                start = pd.to_datetime(row[col_start], dayfirst=True, errors='coerce')
                if pd.isna(start): continue
                start = start.date()
                
                if col_end and pd.notna(row[col_end]):
                    str_end = str(row[col_end])
                    if '4000' in str_end or '2999' in str_end:
                        end = SAFE_FUTURE_DATE
                    else:
                        end_dt = pd.to_datetime(row[col_end], dayfirst=True, errors='coerce')
                        if pd.isna(end_dt): end = start
                        else:
                            end = end_dt.date()
                            if end > SAFE_FUTURE_DATE: end = SAFE_FUTURE_DATE
                else:
                    end = start 
            except Exception: continue

            delta = (end - start).days
            if delta < 0: continue 
            if delta > 2000: delta = 2000 

            for i in range(delta + 1):
                curr_date = start + timedelta(days=i)
                new_absences.append(Absence(
                    agent_id=agent_id,
                    segment_id=segment_id,
                    date=curr_date,
                    absence_code=code
                ))
                count += 1

        if new_absences:
            BATCH_SIZE = 2000
            for i in range(0, len(new_absences), BATCH_SIZE):
                db.session.bulk_save_objects(new_absences[i:i + BATCH_SIZE])
            db.session.commit()
            return jsonify({"message": f"Carga exitosa. {count} días de absentismo consolidados en BDB."})
        else:
            return jsonify({"message": "No se guardaron datos. Verifica identificaciones."}), 200

    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({"error": f"Error crítico: {str(e)}"}), 500


@bp.route('/apply_absences_updates', methods=['POST'])
def apply_absences_updates():
    try:
        items = request.json.get('items', [])
        count = 0
        for item in items:
            date = datetime.datetime.strptime(item['fecha'], '%Y-%m-%d').date()
            agent_id = item['agent_id']
            new_code = item['valor_nuevo']
            
            sched = Schedule.query.filter_by(agent_id=agent_id, schedule_date=date).first()
            if sched:
                sched.shift = new_code
                sched.hours = 0
                sched.is_manual_edit = True
            else:
                db.session.add(Schedule(
                    agent_id=agent_id, schedule_date=date, shift=new_code, hours=0, is_manual_edit=True
                ))
            count += 1
        
        db.session.commit()
        return jsonify({"message": f"{count} novedades aplicadas correctamente."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ==============================================================================
# SECCIÓN: PLANIFICACIÓN (SCHEDULING)
# ==============================================================================

@bp.route('/schedule/run/<int:segment_id>', methods=['POST'])
def run_schedule_for_campaign_segment(segment_id):
    data = request.get_json()
    if not all(k in data for k in ['start_date', 'end_date']): return jsonify({"error": "Faltan fechas."}), 400

    try:
        start_date = datetime.date.fromisoformat(data['start_date'])
        end_date = datetime.date.fromisoformat(data['end_date'])
    except (ValueError, TypeError): return jsonify({"error": "Formato de fecha inválido."}), 400

    segment = Segment.query.get(segment_id)
    if not segment: return jsonify({"error": "Segmento no encontrado."}), 404
    
    all_agents = Agent.query.filter_by(segment_id=segment.id).options(joinedload(Agent.scheduling_rule)).all()
    agents_to_schedule = [a for a in all_agents if a.scheduling_rule is not None]
    if not agents_to_schedule: return jsonify({"message": "No hay agentes para planificar."}), 200

    # Recuperar BDB de Absentismos
    stored_absences = Absence.query.filter(
        Absence.segment_id == segment_id,
        Absence.date.between(start_date, end_date)
    ).all()

    locked_schedule_map = {}
    for abs_rec in stored_absences:
        dummy_entry = Schedule(
            agent_id=abs_rec.agent_id, 
            schedule_date=abs_rec.date, 
            shift=abs_rec.absence_code, 
            is_manual_edit=True
        )
        locked_schedule_map[(abs_rec.agent_id, abs_rec.date)] = dummy_entry

    staffing_needs_raw = StaffingResult.query.filter(
        StaffingResult.segment_id == segment.id,
        StaffingResult.result_date.between(start_date, end_date)
    ).all()
    
    time_labels_list = []
    needs_by_day = {}
    
    if staffing_needs_raw:
        try:
            first_valid = next((r for r in staffing_needs_raw if r.agents_online and r.agents_online != '{}'), None)
            if first_valid:
                time_labels_list = sorted([k for k in json.loads(first_valid.agents_online).keys() if ':' in str(k)])
                for r in staffing_needs_raw:
                    day_data = json.loads(r.agents_online or '{}')
                    needs_by_day[r.result_date] = [math.ceil(float(day_data.get(lbl, 0) or 0)) for lbl in time_labels_list]
        except: pass

    if not time_labels_list:
        dt = datetime.datetime(2000,1,1,0,0)
        while dt.day == 1:
            time_labels_list.append(dt.strftime('%H:%M'))
            dt += datetime.timedelta(minutes=30)

    try:
        # --- CORRECCIÓN AQUÍ: Usar 'Scheduler' en lugar de 'SchedulingService' ---
        scheduler = scheduling_service.Scheduler(
            agents=agents_to_schedule, 
            segment=segment, 
            needs_by_day=needs_by_day,
            time_labels_list=time_labels_list, 
            start_date=start_date,
            end_date=end_date,
            existing_schedule_map=locked_schedule_map
        )
        result_schedule, _ = scheduler.run()
        
        if "error" in result_schedule: return jsonify(result_schedule), 500
            
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Error en planificador: {str(e)}"}), 500

    # Guardar Resultados
    try:
        Schedule.query.filter(
            Schedule.agent_id.in_([a.id for a in agents_to_schedule]),
            Schedule.schedule_date.between(start_date, end_date)
        ).delete(synchronize_session=False)

        new_schedule_entries = []
        agent_map_by_name = {a.nombre_completo: a for a in agents_to_schedule}

        for agent_name, daily_shifts in result_schedule.items():
            agent_obj = agent_map_by_name.get(agent_name)
            if not agent_obj: continue

            for date_str, shift_name in daily_shifts.items():
                curr_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
                is_absence = (agent_obj.id, curr_date) in locked_schedule_map
                hours = scheduling_service.calculate_shift_duration_helper(shift_name)
                
                new_schedule_entries.append(Schedule(
                    agent_id=agent_obj.id,
                    schedule_date=curr_date,
                    shift=shift_name,
                    hours=hours,
                    is_manual_edit=is_absence
                ))

        if new_schedule_entries:
            db.session.bulk_save_objects(new_schedule_entries)
            db.session.commit()

        return jsonify({"message": f"Planificación generada. Se aplicaron {len(locked_schedule_map)} novedades desde la base de datos."})

    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({"error": f"Error al guardar: {str(e)}"}), 500


@bp.route('/get_schedule_with_conflicts', methods=['POST'])
def get_schedule_with_conflicts():
    try:
        # Importación local para evitar ciclos si es necesario
        from .services import scheduling_service
        
        data = request.form 
        segment_id = data.get('segment_id')
        start_date = datetime.datetime.strptime(data.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.datetime.strptime(data.get('end_date'), '%Y-%m-%d').date()
        
        # --- NUEVO: GESTIÓN DE ESCENARIO ---
        scenario_id = data.get('scenario_id')
        
        # Si no viene escenario, buscamos el Oficial por defecto
        if not scenario_id or scenario_id == 'official':
            official_scen = Scenario.query.filter_by(segment_id=segment_id, is_official=True).first()
            if official_scen:
                scenario_id = official_scen.id
            else:
                # Fallback de seguridad si no existen escenarios aún
                return jsonify({"error": "No se encontró un escenario oficial para este segmento."}), 404

        # 1. Construir la vista (Pasamos el scenario_id al servicio)
        # Nota: Debes haber actualizado build_schedule_view_model en scheduling_service.py para aceptar este argumento
        view_data = scheduling_service.build_schedule_view_model(
            segment_id, start_date, end_date, ausencias_file=None, scenario_id=scenario_id
        )
        
        # 2. Obtener Ausencias (Estas suelen ser globales/reales, por eso filtramos por segmento)
        stored_absences = Absence.query.filter(
            Absence.segment_id == segment_id,
            Absence.date.between(start_date, end_date)
        ).all()
        
        # 3. Obtener Horarios (Estos SÍ dependen del escenario)
        current_schedules = Schedule.query.filter(
            Schedule.scenario_id == scenario_id,  # <--- FILTRO CLAVE
            Schedule.schedule_date.between(start_date, end_date)
        ).all()
        
        schedule_map = {(s.agent_id, s.schedule_date): s.shift for s in current_schedules}
        
        # Mapa de agentes (Reales + Simulados de este escenario)
        # Traemos todos para asegurar que encontramos el nombre si hay conflicto
        all_agents = Agent.query.filter(
            Agent.segment_id == segment_id,
            or_(Agent.scenario_id == None, Agent.scenario_id == scenario_id)
        ).all()
        agent_map = {a.id: a for a in all_agents}
        
        conflicts = []
        for abs_rec in stored_absences:
            # Verificamos qué turno tiene asignado en ESTE escenario
            current_shift = schedule_map.get((abs_rec.agent_id, abs_rec.date), "LIBRE")
            
            # Si el turno en la simulación difiere de la ausencia real, es un conflicto
            if current_shift != abs_rec.absence_code:
                agent = agent_map.get(abs_rec.agent_id)
                if agent:
                    conflicts.append({
                        "agent_id": abs_rec.agent_id,
                        "nombre": agent.nombre_completo,
                        "identificacion": agent.identificacion,
                        "fecha": abs_rec.date.strftime('%Y-%m-%d'),
                        "fecha_display": abs_rec.date.strftime('%d/%m/%Y'),
                        "valor_actual": current_shift,
                        "valor_nuevo": abs_rec.absence_code,
                        "es_conflicto": True
                    })
        
        view_data['pending_conflicts'] = conflicts
        return jsonify(view_data)

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ==============================================================================
# SECCIÓN: DESCANSOS (BREAKS)
# ==============================================================================

@bp.route('/assign_breaks', methods=['POST'])
def assign_breaks():
    try:
        data = request.json
        result = breaks_service.assign_breaks_to_schedule(
            data.get('segment_id'),
            datetime.datetime.strptime(data.get('start_date'), '%Y-%m-%d').date(),
            datetime.datetime.strptime(data.get('end_date'), '%Y-%m-%d').date()
        )
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Error: {str(e)}"}), 500

@bp.route('/get_break_distribution', methods=['POST'])
def get_break_distribution():
    try:
        data = request.json
        result = breaks_service.get_break_distribution_data(
            data.get('segment_id'),
            datetime.datetime.strptime(data.get('start_date'), '%Y-%m-%d').date(),
            datetime.datetime.strptime(data.get('end_date'), '%Y-%m-%d').date()
        )
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Error: {str(e)}"}), 500

@bp.route('/update_breaks_bulk', methods=['POST'])
def update_breaks_bulk():
    try:
        result = breaks_service.update_manual_break(request.json)
        return jsonify(result)
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@bp.route('/download_breaks', methods=['POST'])
def download_breaks():
    try:
        file_output = breaks_service.generate_breaks_excel(
            request.form.get('segment_id'),
            datetime.datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date(),
            datetime.datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
        )
        return send_file(
            file_output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='Descansos.xlsx'
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/get_break_rules/<int:segment_id>', methods=['GET'])
def get_break_rules(segment_id):
    try:
        segment = Segment.query.get(segment_id)
        if not segment: return jsonify({"error": "Segmento no encontrado"}), 404
        rules = BreakRule.query.filter_by(country=segment.campaign.country).first()
        data = {
            "min_shift_hours": rules.min_shift_hours if rules else 6,
            "max_shift_hours": rules.max_shift_hours if rules else 9,
            "break_duration": rules.break_duration_minutes if rules else 20,
            "pvd_duration": rules.pvd_minutes_per_hour if rules else 5,
            "num_pvds": rules.number_of_pvds if rules else 2
        }
        return jsonify(data)
    except Exception as e: return jsonify({"error": str(e)}), 500

@bp.route('/save_break_rules', methods=['POST'])
def save_break_rules():
    return jsonify({"message": "Reglas actualizadas."})

# ==============================================================================
# SECCIÓN: SUMMARY (RESTAURADA COMPLETA)
# ==============================================================================

@bp.route('/get_summary', methods=['POST'])
def get_summary():
    try:
        data = request.json
        segment_id = data.get('segment_id')
        start_date = datetime.datetime.strptime(data.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.datetime.strptime(data.get('end_date'), '%Y-%m-%d').date()

        segment = Segment.query.get(segment_id)
        if not segment: return jsonify({"error": "Segmento no encontrado."}), 404
        service_type = segment.service_type

        results = StaffingResult.query.filter(
            StaffingResult.segment_id == segment_id,
            StaffingResult.result_date.between(start_date, end_date)
        ).order_by(StaffingResult.result_date).all()

        if not results:
            return jsonify({"error": "No se encontraron datos de dimensionamiento para los filtros seleccionados."}), 404

        all_schedules_in_period = Schedule.query.join(Agent).filter(
            Agent.segment_id == segment_id,
            Schedule.schedule_date.between(start_date, end_date)
        ).all()
        
        first_valid_result = next((r for r in results if r.agents_online and r.agents_online != '{}'), None)
        if not first_valid_result:
            return jsonify({"error": "No se encontraron datos con intervalos de tiempo válidos."}), 404

        time_labels = sorted([k for k in json.loads(first_valid_result.agents_online).keys() if ':' in k])
        
        # SLA targets (default fallback)
        SLA_PERCENT_TARGET = results[0].sla_target_percentage if results[0].sla_target_percentage is not None else 0.80
        SLA_TIME_TARGET = results[0].sla_target_time if results[0].sla_target_time is not None else 20

        date_range = [start_date + datetime.timedelta(days=i) for i in range((end_date - start_date).days + 1)]
        coverage_by_day = {day: {label: 0 for label in time_labels} for day in date_range}
        
        for s in all_schedules_in_period:
            if s.shift and '-' in s.shift and s.shift not in VALID_AUSENCIA_CODES:
                try:
                    for part in s.shift.split('/'):
                        start_str, end_str = [x.strip() for x in part.split('-')]
                        start_idx = time_labels.index(start_str)
                        end_idx = time_labels.index(end_str) if end_str != "24:00" else len(time_labels)
                        for i in range(start_idx, end_idx):
                            if s.schedule_date in coverage_by_day:
                                coverage_by_day[s.schedule_date][time_labels[i]] += 1
                except (ValueError, IndexError): continue
        
        summary_data = {}
        for r in results:
            day_str = r.result_date.strftime('%d/%m/%Y')
            planned_hc = coverage_by_day.get(r.result_date, {})
            reducers = json.loads(r.reducers_forecast or '{}')
            calls = json.loads(r.calls_forecast or '{}')
            aht = json.loads(r.aht_forecast or '{}')
            required_hc = json.loads(r.agents_online or '{}')
            
            present_hc = {lbl: planned_hc.get(lbl, 0) * (1 - float(reducers.get("absenteeism", {}).get(lbl, 0) or 0)) for lbl in time_labels}
            logged_hc = {lbl: present_hc.get(lbl, 0) * (1 - float(reducers.get("shrinkage", {}).get(lbl, 0) or 0)) for lbl in time_labels}
            effective_hc = {lbl: logged_hc.get(lbl, 0) * (1 - float(reducers.get("auxiliaries", {}).get(lbl, 0) or 0)) for lbl in time_labels}

            over_under, sl_real, nda_real, capacity, handled_calls, attended_within_sla = {}, {}, {}, {}, {}, {}
            
            # Cálculos Inbound vs Backoffice
            if service_type == 'INBOUND':
                for lbl in time_labels:
                    agents = math.floor(effective_hc.get(lbl, 0))
                    aht_val = float(aht.get(lbl, 0) or 0)
                    calls_val = float(calls.get(lbl, 0) or 0)
                    
                    over_under[lbl] = effective_hc.get(lbl, 0) - (float(required_hc.get(lbl, 0) or 0))
                    capacity_val = staffing_service._calculate_sl_capacity(agents, aht_val, SLA_PERCENT_TARGET, SLA_TIME_TARGET)
                    capacity[lbl] = capacity_val
                    handled_calls[lbl] = min(capacity_val, calls_val)
                    attainable_with_sla = capacity_val * SLA_PERCENT_TARGET
                    attended_within_sla[lbl] = min(calls_val, attainable_with_sla)
                    
                    sl_real[lbl] = (attended_within_sla[lbl] / calls_val) if calls_val > 0 else 1.0
                    nda_real[lbl] = (handled_calls[lbl] / calls_val) if calls_val > 0 else 1.0
                summary_data[day_str] = {'planned_headcount': planned_hc, 'present_headcount': present_hc, 'logged_headcount': logged_hc, 'effective_headcount': effective_hc, 'calls_forecast': calls, 'aht_forecast': aht, 'over_under_staffing': over_under, 'call_capacity': capacity, 'service_level_real': sl_real, 'attention_level_real': nda_real, 'handled_calls': handled_calls, 'attended_within_sla': attended_within_sla }

            elif service_type in ['BACKOFFICE', 'OUTBOUND']:
                tasks_req, capacity_task, handled_task, productivity, deficit = {}, {}, {}, {}, {}
                for lbl in time_labels:
                    effective_hours = effective_hc.get(lbl, 0) * 0.5
                    aht_val = float(aht.get(lbl, 0) or 0)
                    tasks_val = float(calls.get(lbl, 0) or 0)
                    
                    tasks_req[lbl] = tasks_val
                    task_cap = (effective_hours * 3600 / aht_val) if aht_val > 0 else 0
                    capacity_task[lbl] = task_cap
                    handled_task[lbl] = min(task_cap, tasks_val)
                    productivity[lbl] = (handled_task[lbl] / tasks_val) if tasks_val > 0 else 1.0
                    deficit[lbl] = task_cap - tasks_val

                summary_data[day_str] = {'planned_headcount': planned_hc, 'effective_headcount': effective_hc, 'tasks_forecast': tasks_req, 'aht_forecast': aht, 'task_capacity': capacity_task, 'tasks_handled': handled_task, 'productivity': productivity, 'deficit_surplus': deficit}


        # Totales del periodo
        if service_type == 'INBOUND':
            totals = { key: 0 for key in ['calls', 'aht_weighted', 'capacity', 'handled', 'attended_sla', 'h_plan', 'h_pres', 'h_log', 'h_eff'] }
            def sum_ts(d): return sum(float(v or 0) for k,v in d.items() if ':' in str(k))
            for day_data in summary_data.values():
                totals['calls'] += sum_ts(day_data['calls_forecast'])
                totals['capacity'] += sum_ts(day_data['call_capacity'])
                totals['handled'] += sum_ts(day_data['handled_calls'])
                totals['attended_sla'] += sum_ts(day_data['attended_within_sla'])
                totals['h_plan'] += sum_ts(day_data['planned_headcount'])*0.5
                totals['h_pres'] += sum_ts(day_data['present_headcount'])*0.5
                totals['h_log'] += sum_ts(day_data['logged_headcount'])*0.5
                totals['h_eff'] += sum_ts(day_data['effective_headcount'])*0.5
                for lbl in time_labels: totals['aht_weighted'] += float(day_data['calls_forecast'].get(lbl, 0) or 0) * float(day_data['aht_forecast'].get(lbl, 0) or 0)
            
            num_days = (end_date - start_date).days + 1
            vac_count = sum(1 for s in all_schedules_in_period if s.shift == 'VAC')
            bmed_count = sum(1 for s in all_schedules_in_period if s.shift == 'BMED')

            period_summary = {
                "Total Llamadas": totals['calls'], "AHT promedio": totals['aht_weighted'] / totals['calls'] if totals['calls'] > 0 else 0,
                "Call Capacity Total": totals['capacity'], "Llamadas Atendidas Alcanzables": totals['handled'], "Total Atendidas < Objetivo": totals['attended_sla'],
                "NS Final": totals['attended_sla'] / totals['calls'] if totals['calls'] > 0 else 1.0, "NDA Final": totals['handled'] / totals['calls'] if totals['calls'] > 0 else 1.0,
                "Horas Dimensionadas": totals['h_plan'], "Horas Presentes": totals['h_pres'], "Horas Logadas": totals['h_log'], "Horas efectivas": totals['h_eff'],
                "Adherencia Bruta": totals['h_log'] / totals['h_pres'] if totals['h_pres'] > 0 else 0, "Adherencia Neta": totals['h_eff'] / totals['h_log'] if totals['h_log'] > 0 else 0,
                "VAC promedio": vac_count / num_days if num_days > 0 else 0, "BMED promedio": bmed_count / num_days if num_days > 0 else 0
            }
            
            tables = {
                "planned": format_table("planned_headcount", "Asesores Planificados", summary_data, time_labels), 
                "present": format_table("present_headcount", "Asesores Presentes", summary_data, time_labels),
                "logged": format_table("logged_headcount", "Asesores Logados", summary_data, time_labels), 
                "effective": format_table("effective_headcount", "Asesores Efectivos", summary_data, time_labels),
                "over_under": format_table("over_under_staffing", "Sobredimensionamiento / Subdimensionamiento", summary_data, time_labels), 
                "service_level": format_table("service_level_real", "Nivel de Servicio", summary_data, time_labels, is_percent=True, is_kpi=True),
                "attention_level": format_table("attention_level_real", "Nivel de Atención", summary_data, time_labels, is_percent=True, is_kpi=True), 
                "calls": format_table("calls_forecast", "Llamadas Pronosticadas", summary_data, time_labels),
                "attended_within_sla": format_table("attended_within_sla", "Total Atendidas < Objetivo", summary_data, time_labels), 
                "handled_calls": format_table("handled_calls", "Llamadas Atendidas Alcanzables", summary_data, time_labels),
                "aht": format_table("aht_forecast", "AHT Pronosticado", summary_data, time_labels), 
                "capacity": format_table("call_capacity", "Capacidad Máxima de Llamadas", summary_data, time_labels)
            }

        else: # BACKOFFICE
            totals = {'tasks': 0, 'handled': 0, 'h_plan': 0, 'h_eff': 0, 'aht_w': 0}
            def sum_ts(d): return sum(float(v or 0) for k,v in d.items() if ':' in str(k))
            for day_data in summary_data.values():
                totals['tasks'] += sum_ts(day_data['tasks_forecast']); totals['handled'] += sum_ts(day_data['tasks_handled'])
                totals['h_plan'] += sum_ts(day_data['planned_headcount'])*0.5; totals['h_eff'] += sum_ts(day_data['effective_headcount'])*0.5
                for lbl in time_labels: totals['aht_w'] += float(day_data['tasks_forecast'].get(lbl, 0) or 0) * float(day_data['aht_forecast'].get(lbl, 0) or 0)
            
            period_summary = {
                "Total Tareas": totals['tasks'], "Total Gestionadas": totals['handled'], "Productividad": totals['handled']/totals['tasks'] if totals['tasks']>0 else 0,
                "AHT Promedio": totals['aht_w']/totals['tasks'] if totals['tasks']>0 else 0, "Horas Planificadas": totals['h_plan'], "Horas Efectivas": totals['h_eff']
            }
            tables = {
                "planned": format_table("planned_headcount", "Planificados", summary_data, time_labels), "effective": format_table("effective_headcount", "Efectivos", summary_data, time_labels),
                "tasks": format_table("tasks_forecast", "Tareas Requeridas", summary_data, time_labels), "handled": format_table("tasks_handled", "Tareas Gestionadas", summary_data, time_labels),
                "capacity": format_table("task_capacity", "Capacidad", summary_data, time_labels), "deficit": format_table("deficit_surplus", "Déficit", summary_data, time_labels)
            }

        return jsonify({ "tables": tables, "summary": period_summary })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Ocurrió un error al procesar el resumen: {str(e)}"}), 500

def format_table(key, title, data_source, time_labels, is_percent=False, is_kpi=False):
    cols = ['Día'] + time_labels + ['Total/Promedio']
    rows = []
    for day, data in sorted(data_source.items(), key=lambda i: datetime.datetime.strptime(i[0], '%d/%m/%Y')):
        row = {'Día': day}
        series = data.get(key, {})
        numeric_values = [float(series.get(lbl, 0) or 0) for lbl in time_labels]
        for i, lbl in enumerate(time_labels): row[lbl] = numeric_values[i]
        
        daily_total = sum(numeric_values)
        if key.endswith('_headcount') or key in ['over_under_staffing', 'deficit_surplus']:
            row['Total/Promedio'] = daily_total * 0.5
        elif is_kpi:
            base_key = 'calls_forecast' if 'calls_forecast' in data else 'tasks_forecast'
            calls_day = data.get(base_key, {})
            w_sum = sum(val * float(calls_day.get(time_labels[i], 0) or 0) for i, val in enumerate(numeric_values))
            t_calls = sum(float(v or 0) for k,v in calls_day.items() if ':' in k)
            row['Total/Promedio'] = w_sum / t_calls if t_calls > 0 else 0
        else:
            row['Total/Promedio'] = daily_total
        rows.append(row)
    
    # Calcular total del periodo (suma simple de la columna Total, salvo KPIs que no se suman)
    total_val = sum(row['Total/Promedio'] for row in rows) if not is_kpi else None
    return {'table_key': key, 'title': title, 'is_percent': is_percent, 'is_kpi': is_kpi, 'columns': cols, 'data': rows, 'period_total': total_val}


# ==============================================================================
# SECCIÓN: FORECASTING (TODAS LAS RUTAS COMPLETAS)
# ==============================================================================

# --- 1. SEGUIMIENTO (ACTUALS VS FORECAST) ---

@bp.route('/upload_actuals', methods=['POST'])
def upload_actuals():
    try:
        if 'actuals_excel' not in request.files: return jsonify({"error": "Falta archivo."}), 400
        segment_id = request.form.get('segment_id')
        file = request.files['actuals_excel']
        all_sheets_df = pd.read_excel(file, sheet_name=['ENTRANTES', 'ATENDIDAS', 'NDS', 'AHT'])
        
        df_entrantes = all_sheets_df['ENTRANTES']
        date_col = df_entrantes.columns[3] if len(df_entrantes.columns) > 3 else df_entrantes.columns[0]
        time_cols = [col for col in df_entrantes.columns if isinstance(col, (datetime.time, datetime.datetime)) or ':' in str(col)]

        for index in df_entrantes.index:
            date_val = df_entrantes.loc[index, date_col]
            if pd.isna(pd.to_datetime(date_val, errors='coerce')): continue
            date = pd.to_datetime(date_val).date()
            
            day_data = {}
            for col in time_cols:
                interval = col.strftime('%H:%M') if isinstance(col, (datetime.time, datetime.datetime)) else str(col)
                day_data[interval] = {
                    "entrantes": float(all_sheets_df['ENTRANTES'].loc[index, col] or 0),
                    "atendidas": float(all_sheets_df['ATENDIDAS'].loc[index, col] or 0),
                    "nds": float(all_sheets_df['NDS'].loc[index, col] or 0),
                    "aht": float(all_sheets_df['AHT'].loc[index, col] or 0),
                }
            
            existing = ActualsData.query.filter_by(result_date=date, segment_id=segment_id).first()
            json_str = json.dumps(day_data)
            if existing: existing.actuals_data = json_str
            else: db.session.add(ActualsData(result_date=date, segment_id=segment_id, actuals_data=json_str))
        
        db.session.commit()
        return jsonify({"message": "Datos reales cargados."})
    except Exception as e:
        db.session.rollback(); return jsonify({"error": str(e)}), 500

@bp.route('/get_forecasting_data', methods=['POST'])
def get_forecasting_data():
    try:
        data = request.json
        segment_id = data.get('segment_id')
        start_date = datetime.datetime.strptime(data.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.datetime.strptime(data.get('end_date'), '%Y-%m-%d').date()
        
        forecast_results = StaffingResult.query.filter(
            StaffingResult.segment_id == segment_id, 
            StaffingResult.result_date.between(start_date, end_date)
        ).order_by(StaffingResult.result_date).all()
        
        actuals_results = ActualsData.query.filter(
            ActualsData.segment_id == segment_id, 
            ActualsData.result_date.between(start_date, end_date)
        ).all()

        if not forecast_results: return jsonify({"error": "No se encontraron datos de pronóstico."}), 404
            
        actuals_map = {r.result_date: r for r in actuals_results}
        response_data = []
        
        for forecast in forecast_results:
            date = forecast.result_date
            try:
                forecast_calls_data = json.loads(forecast.calls_forecast or '{}')
                forecast_aht_data = json.loads(forecast.aht_forecast or '{}')
            except: continue
            
            total_forecast_calls = sum(float(v or 0) for k, v in forecast_calls_data.items() if ':' in str(k))
            weighted_aht_sum = sum(float(forecast_calls_data.get(k, 0) or 0) * float(forecast_aht_data.get(k, 0) or 0) for k in forecast_calls_data if ':' in str(k))
            avg_forecast_aht = (weighted_aht_sum / total_forecast_calls) if total_forecast_calls > 0 else 0
            
            day_summary = {
                "date": date.strftime('%d/%m/%Y'), "forecast_calls": round(total_forecast_calls), "forecast_aht": round(avg_forecast_aht),
                "real_entrantes": "N/A", "real_atendidas": "N/A", "real_aht": "N/A", "real_nda": "N/A", "real_llamadas_nds": "N/A",
                "real_nds_percent": "N/A", "real_nda_numeric": None, "desviacion_llamadas_percent": "N/A", "desviacion_aht_percent": "N/A"
            }

            if date in actuals_map:
                try:
                    actuals_json = json.loads(actuals_map[date].actuals_data)
                    total_real_entrantes = sum(float(d.get('entrantes', 0) or 0) for d in actuals_json.values())
                    total_real_atendidas = sum(float(d.get('atendidas', 0) or 0) for d in actuals_json.values())
                    total_real_nds_calls = sum(float(d.get('nds', 0) or 0) for d in actuals_json.values())
                    weighted_real_aht_sum = sum(float(d.get('atendidas', 0) or 0) * float(d.get('aht', 0) or 0) for d in actuals_json.values())
                    
                    avg_real_aht = (weighted_real_aht_sum / total_real_atendidas) if total_real_atendidas > 0 else 0
                    avg_real_nda_percent = (total_real_atendidas / total_real_entrantes) * 100 if total_real_entrantes > 0 else 0
                    avg_real_nds_percent = (total_real_nds_calls / total_real_atendidas) * 100 if total_real_atendidas > 0 else 0
                    desv_calls_pct = ((total_real_entrantes - total_forecast_calls) / total_forecast_calls) * 100 if total_forecast_calls > 0 else 0
                    desv_aht_pct = ((avg_real_aht - avg_forecast_aht) / avg_forecast_aht) * 100 if avg_forecast_aht > 0 else 0
                    
                    day_summary.update({
                        "real_entrantes": round(total_real_entrantes), "real_atendidas": round(total_real_atendidas), "real_aht": round(avg_real_aht),
                        "real_nda": f"{avg_real_nda_percent:.1f}%", "real_llamadas_nds": round(total_real_nds_calls),
                        "real_nds_percent": f"{avg_real_nds_percent:.1f}%", "real_nda_numeric": avg_real_nda_percent,
                        "desviacion_llamadas_percent": f"{desv_calls_pct:.1f}%", "desviacion_aht_percent": f"{desv_aht_pct:.1f}%"
                    })
                except: pass
            response_data.append(day_summary)
        return jsonify(response_data)
    except Exception as e: return jsonify({"error": f"Error: {str(e)}"}), 500


# --- 2. FORECASTING INTRADÍA (PATRONES) ---

@bp.route('/calculate_intraday_distribution', methods=['POST'])
def calculate_intraday_distribution():
    """Opción A: Análisis por semanas recientes"""
    try:
        file = request.files['historical_data']
        weeks = int(request.form.get('weeks_to_analyze', '10'))
        result = forecasting_service.analyze_intraday_distribution(file, weeks)
        return jsonify(result)
    except Exception as e: return jsonify({"error": str(e)}), 500

@bp.route('/analyze_specific_date_historically', methods=['POST'])
def analyze_specific_date_historically_route():
    """Opción B: Análisis de una fecha histórica (ej: 25 Dic)"""
    try:
        file = request.files['historical_data']
        target_date = request.form.get('target_date') # "2025-12-25"
        if not target_date: return jsonify({"error": "Falta fecha."}), 400
        
        # Llama a la lógica que acabamos de restaurar
        result = forecasting_service.analyze_specific_date_historically(file, target_date)
        return jsonify(result)
    except Exception as e: return jsonify({"error": str(e)}), 500

@bp.route('/forecast/specific-date-curve', methods=['POST'])
def get_specific_date_curve():
    """Obtiene la curva exacta de un día pasado"""
    try:
        file = request.files['historical_data']
        specific_date = request.form.get('specific_date')
        result = forecasting_service.analyze_specific_date_curve(file, specific_date)
        return jsonify(result)
    except Exception as e: return jsonify({"error": str(e)}), 500

@bp.route('/build_weighted_curve', methods=['POST'])
def build_weighted_curve():
    try:
        d = request.json
        return jsonify(forecasting_service.build_weighted_curve(
            d['weights'], d['day_of_week'], d['all_weekly_data'], d['labels']
        ))
    except Exception as e: return jsonify({"error": str(e)}), 500


# --- 3. GENERACIÓN Y GUARDADO (PLANTILLAS EXCEL) ---

@bp.route('/generate_forecast_template', methods=['POST'])
def generate_forecast_template():
    try:
        forecast_file = request.files['forecast_file']
        holidays_file = request.files.get('holidays_file')
        curves_data = json.loads(request.form['curves_data'])

        # 1. Distribuir Volumen (Servicio)
        rows, labels = forecasting_service.distribute_intraday_volume(forecast_file, holidays_file, curves_data)
        
        # 2. Transformar a 30 min (Servicio)
        final_rows, final_labels = forecasting_service.transform_hourly_to_half_hourly(rows, labels)

        if not final_rows: return jsonify({"error": "No se generaron datos."}), 400

        # Generar Excel
        df = pd.DataFrame(final_rows)
        # Reordenar columnas estéticas
        cols = ['Fecha', 'Dia', 'Semana', 'Tipo'] + [c for c in final_labels if c in df.columns]
        df = df[cols]

        output = io.BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter', datetime_format='dd/mm/yyyy')
        df.to_excel(writer, index=False, sheet_name='Volumen_a_gestionar')
        for s in ['AHT_esperado', 'Absentismo_esperado', 'Auxiliares_esperados']:
            pd.DataFrame(columns=df.columns).to_excel(writer, index=False, sheet_name=s)
        writer.close(); output.seek(0)
        
        return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name='Plantilla_Pronostico.xlsx')
    except Exception as e: return jsonify({"error": str(e)}), 500

@bp.route('/save_forecast_to_db', methods=['POST'])
def save_forecast_to_db():
    try:
        segment_id = request.form.get('segment_id')
        forecast_file = request.files['forecast_file']
        holidays_file = request.files.get('holidays_file')
        curves_data = json.loads(request.form['curves_data'])

        rows, labels = forecasting_service.distribute_intraday_volume(forecast_file, holidays_file, curves_data)
        final_rows, final_labels = forecasting_service.transform_hourly_to_half_hourly(rows, labels)

        if not final_rows: return jsonify({"error": "Sin datos."}), 400
        
        df = pd.DataFrame(final_rows)
        StaffingResult.query.filter(
            StaffingResult.segment_id == segment_id,
            StaffingResult.result_date.between(df['Fecha'].min().date(), df['Fecha'].max().date())
        ).delete(synchronize_session=False)

        new_entries = []
        for _, row in df.iterrows():
            calls = row.to_dict()
            if 'Fecha' in calls: calls['Fecha'] = calls['Fecha'].strftime('%Y-%m-%d %H:%M:%S')
            new_entries.append(StaffingResult(
                result_date=row['Fecha'].date(), segment_id=segment_id,
                calls_forecast=json.dumps(calls), 
                agents_online=json.dumps({c:0 for c in final_labels}),
                agents_total=json.dumps({c:0 for c in final_labels}), 
                aht_forecast=json.dumps({c:0 for c in final_labels}),
                reducers_forecast=json.dumps({})
            ))
        db.session.bulk_save_objects(new_entries); db.session.commit()
        return jsonify({"message": "Pronóstico guardado."})
    except Exception as e: return jsonify({"error": str(e)}), 500


# --- 4. FORECASTING MENSUAL (LARGO PLAZO) ---

@bp.route('/calculate_monthly_forecast_v2', methods=['POST'])
def calculate_monthly_forecast_v2():
    try:
        return jsonify(forecasting_service.calculate_monthly_forecast(
            request.files['historical_data'], request.files['holidays_data'],
            float(request.form.get('recency_weight', 70))/100,
            json.loads(request.form.get('manual_overrides', '{}')),
            request.form.get('year_weights')
        ))
    except Exception as e: return jsonify({"error": str(e)}), 500

@bp.route('/save_monthly_forecast', methods=['POST'])
def save_monthly_forecast():
    try:
        data = request.json
        seg_id = data.get('segment_id')
        pivot = data.get('forecast_pivot')
        exist = MonthlyForecast.query.filter_by(segment_id=seg_id).first()
        if exist: exist.forecast_pivot_data = json.dumps(pivot)
        else: db.session.add(MonthlyForecast(segment_id=seg_id, forecast_pivot_data=json.dumps(pivot)))
        db.session.commit()
        return jsonify({"message": "Guardado."})
    except Exception as e: return jsonify({"error": str(e)}), 500

@bp.route('/get_monthly_forecast', methods=['POST'])
def get_monthly_forecast():
    try:
        f = MonthlyForecast.query.filter_by(segment_id=request.json.get('segment_id')).first()
        if not f: return jsonify({"message": "No hay datos."})
        pivot = json.loads(f.forecast_pivot_data)
        years = sorted([int(y) for y in pivot.keys()])
        return jsonify({'pivot': pivot, 'current_year': years[-2] if len(years)>1 else years[0], 'target_year': years[-1]})
    except Exception as e: return jsonify({"error": str(e)}), 500

@bp.route('/export_monthly_forecast', methods=['POST'])
def export_monthly_forecast():
    try:
        pivot = json.loads(request.form.get('forecast_data_json')).get('pivot', {})
        rows = []
        months = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        for y in sorted(pivot.keys(), key=int):
            row = {'Año': y}
            for i, m in enumerate(months): row[m] = float(pivot[y].get(str(i+1), 0))
            row['TOTAL'] = sum(float(pivot[y].get(str(i+1), 0)) for i in range(12))
            rows.append(row)
        
        output = io.BytesIO()
        pd.DataFrame(rows).to_excel(output, index=False)
        output.seek(0)
        return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name='Mensual.xlsx')
    except Exception as e: return jsonify({"error": str(e)}), 500


# --- 5. FORECASTING INTRA-MES (DISTRIBUCIÓN MENSUAL A DIARIA) ---

@bp.route('/distribute_intramonth_forecast', methods=['POST'])
def distribute_intramonth_forecast():
    try:
        segment_id = request.form.get('segment_id')
        source = request.form.get('source') # 'db' o 'upload'
        historical_file = request.files.get('historical_excel')
        holidays_file = request.files.get('holidays_excel')

        monthly_volume_df = None
        if source == 'db':
            year, month = int(request.form.get('year')), int(request.form.get('month'))
            forecast_db = MonthlyForecast.query.filter_by(segment_id=segment_id).first()
            if not forecast_db: return jsonify({"error": "No hay previsión guardada."}), 404
            
            vol = json.loads(forecast_db.forecast_pivot_data).get(str(year), {}).get(str(month))
            monthly_volume_df = pd.DataFrame([{'año': year, 'mes': month, 'volumen': vol}])
        else:
            monthly_volume_df = pd.read_excel(request.files.get('volume_excel'))
        
        # Llamada al Servicio
        result_df = forecasting_service.distribute_intramonth_forecast(
            monthly_volume_df, historical_file, holidays_file
        )
        return jsonify({"data": result_df.to_dict(orient='records')})

    except Exception as e: return jsonify({"error": str(e)}), 500

# ==============================================================================
# SECCIÓN: ADMINISTRACIÓN (RECUPERADO)
# ==============================================================================

@bp.route('/get_segment_details/<int:segment_id>')
def get_segment_details_admin(segment_id):
    if session.get('role') != 'admin': return jsonify({"error": "Acceso denegado"}), 403
    segment = Segment.query.get(segment_id)
    if segment:
        return jsonify({
            'id': segment.id, 'name': segment.name, 'campaign_id': segment.campaign_id,
            'service_type': segment.service_type, 'bo_sla_hours': segment.bo_sla_hours,
            'lunes_apertura': segment.lunes_apertura or '', 'lunes_cierre': segment.lunes_cierre or '',
            'martes_apertura': segment.martes_apertura or '', 'martes_cierre': segment.martes_cierre or '',
            'miercoles_apertura': segment.miercoles_apertura or '', 'miercoles_cierre': segment.miercoles_cierre or '',
            'jueves_apertura': segment.jueves_apertura or '', 'jueves_cierre': segment.jueves_cierre or '',
            'viernes_apertura': segment.viernes_apertura or '', 'viernes_cierre': segment.viernes_cierre or '',
            'sabado_apertura': segment.sabado_apertura or '', 'sabado_cierre': segment.sabado_cierre or '',
            'domingo_apertura': segment.domingo_apertura or '', 'domingo_cierre': segment.domingo_cierre or '',
            'weekend_policy': segment.weekend_policy, 'min_full_weekends_off_per_month': segment.min_full_weekends_off_per_month
        })
    return jsonify({'error': 'Segmento no encontrado'}), 404

@bp.route('/admin/update_password', methods=['POST'])
def admin_update_password():
    if session.get('role') != 'admin':
        return jsonify({"error": "Acceso denegado"}), 403
    try:
        data = request.json
        user_id = data.get('user_id')
        new_password = data.get('new_password')

        if not user_id or not new_password or len(new_password) < 8:
            return jsonify({"error": "La contraseña debe tener al menos 8 caracteres."}), 400

        user_to_update = User.query.get(user_id)
        if not user_to_update:
            return jsonify({"error": "Usuario no encontrado."}), 404
        
        user_to_update.password_hash = generate_password_hash(new_password, method='pbkdf2:sha256')
        db.session.commit()
        
        return jsonify({"message": f"Contraseña de '{user_to_update.username}' actualizada."})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error en el servidor: {str(e)}"}), 500
    
# En app/api_routes.py

@bp.route('/upload_agents', methods=['POST'])
def upload_agents():
    if 'agents_excel_file' not in request.files:
        return jsonify({"error": "No se encontró ningún archivo en la petición."}), 400

    file = request.files['agents_excel_file']
    if file.filename == '':
        return jsonify({"error": "No se seleccionó ningún archivo."}), 400

    try:
        df = pd.read_excel(file)
        df.columns = [str(col).strip().lower().replace(' ', '_').replace('.', '') for col in df.columns]

        col_id = next((c for c in df.columns if c in ['identificacion', 'dni', 'cedula', 'id_legal', 'id']), None)
        col_nombre = next((c for c in df.columns if c in ['nombre', 'nombre_completo', 'apellidos_y_nombre']), None)
        col_segmento = next((c for c in df.columns if c in ['segmento', 'servicio', 'campana']), None)
        
        if not col_id or not col_segmento:
            return jsonify({"error": "El archivo debe tener columnas 'Identificacion' y 'Segmento'."}), 400

        unique_segments_excel = df[col_segmento].dropna().unique()
        updated_count = 0
        created_count = 0
        deleted_count = 0
        
        # 1. Procesar Bajas primero (Delete)
        # Es seguro hacerlo antes de cualquier inserción
        for seg_name in unique_segments_excel:
            segment_db = Segment.query.filter(Segment.name.ilike(seg_name.strip())).first()
            if not segment_db: continue
            
            current_agents_db = Agent.query.filter_by(segment_id=segment_db.id).all()
            df_seg = df[df[col_segmento] == seg_name]
            excel_dnis = set(df_seg[col_id].astype(str).str.strip().str.replace('.0', '').str.upper())
            
            for agent in current_agents_db:
                if str(agent.identificacion).strip().upper() not in excel_dnis:
                    Schedule.query.filter_by(agent_id=agent.id).delete()
                    Absence.query.filter_by(agent_id=agent.id).delete()
                    db.session.delete(agent)
                    deleted_count += 1
        
        # Hacemos commit de los borrados para limpiar la sesión
        db.session.commit()

        # 2. Procesar Altas y Modificaciones
        for index, row in df.iterrows():
            seg_name = str(row[col_segmento]).strip()
            segment_db = Segment.query.filter(Segment.name.ilike(seg_name)).first()
            if not segment_db: continue

            dni_val = str(row[col_id]).strip().replace('.0', '').upper()
            nombre_val = str(row.get(col_nombre, '')).strip()
            contrato_val = str(row.get('contrato', '0')).strip()
            
            # Buscamos si ya existe (Query directa para evitar caché sucia)
            agent = Agent.query.filter_by(identificacion=dni_val).first()
            
            if agent:
                # --- ACTUALIZAR ---
                agent.nombre_completo = nombre_val
                agent.segment_id = segment_db.id # Asegurar que está en el segmento correcto
                
                if contrato_val and contrato_val != '0':
                    try:
                        hours = float(contrato_val.lower().replace('h',''))
                        # Usamos una query segura
                        rule = SchedulingRule.query.filter_by(weekly_hours=hours, country_code=segment_db.campaign.country).first()
                        if rule: agent.scheduling_rule = rule
                    except: pass
                
                # Actualizar otros campos si vienen
                if 'turno_sugerido' in row: agent.turno_sugerido = str(row['turno_sugerido']).strip()
                
                updated_count += 1
            else:
                # --- CREAR ---
                new_agent = Agent(
                    identificacion=dni_val,
                    nombre_completo=nombre_val if nombre_val else f"Agente {dni_val}",
                    segment_id=segment_db.id
                )
                
                # Regla por defecto o por contrato
                rule = None
                if contrato_val and contrato_val != '0':
                    try:
                        hours = float(contrato_val.lower().replace('h',''))
                        rule = SchedulingRule.query.filter_by(weekly_hours=hours, country_code=segment_db.campaign.country).first()
                    except: pass
                
                if not rule:
                    # Fallback a regla por defecto
                    rule = SchedulingRule.query.first()
                
                if rule:
                    new_agent.scheduling_rule = rule
                else:
                     # Si no hay reglas, esto fallará por el NOT NULL constraint.
                     # Creamos una regla dummy o lanzamos error controlado.
                     return jsonify({"error": f"No se encontraron reglas de contrato para el agente {dni_val}. Crea reglas primero."}), 400

                db.session.add(new_agent)
                created_count += 1

        db.session.commit()
        
        return jsonify({
            "message": f"Sincronización exitosa. Nuevos: {created_count}, Actualizados: {updated_count}, Bajas: {deleted_count}."
        })

    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Error al procesar: {str(e)}"}), 500
    else:
        return jsonify({"error": "Formato de archivo no válido. Por favor, sube un archivo .xlsx."}), 400
    
@bp.route('/update_schedule', methods=['POST'])
def update_schedule():
    try:
        from .services import scheduling_service
        data = request.json
        agent_id = data.get('agent_id')
        date_str = data.get('date')
        new_shift = data.get('shift')
        
        schedule_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        
        entry = Schedule.query.filter_by(agent_id=agent_id, schedule_date=schedule_date).first()
        
        if not entry:
            # Si era LIBRE y no existía en BD, lo creamos
            entry = Schedule(agent_id=agent_id, schedule_date=schedule_date)
            db.session.add(entry)
        
        entry.shift = new_shift
        entry.hours = scheduling_service.calculate_shift_duration_helper(new_shift)
        entry.is_manual_edit = True # IMPORTANTE: Marcar como manual para protegerlo
        
        db.session.commit()
        return jsonify({"message": "Actualizado"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@bp.route('/export_schedule', methods=['POST'])
def export_schedule():
    try:
        
        # 1. Recolectar datos
        data = request.json
        segment_id = data.get('segment_id')
        start_date = datetime.datetime.strptime(data.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.datetime.strptime(data.get('end_date'), '%Y-%m-%d').date()
        
        # --- NUEVO: Obtener filtro de DNIs ---
        filter_dnis_str = data.get('filter_dnis', '')

        segment = Segment.query.options(joinedload(Segment.campaign)).filter_by(id=segment_id).first()
        if not segment: return jsonify({"error": "Segmento no encontrado."}), 404
        
        campaign_code = segment.campaign.code if segment.campaign else ""
        
        # 2. Construir la consulta de Agentes
        query = Agent.query.filter_by(segment_id=segment_id)

        # --- LÓGICA DE FILTRADO POR DNI ---
        filename_suffix = "Completo"
        if filter_dnis_str and filter_dnis_str.strip():
            # Separar por comas, limpiar espacios y crear lista
            dni_list = [x.strip() for x in filter_dnis_str.split(',') if x.strip()]
            if dni_list:
                # Filtrar solo los agentes que coincidan
                query = query.filter(Agent.identificacion.in_(dni_list))
                filename_suffix = "Filtrado"

        agents = query.order_by(Agent.nombre_completo).all()
        
        if not agents: 
            return jsonify({"error": "No se encontraron agentes con los criterios seleccionados."}), 404

        agent_ids = [agent.id for agent in agents]
        schedules = Schedule.query.filter(
            Schedule.agent_id.in_(agent_ids),
            Schedule.schedule_date.between(start_date, end_date)
        ).all()
        
        schedule_map = {(s.agent_id, s.schedule_date): s for s in schedules}

        # Columnas requeridas por la plataforma WFM
        columns = [
            'Centro', 'Servicio', 'Id_Legal', 'Fecha_Entrada', 'Fecha_Salida', 
            'Hora_Entrada', 'Hora_Salida', 'Novedad', 
            'Formacion1_HE', 'Formacion1_HS', 'Formacion2_HE', 'Formacion2_HS', 
            'Descanso1_HE', 'Descanso1_HS', 'Descanso2_HE', 'Descanso2_HS', 
            'PVD1', 'PVD2', 'PVD3', 'PVD4', 'PVD5', 'PVD6', 'PVD7', 'PVD8', 'PVD9', 'PVD10', 
            'Observacion', 'susceptible_de_pago', 'Complementarias'
        ]
        
        export_data = []
        date_range = [start_date + datetime.timedelta(days=i) for i in range((end_date - start_date).days + 1)]
        EXPORTABLE_NOVEDADES = ['LIBRE', 'DLF'] 

        for agent in agents:
            for day in date_range:
                schedule_entry = schedule_map.get((agent.id, day))
                shift = 'LIBRE' 
                if schedule_entry:
                    shift = schedule_entry.shift

                # --- FILTRO DE EXPORTACIÓN ---
                is_work_shift = '-' in shift and shift not in VALID_AUSENCIA_CODES
                is_allowed_novedad = shift in EXPORTABLE_NOVEDADES
                
                if not is_work_shift and not is_allowed_novedad:
                    continue 

                # --- PREPARAR FILA BASE ---
                base_row = {col: '' for col in columns}
                base_row['Centro'] = agent.centro or ''
                base_row['Servicio'] = campaign_code
                base_row['Id_Legal'] = agent.identificacion
                base_row['Fecha_Entrada'] = day.strftime('%d/%m/%Y')
                base_row['Fecha_Salida'] = day.strftime('%d/%m/%Y')
                base_row['susceptible_de_pago'] = 'NO'
                base_row['Complementarias'] = 'NO'

                # CASO A: TURNO DE TRABAJO (Horas)
                if is_work_shift:
                    parts = shift.split('/')
                    for i, part in enumerate(parts):
                        if '-' not in part: continue
                        
                        part_row = base_row.copy()
                        start_str, end_str = part.strip().split('-')
                        part_row['Hora_Entrada'] = start_str
                        part_row['Hora_Salida'] = '23:59' if end_str.strip() == '24:00' else end_str

                        if i == 0 and schedule_entry:
                            part_row['Descanso1_HE'] = schedule_entry.descanso1_he or ''
                            part_row['Descanso1_HS'] = schedule_entry.descanso1_hs or ''
                            part_row['Descanso2_HE'] = schedule_entry.descanso2_he or ''
                            part_row['Descanso2_HS'] = schedule_entry.descanso2_hs or ''
                            for pvd_num in range(1, 11):
                                part_row[f'PVD{pvd_num}'] = getattr(schedule_entry, f'pvd{pvd_num}', '') or ''
                        
                        export_data.append(part_row)

                # CASO B: NOVEDAD (LIBRE, DLF)
                else:
                    row_with_novedad = base_row.copy()
                    row_with_novedad['Hora_Entrada'] = '00:00'
                    row_with_novedad['Hora_Salida'] = '23:59'
                    row_with_novedad['Novedad'] = shift
                    export_data.append(row_with_novedad)
        
        df = pd.DataFrame(export_data, columns=columns)
        df = df.fillna('')

        output = io.BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        df.to_excel(writer, index=False, sheet_name='Horarios')
        
        worksheet = writer.sheets['Horarios']
        for i, col in enumerate(df.columns):
            column_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.set_column(i, i, column_len)

        writer.close()
        output.seek(0)
        
        filename = f'Horarios_{campaign_code}_{start_date.strftime("%Y%m%d")}_{filename_suffix}.xlsx'
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Ocurrió un error al exportar: {str(e)}"}), 500


@bp.route('/calculator/calculate', methods=['POST'])
def calculate_staffing():
    try:
        # 1. Recibir Archivos y Datos
        file = request.files.get('staffing_template')
        if not file: return jsonify({"error": "Falta el archivo de plantilla."}), 400
        
        seg_id = request.form.get('segment_id')
        start = request.form.get('start_date')
        end = request.form.get('end_date')
        
        # --- NUEVO: GESTIÓN DE ESCENARIO ---
        scenario_id = request.form.get('scenario_id')
        
        # Si no viene escenario, buscamos/creamos el Oficial
        if not scenario_id or scenario_id == 'official':
            official = Scenario.query.filter_by(segment_id=seg_id, is_official=True).first()
            if not official:
                # Auto-crear oficial si es la primera vez
                official = Scenario(name="Oficial (Producción)", segment_id=seg_id, is_official=True)
                db.session.add(official)
                db.session.commit()
            scenario_id = official.id

        segment = Segment.query.get(seg_id)
        if not segment: return jsonify({"error": "Segmento no encontrado."}), 404
        
        # 2. Preparar Datos (Llamada al servicio)
        sheets = staffing_service.prepare_staffing_data_from_request(file, seg_id, start, end)
        if 'error' in sheets: return jsonify(sheets), 400
        
        # 3. Configuración de cálculo
        conf = {
            "service_type": segment.service_type,
            "sla_objetivo": float(request.form.get('sla_objetivo', 0.8)),
            "sla_tiempo": int(request.form.get('sla_tiempo', 20)),
            "intervalo_seg": 1800
        }
        
        # 4. Procesar Matemática (Erlang C / Lineal)
        # Esta función retorna 4 dataframes y 1 dict de KPIs
        dim, pres, log, efec, kpis = staffing_service.process_staffing_template(conf, sheets)
        
        if dim is None: return jsonify({"error": "Error en el cálculo. Verifica los datos del Excel."}), 400
        
        # 5. Guardar en BD (CONEXIÓN CRÍTICA CON SCHEDULING)
        # --- CAMBIO: Pasamos el scenario_id para guardar en la partición correcta ---
        # Nota: Debes actualizar la firma de 'save_staffing_results' en staffing_service.py
        staffing_service.save_staffing_results(seg_id, conf, sheets, dim, efec, scenario_id=scenario_id)
        
        # 6. Formatear respuesta para el Frontend
        res = {
            "dimensionados": _format_and_calculate_simple(dim).to_dict(orient='split'),
            "presentes": _format_and_calculate_simple(pres).to_dict(orient='split'),
            "logados": _format_and_calculate_simple(log).to_dict(orient='split'),
            "efectivos": _format_and_calculate_simple(efec).to_dict(orient='split'),
            "kpis": kpis,
            "scenario_id": scenario_id # Devolvemos el ID para confirmación
        }
        
        # Limpieza de índice pandas para JSON
        for k in res: 
            if isinstance(res[k], dict) and 'index' in res[k]: del res[k]['index']
            
        return jsonify(res)
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Error interno: {str(e)}"}), 500
    
@bp.route('/import_schedules', methods=['POST'])
def import_schedules():
    try:
        # 1. Recolectar datos
        segment_id = request.form.get('segment_id')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        file = request.files.get('schedules_excel')

        if not all([segment_id, start_date_str, end_date_str, file]):
            return jsonify({"error": "Faltan datos (segmento, rango de fechas o archivo)."}), 400

        start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()

        # 2. Mapear Agentes (DNI -> ID)
        agents_in_segment = Agent.query.filter_by(segment_id=segment_id).all()
        if not agents_in_segment:
            return jsonify({"error": "No hay agentes en este segmento."}), 400
            
        agent_map = {
            str(a.identificacion).strip().upper().replace('.0', ''): a 
            for a in agents_in_segment
        }

        # 3. Leer Excel y Normalizar Columnas
        df = pd.read_excel(file)
        df.columns = [str(col).strip().upper().replace(' ', '_') for col in df.columns]

        col_dni = next((c for c in df.columns if c in ['ID_LEGAL', 'DNI', 'CEDULA']), None)
        col_fecha = next((c for c in df.columns if c in ['FECHA_ENTRADA', 'FECHA']), None)
        
        if not col_dni or not col_fecha:
            return jsonify({"error": "El archivo debe tener columnas 'Id_Legal' y 'Fecha_Entrada'."}), 400

        # 4. Procesar filas del Excel
        schedules_to_process = defaultdict(lambda: {'shifts': [], 'novedad': None, 'extras': {}})
        agents_in_file_ids = set()

        for index, row in df.iterrows():
            raw_dni = str(row[col_dni]).strip().upper().replace('.0', '')
            agent = agent_map.get(raw_dni)
            if not agent: continue 
            
            try:
                # dayfirst=True es importante para fechas tipo 01/02/2025
                sched_date = pd.to_datetime(row[col_fecha], dayfirst=True).date()
            except: continue
            
            if not (start_date <= sched_date <= end_date): continue
            
            agents_in_file_ids.add(agent.id)
            key = (agent.id, sched_date)
            
            novedad = str(row.get('NOVEDAD', '')).strip().upper()
            h_ent = str(row.get('HORA_ENTRADA', '')).strip()
            h_sal = str(row.get('HORA_SALIDA', '')).strip()
            
            # Prioridad: Si dice "LIBRE" o tiene Novedad, es eso. Si tiene horas, es turno.
            if novedad and novedad not in ['NAN', '0', '', 'None']:
                schedules_to_process[key]['novedad'] = novedad
            elif h_ent and h_sal and h_ent not in ['NAN', '0', ''] and ':' in h_ent:
                tramo = f"{h_ent}-{h_sal}"
                schedules_to_process[key]['shifts'].append(tramo)

            # Guardar Descansos/PVDs (toma la primera ocurrencia del día)
            if not schedules_to_process[key]['extras']:
                schedules_to_process[key]['extras'] = {
                    'descanso1_he': str(row.get('DESCANSO1_HE', '')).strip() or None,
                    'descanso1_hs': str(row.get('DESCANSO1_HS', '')).strip() or None,
                    'descanso2_he': str(row.get('DESCANSO2_HE', '')).strip() or None,
                    'descanso2_hs': str(row.get('DESCANSO2_HS', '')).strip() or None
                }
                for i in range(1, 11):
                    pvd_val = str(row.get(f'PVD{i}', '')).strip()
                    if pvd_val and pvd_val not in ['NAN', '0']:
                        schedules_to_process[key]['extras'][f'pvd{i}'] = pvd_val

        if not agents_in_file_ids:
            return jsonify({"error": "Ningún agente del archivo coincide con el segmento."}), 400

        # 5. PROTECCIÓN DE ABSENTISMOS (La parte más importante)
        # Buscamos en BD qué días ya tienen ausencias 'oficiales' (VAC, BMED, etc.)
        existing_absences = Schedule.query.filter(
            Schedule.agent_id.in_(agents_in_file_ids),
            Schedule.schedule_date.between(start_date, end_date),
            Schedule.shift.in_(VALID_AUSENCIA_CODES) 
        ).all()
        
        # Creamos un conjunto de días bloqueados: (id_agente, fecha)
        locked_dates = {(s.agent_id, s.schedule_date) for s in existing_absences}

        # 6. LIMPIEZA DE TURNOS ANTERIORES
        # Borramos TODO lo que NO sea una ausencia protegida
        # (El símbolo ~ significa NOT en SQLAlchemy filters)
        Schedule.query.filter(
            Schedule.agent_id.in_(agents_in_file_ids),
            Schedule.schedule_date.between(start_date, end_date),
            ~Schedule.shift.in_(VALID_AUSENCIA_CODES) 
        ).delete(synchronize_session=False)

        # 7. INSERTAR NUEVOS DATOS
        new_entries = []
        
        for (agent_id, s_date), data in schedules_to_process.items():
            # SI LA FECHA ESTÁ BLOQUEADA POR ABSENTISMO EN BD, NO HACEMOS NADA
            if (agent_id, s_date) in locked_dates:
                continue 

            final_shift = 'LIBRE'
            if data['novedad']:
                final_shift = data['novedad']
            elif data['shifts']:
                try:
                    # Ordenar tramos por hora inicio
                    data['shifts'].sort(key=lambda x: x.split('-')[0])
                    final_shift = "/".join(data['shifts'])
                except:
                    final_shift = data['shifts'][0]

            hours = scheduling_service.calculate_shift_duration_helper(final_shift)
            
            entry = Schedule(
                agent_id=agent_id,
                schedule_date=s_date,
                shift=final_shift,
                hours=hours,
                is_manual_edit=True, # Marcamos como manual porque viene de carga externa
                **data['extras']
            )
            new_entries.append(entry)
        
        if new_entries:
            db.session.bulk_save_objects(new_entries)
        
        db.session.commit()

        return jsonify({
            "message": f"Carga exitosa. Se actualizaron horarios para {len(agents_in_file_ids)} agentes. Se respetaron {len(locked_dates)} días con absentismo oficial."
        })

    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({"error": f"Error al importar: {str(e)}"}), 500
    
@bp.route('/recalculate_day_metrics', methods=['POST'])
def recalculate_day_metrics():
    try:
        data = request.json
        segment_id = data.get('segment_id')
        coverage = data.get('coverage') # Esto es "Asesor Dimensionado" (Total Plantilla en turno)
        calls = data.get('calls')
        aht = data.get('aht')
        
        # Estos targets vienen del frontend, que los sacó del StaffingResult
        sla_target = data.get('sla_target', 0.8) 
        sla_time = data.get('sla_time', 20)
        
        target_date_str = data.get('date_str')
        
        segment = Segment.query.get(segment_id)
        is_inbound = segment.service_type == 'INBOUND'
        interval_seconds = 1800
        
        shrinkage_arr = [0] * 48
        aux_arr = [0] * 48
        abs_arr = [0] * 48
        
        # Buscar los reductores específicos de ese día
        if target_date_str:
            t_date = datetime.datetime.strptime(target_date_str, '%Y-%m-%d').date()
            forecast_db = StaffingResult.query.filter_by(segment_id=segment_id, result_date=t_date).first()
            if forecast_db:
                # Si el día tiene un SLA específico guardado, úsalo (por si cambia día a día)
                if forecast_db.sla_target_percentage is not None:
                    sla_target = forecast_db.sla_target_percentage

                if forecast_db.reducers_forecast:
                    reducers = json.loads(forecast_db.reducers_forecast)
                    time_keys = sorted([k for k in json.loads(forecast_db.agents_online).keys() if ':' in str(k)])
                    shrinkage_arr = [float(reducers.get('shrinkage', {}).get(t, 0) or 0) for t in time_keys]
                    aux_arr = [float(reducers.get('auxiliaries', {}).get(t, 0) or 0) for t in time_keys]
                    abs_arr = [float(reducers.get('absenteeism', {}).get(t, 0) or 0) for t in time_keys]

        total_calls = sum(calls)
        total_handled = 0
        total_answered_sla = 0
        weighted_aht_sum = 0

        for i in range(len(coverage)):
            # 1. Dimensionados (Total Plantilla)
            dimensionados = coverage[i] 
            
            # Obtener % reductores del intervalo
            p_abs = abs_arr[i] if i < len(abs_arr) else 0
            p_shr = shrinkage_arr[i] if i < len(shrinkage_arr) else 0
            p_aux = aux_arr[i] if i < len(aux_arr) else 0
            
            # 2. Cadena de Resta EXACTA
            presentes = dimensionados * (1 - p_abs)
            logados = presentes * (1 - p_shr)
            efectivos = logados * (1 - p_aux)
            
            net_agents = efectivos # Este es el valor final para Erlang

            vol = calls[i]
            t_aht = aht[i]
            
            if vol > 0:
                weighted_aht_sum += (vol * t_aht)
                
                if t_aht > 0 and net_agents > 0.1:
                    capacity_val = 0
                    if is_inbound:
                        capacity_val = staffing_service._calculate_sl_capacity(
                            net_agents, t_aht, sla_target, sla_time, interval_seconds
                        )
                    else:
                        effective_hours = net_agents * 0.5
                        capacity_val = (effective_hours * 3600 / t_aht)
                    
                    handled = min(capacity_val, vol)
                    
                    if is_inbound:
                        attainable_sla = capacity_val * sla_target
                        attended_sla = min(vol, attainable_sla)
                        total_answered_sla += attended_sla
                    
                    total_handled += handled

        ns_final = (total_answered_sla / total_calls * 100) if total_calls > 0 else 100.0
        nda_final = (total_handled / total_calls * 100) if total_calls > 0 else 100.0

        return jsonify({
            "ns": round(ns_final, 1),
            "nda": round(nda_final, 1),
            "raw_calls": total_calls,
            "raw_sla": total_answered_sla,
            "raw_handled": total_handled,
            "raw_aht_vol": weighted_aht_sum,
            "sla_target_used": sla_target # Devolvemos el target real usado para pintar
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    
# ==============================================================================
# MÓDULO DE GESTIÓN DE CAMBIOS (TL <-> ANALISTA)
# ==============================================================================

@bp.route('/tl/search_agent', methods=['POST'])
def tl_search_agent():
    try:
        query = request.json.get('query', '').strip()
        if len(query) < 3: return jsonify({"error": "Mínimo 3 caracteres"}), 400
        
        agents = Agent.query.filter(
            or_(Agent.nombre_completo.ilike(f"%{query}%"), Agent.identificacion.ilike(f"%{query}%"))
        ).limit(10).all()
        
        return jsonify([{
            "id": a.id, "nombre": a.nombre_completo, 
            "dni": a.identificacion, "segmento": a.segment.name
        } for a in agents])
    except Exception as e: return jsonify({"error": str(e)}), 500

@bp.route('/tl/create_request', methods=['POST'])
def tl_create_request():
    try:
        d = request.json
        date_obj = datetime.datetime.strptime(d['date'], '%Y-%m-%d').date()
        
        # Obtener turno actual para referencia
        curr = Schedule.query.filter_by(agent_id=d['agent_id'], schedule_date=date_obj).first()
        curr_shift = curr.shift if curr else "LIBRE"
        
        req = ShiftChangeRequest(
            agent_id=d['agent_id'], requester_id=session['user_id'],
            request_date=date_obj, current_shift=curr_shift,
            requested_shift=d['new_shift'], reason_type=d['reason'],
            comment=d.get('comment'), status='PENDING'
        )
        db.session.add(req)
        db.session.commit()
        return jsonify({"message": "Solicitud enviada correctamente."})
    except Exception as e: return jsonify({"error": str(e)}), 500

@bp.route('/analyst/manage_request', methods=['POST'])
def analyst_manage_request():
    if session.get('role') not in ['admin', 'analista']: return jsonify({"error": "No autorizado"}), 403
    try:
        d = request.json
        req = ShiftChangeRequest.query.get(d['request_id'])
        if not req or req.status != 'PENDING': return jsonify({"error": "Invalido"}), 404
        
        action = d['action']
        req.status = 'APPROVED' if action == 'APPROVE' else 'REJECTED'
        req.processed_at = datetime.datetime.utcnow()
        req.processed_by = session['user_id']
        
        if action == 'APPROVE':
            # APLICAR CAMBIO EN SCHEDULE REAL
            sched = Schedule.query.filter_by(agent_id=req.agent_id, schedule_date=req.request_date).first()
            hours = scheduling_service.calculate_shift_duration_helper(req.requested_shift)
            
            if sched:
                sched.shift = req.requested_shift
                sched.hours = hours
                sched.is_manual_edit = True # Importante para que el sistema aprenda
            else:
                db.session.add(Schedule(
                    agent_id=req.agent_id, schedule_date=req.request_date,
                    shift=req.requested_shift, hours=hours, is_manual_edit=True
                ))
        
        db.session.commit()
        return jsonify({"message": "Procesado."})
    except Exception as e: 
        db.session.rollback()
        return jsonify({"error": str(e)}), 



# ==============================================================================
# GESTIÓN DE ESCENARIOS (ACTUALIZADO CON FECHAS)
# ==============================================================================

@bp.route('/scenarios/list/<int:segment_id>', methods=['GET'])
def list_scenarios(segment_id):
    try:
        # Filtros de fecha opcionales
        start_str = request.args.get('start_date')
        end_str = request.args.get('end_date')
        
        from .services.scenario_service import get_or_create_official_scenario
        # Asegurar oficial (El oficial siempre sale, sin importar fecha)
        get_or_create_official_scenario(segment_id)
        
        query = Scenario.query.filter_by(segment_id=segment_id)
        
        # Lógica de filtrado:
        # 1. Siempre traer el Oficial.
        # 2. Traer escenarios que se solapen con el rango seleccionado.
        if start_str and end_str:
            start = datetime.datetime.strptime(start_str, '%Y-%m-%d').date()
            end = datetime.datetime.strptime(end_str, '%Y-%m-%d').date()
            
            # Condición: (Oficial) O (Escenario dentro del rango)
            # Un escenario es relevante si su rango toca el rango seleccionado
            query = query.filter(
                or_(
                    Scenario.is_official == True,
                    and_(Scenario.start_date <= end, Scenario.end_date >= start)
                )
            )
        
        scens = query.order_by(Scenario.is_official.desc(), Scenario.created_at.desc()).all()
        
        return jsonify([{
            'id': s.id, 
            'name': s.name, 
            'is_official': s.is_official,
            'dates': f"({s.start_date} - {s.end_date})" if s.start_date else ""
        } for s in scens])

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/scenarios/create', methods=['POST'])
def create_scenario_route():
    try:
        from .services.scenario_service import create_simulation_scenario
        data = request.json
        
        # Validar fechas
        start = datetime.datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        end = datetime.datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        
        # Buscar oficial base para clonar datos iniciales
        official = Scenario.query.filter_by(segment_id=data['segment_id'], is_official=True).first()
        if not official: 
            # Crear oficial si no existe
            from .services.scenario_service import get_or_create_official_scenario
            official = get_or_create_official_scenario(data['segment_id'])
        
        # Crear simulación con fechas
        new_scen = create_simulation_scenario(
            data['segment_id'], 
            data['name'], 
            base_scenario_id=official.id,
            start_date=start,  # Pasar fechas al servicio
            end_date=end
        )
        # Actualizar fechas en el objeto escenario (si el servicio no lo hizo)
        new_scen.start_date = start
        new_scen.end_date = end
        db.session.commit()
        
        return jsonify({'id': new_scen.id, 'name': new_scen.name})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@bp.route('/scenarios/add_simulated_agents', methods=['POST'])
def add_simulated_agents():
    try:
        data = request.json
        scenario_id = data.get('scenario_id')
        count = int(data.get('count', 0))
        shift_type = data.get('shift_type', '09:00-18:00')
        start_date = datetime.datetime.strptime(data.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.datetime.strptime(data.get('end_date'), '%Y-%m-%d').date()

        if not scenario_id: 
            return jsonify({"error": "Falta el ID del escenario."}), 400

        scenario = Scenario.query.get(scenario_id)
        if not scenario:
            return jsonify({"error": "Escenario no encontrado."}), 404

        # 1. Buscar regla por defecto
        default_rule = SchedulingRule.query.first()
        if not default_rule:
            return jsonify({"error": "No hay reglas de contrato definidas."}), 400

        new_agents = []
        
        # 2. Crear los Agentes (Fantasmas)
        for i in range(count):
            fake_identificacion = f"SIM-{scenario_id}-{random.randint(10000, 99999)}"
            
            agent = Agent(
                identificacion=fake_identificacion,
                nombre_completo=f"Simulado {i+1} ({shift_type})",
                segment_id=scenario.segment_id,
                # scenario_id=scenario.id,  <-- OJO: Verifica si tu modelo Agent tiene scenario_id. Si es global, quita esta línea.
                is_simulated=True,
                
                
                
                scheduling_rule_id=default_rule.id
            )
            # Si tu modelo tiene scenario_id, descomenta la línea de arriba.
            # Si los agentes simulados son específicos por escenario, asegúrate de tener ese campo en el modelo Agent.
            
            db.session.add(agent)
            new_agents.append(agent)
        
        db.session.commit()

        # 3. Asignar turnos (Con verificación de duplicados)
        hours = scheduling_service.calculate_shift_duration_helper(shift_type)
        
        curr = start_date
        while curr <= end_date:
            for ag in new_agents:
                # PROTECCIÓN CONTRA DUPLICADOS
                exists = Schedule.query.filter_by(
                    agent_id=ag.id, 
                    schedule_date=curr, 
                    scenario_id=scenario.id
                ).first()

                if not exists:
                    new_sch = Schedule(
                        agent_id=ag.id,
                        schedule_date=curr,
                        shift=shift_type,
                        hours=hours,
                        is_manual_edit=True,
                        scenario_id=scenario.id
                    )
                    db.session.add(new_sch)
            
            curr += datetime.timedelta(days=1)
            
        db.session.commit()
        
        return jsonify({"message": f"{count} agentes simulados agregados correctamente."})

    except Exception as e:
        db.session.rollback()
        # traceback.print_exc() # Asegúrate de importar traceback si usas esto
        print(f"ERROR: {str(e)}") # Imprimir error en consola para depurar
        return jsonify({"error": f"Error al agregar simulados: {str(e)}"}), 500