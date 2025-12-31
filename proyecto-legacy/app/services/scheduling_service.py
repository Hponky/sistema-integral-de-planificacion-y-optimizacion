# app/services/scheduling_service.py

import datetime
import json
import math
import traceback
from collections import defaultdict

import numpy as np
import pandas as pd
from ortools.sat.python import cp_model
from sqlalchemy.orm import joinedload
from sqlalchemy import or_, func

# Importamos Scenario para poder buscar el oficial por defecto
from ..models import Agent, Schedule, StaffingResult, SchedulingRule, Scenario
from ..constants import VALID_AUSENCIA_CODES
from .. import db 

# --- FUNCIONES DE LOGGING ---
def log_section(title):
    print("\n" + "="*80)
    print(f"=== {title.upper()} ===")
    print("="*80)

def log_item(key, value):
    print(f"  > {key}: {value}")

class Scheduler:
    DAY_MAP = {0: "lunes", 1: "martes", 2: "miercoles", 3: "jueves", 4: "viernes", 5: "sabado", 6: "domingo"}

    def __init__(self, agents, segment, needs_by_day, time_labels_list, start_date, end_date, existing_schedule_map={}):
        self.agents = agents
        self.segment = segment
        self.needs_by_day = needs_by_day
        self.time_labels_list = time_labels_list
        self.time_labels_map = {label: i for i, label in enumerate(time_labels_list)}
        self.num_intervals = len(time_labels_list)
        self.existing_schedule_map = existing_schedule_map
        
        self.start_date = start_date
        self.end_date = end_date
        self.all_days = []
        
        curr = self.start_date
        while curr <= self.end_date:
            self.all_days.append(curr)
            curr += datetime.timedelta(days=1)
            
        self.weeks_data = self._group_days_by_week()
        
        self.shift_map = {
            0: {'id': 0, 'name': 'LIBRE', 'hours': 0, 'coverage': [0] * self.num_intervals},
            -1: {'id': -1, 'name': 'AUSENCIA', 'hours': 0, 'coverage': [0] * self.num_intervals}
        }
        self.next_shift_id = 1
        
        # --- MÓDULO DE APRENDIZAJE ---
        # Analiza el pasado para entender preferencias manuales
        self.agent_preferences = self._learn_from_history()

    def _group_days_by_week(self):
        weeks = defaultdict(list)
        for day in self.all_days:
            weeks[day.isocalendar()[1]].append(day)
        return weeks
    
    def _learn_from_history(self):
        """
        Consulta la base de datos para ver qué turnos se han asignado manualmente (is_manual_edit=True)
        a estos agentes en los últimos 90 días.
        """
        log_section("Fase de Aprendizaje (Memoria Histórica)")
        history_start = self.start_date - datetime.timedelta(days=90)
        
        # Consultar ediciones manuales frecuentes agrupadas por (Agente, DíaSemana, Turno)
        # SQLite: strftime('%w') devuelve 0=Domingo...6=Sábado
        manual_edits = db.session.query(
            Schedule.agent_id,
            func.strftime('%w', Schedule.schedule_date).label('weekday_str'),
            Schedule.shift,
            func.count(Schedule.id)
        ).filter(
            Schedule.agent_id.in_([a.id for a in self.agents]),
            Schedule.schedule_date >= history_start,
            Schedule.is_manual_edit == True,
            Schedule.shift != 'LIBRE',
            ~Schedule.shift.in_(VALID_AUSENCIA_CODES)
        ).group_by(
            Schedule.agent_id,
            'weekday_str',
            Schedule.shift
        ).all()
        
        # Mapeo SQLite a Python (0=Mon...6=Sun)
        sqlite_to_python = {'0': 6, '1': 0, '2': 1, '3': 2, '4': 3, '5': 4, '6': 5}
        
        preferences = defaultdict(lambda: defaultdict(int))
        count_learned = 0
        
        for agent_id, w_str, shift, count in manual_edits:
            py_weekday = sqlite_to_python.get(w_str)
            # El peso aumenta cuantas más veces hayas puesto ese turno manualmente
            preferences[agent_id][py_weekday] = {shift: count * 50} 
            count_learned += 1
            
        log_item("Patrones aprendidos", f"{count_learned} preferencias detectadas")
        return preferences

    def run(self):
        log_section("INICIANDO OPTIMIZACIÓN")
        model = cp_model.CpModel()

        # 1. Variables
        self.works_on_day, self.shift_vars = self._create_core_variables(model)
        
        # 2. Restricciones Duras
        self._add_weekend_constraints(model)
        
        # 3. Objetivo
        self.expressions = self._add_objective_function(model)
        
        # 4. Solver
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 300.0
        solver.parameters.linearization_level = 0
        
        log_item("Resolviendo...", f"{len(self.agents)} agentes")
        status = solver.Solve(model)
        log_item("Estado", solver.StatusName(status))

        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            return self._process_solver_solution(solver)
        else:
            return {"error": "Infactible. Revisa restricciones."}, {}

    def _create_core_variables(self, model):
        works_on_day = {}
        shift_vars = {}
        
        for agent in self.agents:
            rule = agent.scheduling_rule
            if not rule: continue

            for day in self.all_days:
                # Verificar bloqueo (Absentismo o Manual EXISTENTE en este escenario)
                existing_entry = self.existing_schedule_map.get((agent.id, day))
                
                if existing_entry:
                    works_on_day[(agent.id, day)] = model.NewConstant(0)
                    continue
                
                valid_shift_ids = self._generate_valid_shifts_for_day(agent, rule, day)
                
                if not valid_shift_ids:
                    works_on_day[(agent.id, day)] = model.NewConstant(0)
                    continue
                
                works_on_day[(agent.id, day)] = model.NewBoolVar(f'w_{agent.id}_{day}')
                
                day_shift_vars = []
                for s_id in valid_shift_ids:
                    s_var = model.NewBoolVar(f's_{agent.id}_{day}_{s_id}')
                    shift_vars[(agent.id, day, s_id)] = s_var
                    day_shift_vars.append(s_var)
                
                model.Add(sum(day_shift_vars) == works_on_day[(agent.id, day)])
                
        return works_on_day, shift_vars

    def _generate_valid_shifts_for_day(self, agent, rule, day):
        day_name = self.DAY_MAP[day.weekday()]
        agent_window = getattr(agent, f"ventana_{day_name}", "LIBRE").strip().upper()
        
        if not agent_window or agent_window in ['LIBRE', '-']: return []
        
        possible_shifts = []

        # A. Turno Fijo / Partido
        if '/' in agent_window:
            try:
                total_hours = 0
                temp_coverage = [0] * self.num_intervals
                for part in agent_window.split('/'):
                    start_str, end_str = [s.strip() for s in part.split('-')]
                    start_idx = self.time_labels_map.get(start_str)
                    end_idx = self.num_intervals if end_str == '24:00' else self.time_labels_map.get(end_str)
                    
                    if start_idx is None or end_idx is None: raise KeyError
                    total_hours += (end_idx - start_idx) / 2.0
                    for i in range(start_idx, end_idx): temp_coverage[i] = 1
                
                if rule.min_daily_hours <= total_hours <= rule.max_daily_hours:
                    shift_id = self._get_or_create_shift_from_coverage(agent_window, temp_coverage)
                    if shift_id: return [shift_id]
                return []
            except: return []

        # B. Ventana Flotante
        try: 
            target_hours = rule.weekly_hours / rule.days_per_week if rule.days_per_week > 0 else rule.max_daily_hours
        except: target_hours = rule.max_daily_hours
        
        hour_steps = [target_hours, target_hours + 0.5, target_hours - 0.5]
        valid_hours = sorted([h for h in set(hour_steps) if rule.min_daily_hours <= h <= rule.max_daily_hours], reverse=True)
        if not valid_hours: valid_hours = [target_hours]

        for hours in valid_hours:
            if hours <= 0: continue
            num_intervals = int(hours * 2)
            try:
                start_win_str, end_win_str = [s.strip() for s in agent_window.split('-')]
                start_win_idx = self.time_labels_map.get(start_win_str)
                end_win_idx = self.num_intervals if end_win_str == '24:00' else self.time_labels_map.get(end_win_str)
                
                if start_win_idx is None or end_win_idx is None: continue
                
                for start_idx in range(start_win_idx, end_win_idx - num_intervals + 1):
                    end_idx = start_idx + num_intervals
                    shift_id = self._get_or_create_shift_id(start_idx, end_idx)
                    if shift_id: possible_shifts.append(shift_id)
            except: continue
            
        return list(set(possible_shifts))

    def _get_or_create_shift_id(self, start_idx, end_idx):
        if start_idx >= end_idx or end_idx > len(self.time_labels_list): return None
        hours_float = (end_idx - start_idx) / 2.0
        hours_int = int(hours_float * 10)
        end_label = '24:00' if end_idx == len(self.time_labels_list) else self.time_labels_list[end_idx]
        shift_name = f"{self.time_labels_list[start_idx]}-{end_label}"
        
        for s_id, s_data in self.shift_map.items():
            if s_id > 0 and s_data['name'] == shift_name: return s_id
            
        new_id = self.next_shift_id
        coverage = [0] * self.num_intervals
        for i in range(start_idx, end_idx): coverage[i] = 1
        self.shift_map[new_id] = {'id': new_id, 'name': shift_name, 'hours': hours_int, 'coverage': coverage}
        self.next_shift_id += 1
        return new_id

    def _get_or_create_shift_from_coverage(self, shift_name, coverage_array):
        for s_id, s_data in self.shift_map.items():
            if s_id > 0 and s_data['name'] == shift_name: return s_id
        hours_float = sum(coverage_array) / 2.0
        hours_int = int(hours_float * 10)
        new_id = self.next_shift_id
        self.shift_map[new_id] = {'id': new_id, 'name': shift_name, 'hours': hours_int, 'coverage': coverage_array}
        self.next_shift_id += 1
        return new_id

    def _add_weekend_constraints(self, model):
        for agent in self.agents:
            if not agent.scheduling_rule: continue
            weekends_off_vars = []
            for week_num, week_days in self.weeks_data.items():
                sat = next((d for d in week_days if d.weekday() == 5), None)
                sun = next((d for d in week_days if d.weekday() == 6), None)
                if not sat or not sun: continue

                work_sat = self.works_on_day.get((agent.id, sat))
                work_sun = self.works_on_day.get((agent.id, sun))
                
                if work_sat is None and work_sun is None: 
                    weekends_off_vars.append(1)
                    continue
                
                if work_sat is None: work_sat = 0
                if work_sun is None: work_sun = 0

                is_off = model.NewBoolVar(f'woff_{agent.id}_{week_num}')
                model.Add(work_sat + work_sun == 0).OnlyEnforceIf(is_off)
                model.Add(work_sat + work_sun > 0).OnlyEnforceIf(is_off.Not())
                weekends_off_vars.append(is_off)
            
            if weekends_off_vars:
                min_weekends = getattr(agent.scheduling_rule, 'min_full_weekends_off_per_month', 2)
                model.Add(sum(weekends_off_vars) >= min_weekends)

    def _add_objective_function(self, model):
        total_penalties = []
        expressions = {'weekly_hours': defaultdict(dict), 'weekly_days': defaultdict(dict)}
        
        # 1. Cobertura (Prioridad Máxima)
        for day in self.all_days:
            needs = self.needs_by_day.get(day, [0]*self.num_intervals)
            for i in range(self.num_intervals):
                coverage = sum(self.shift_vars.get((a.id, day, s), 0) * self.shift_map[s]['coverage'][i] 
                               for a in self.agents for s in range(1, self.next_shift_id) 
                               if (a.id, day, s) in self.shift_vars)
                shortage = model.NewIntVar(0, 1000, f'short_{day}_{i}')
                model.Add(shortage >= needs[i] - coverage)
                total_penalties.append(shortage * 100000)

        # 2. Contratos + APRENDIZAJE
        for agent in self.agents:
            rule = agent.scheduling_rule
            if not rule: continue
            
            for week, days in self.weeks_data.items():
                schedulable = sum(1 for d in days if (agent.id, d) in self.works_on_day)
                if schedulable == 0: continue
                
                target_days = min(rule.days_per_week, schedulable)
                target_hours = int((rule.weekly_hours * (target_days / rule.days_per_week)) * 10)

                actual_days = sum(self.works_on_day[(agent.id, d)] for d in days if (agent.id, d) in self.works_on_day)
                actual_hours = sum(self.shift_vars[(agent.id, d, s)] * self.shift_map[s]['hours']
                                   for d in days for s in range(1, self.next_shift_id) 
                                   if (agent.id, d, s) in self.shift_vars)
                
                expressions['weekly_days'][agent.id][week] = actual_days
                expressions['weekly_hours'][agent.id][week] = actual_hours

                d_diff = model.NewIntVar(-7, 7, '')
                model.Add(d_diff == actual_days - target_days)
                abs_d = model.NewIntVar(0, 7, '')
                model.AddAbsEquality(abs_d, d_diff)
                total_penalties.append(abs_d * 5000)

                h_diff = model.NewIntVar(-1000, 1000, '')
                model.Add(h_diff == actual_hours - target_hours)
                abs_h = model.NewIntVar(0, 1000, '')
                model.AddAbsEquality(abs_h, h_diff)
                total_penalties.append(abs_h * 100)
                
                total_penalties.append(actual_hours * -1)

            # --- APLICACIÓN DEL APRENDIZAJE (BONIFICACIÓN) ---
            for day in self.all_days:
                weekday = day.weekday()
                prefs = self.agent_preferences.get(agent.id, {}).get(weekday, {})
                
                if prefs:
                    for s_id in range(1, self.next_shift_id):
                        if (agent.id, day, s_id) in self.shift_vars:
                            shift_name = self.shift_map[s_id]['name']
                            if shift_name in prefs:
                                weight = prefs[shift_name]
                                # Aplicar recompensa negativa (reduce el costo total)
                                total_penalties.append(self.shift_vars[(agent.id, day, s_id)] * (-1 * weight))

        model.Minimize(sum(total_penalties))
        return expressions

    def _process_solver_solution(self, solver):
        schedule_output = defaultdict(dict)
        solution_details = {}
        
        for agent in self.agents:
            for day in self.all_days:
                day_str = day.strftime('%Y-%m-%d')
                shift_name = 'LIBRE'
                
                existing = self.existing_schedule_map.get((agent.id, day))
                if existing:
                    shift_name = existing.shift
                else:
                    for s_id in range(1, self.next_shift_id):
                        if (agent.id, day, s_id) in self.shift_vars:
                            if solver.Value(self.shift_vars[(agent.id, day, s_id)]) == 1:
                                shift_name = self.shift_map[s_id]['name']
                                break
                
                schedule_output[agent.nombre_completo][day_str] = shift_name
        
        return schedule_output, solution_details

# --- FUNCIONES DE UTILIDAD PARA LA VISTA (CON SUPORTE ESCENARIOS) ---

def calculate_shift_duration_helper(shift_str):
    duration = 0
    if not isinstance(shift_str, str) or shift_str in VALID_AUSENCIA_CODES or shift_str == 'LIBRE': 
        return 0
    for part in shift_str.split('/'):
        try:
            start_str, end_str = [s.strip() for s in part.split('-')]
            start_time = datetime.datetime.strptime(start_str, '%H:%M')
            end_time = datetime.datetime.strptime('23:59', '%H:%M') + datetime.timedelta(minutes=1) if end_str == '24:00' else datetime.datetime.strptime(end_str, '%H:%M')
            if end_time <= start_time: end_time += datetime.timedelta(days=1)
            duration += (end_time - start_time).total_seconds() / 3600
        except: continue
    return duration

def build_schedule_view_model(segment_id, start_date, end_date, ausencias_file=None, scenario_id=None):
    # 1. Determinar Escenario
    if not scenario_id or str(scenario_id) == 'official':
        official = Scenario.query.filter_by(segment_id=segment_id, is_official=True).first()
        scenario_id = official.id if official else None

    # 2. Cargar Agentes (Reales + Simulados de ESTE escenario)
    if scenario_id:
        agents_query = Agent.query.filter(
            Agent.segment_id == segment_id,
            or_(Agent.scenario_id == None, Agent.scenario_id == scenario_id)
        )
    else:
        agents_query = Agent.query.filter(Agent.segment_id == segment_id, Agent.scenario_id == None)
        
    all_agents = agents_query.options(joinedload(Agent.scheduling_rule)).order_by(Agent.is_simulated, Agent.nombre_completo).all()
    
    if not all_agents: return {"schedule": [], "chart_data": {"labels": [], "days": {}}, "agent_map": {}, "kpi_summary": {}, "daily_forecast": {}}
    
    agent_ids = [a.id for a in all_agents]
    
    # 3. Cargar Horarios (Filtrados por Escenario)
    sched_query = Schedule.query.filter(
        Schedule.agent_id.in_(agent_ids),
        Schedule.schedule_date.between(start_date, end_date)
    )
    if scenario_id:
        sched_query = sched_query.filter(Schedule.scenario_id == scenario_id)
    else:
        sched_query = sched_query.filter(Schedule.scenario_id == None)

    schedules = sched_query.all()
    schedule_map = {(s.agent_id, s.schedule_date): s for s in schedules}
    
    # 4. Cargar Forecast (Filtrado por Escenario)
    staff_query = StaffingResult.query.filter(
        StaffingResult.segment_id == segment_id,
        StaffingResult.result_date.between(start_date, end_date)
    )
    if scenario_id:
        staff_query = staff_query.filter(StaffingResult.scenario_id == scenario_id)
    else:
        staff_query = staff_query.filter(StaffingResult.scenario_id == None)
        
    staffing_needs = staff_query.all()

    needs_by_day = {}
    daily_forecast = {} 
    time_labels = []
    
    if staffing_needs:
        first = next((r for r in staffing_needs if r.agents_online and r.agents_online != '{}'), None)
        if first:
            time_labels = sorted([k for k in json.loads(first.agents_online).keys() if ':' in str(k)])
            
            for r in staffing_needs:
                d_str = r.result_date.strftime('%Y-%m-%d')
                needs_by_day[r.result_date] = [math.ceil(float(json.loads(r.agents_online or '{}').get(lbl,0) or 0)) for lbl in time_labels]
                
                calls_data = json.loads(r.calls_forecast or '{}')
                aht_data = json.loads(r.aht_forecast or '{}')
                
                daily_forecast[d_str] = {
                    "calls": [float(calls_data.get(t, 0) or 0) for t in time_labels],
                    "aht": [float(aht_data.get(t, 0) or 0) for t in time_labels],
                    "sla_target": r.sla_target_percentage or 0.8,
                    "sla_time": r.sla_target_time or 20
                }

    if not time_labels:
        dt = datetime.datetime(2000,1,1,0,0)
        while dt.day == 1:
            time_labels.append(dt.strftime('%H:%M'))
            dt += datetime.timedelta(minutes=30)

    # 5. Construcción de Matriz
    schedule_data_list = []
    date_range = [start_date + datetime.timedelta(days=i) for i in range((end_date - start_date).days + 1)]
    
    coverage_data = {d.strftime('%Y-%m-%d'): np.zeros(len(time_labels)) for d in date_range}
    time_labels_map = {t: i for i, t in enumerate(time_labels)}

    for agent in all_agents:
        agent_sched = {}
        weekly_hours = defaultdict(float)
        for day in date_range:
            d_str = day.strftime('%Y-%m-%d')
            entry = schedule_map.get((agent.id, day))
            shift = entry.shift if entry else 'LIBRE'
            agent_sched[d_str] = shift
            
            h = calculate_shift_duration_helper(shift)
            iso_week = day.isocalendar()[1]
            weekly_hours[f"S{iso_week}"] += h
            
            if '-' in shift and shift not in VALID_AUSENCIA_CODES:
                for part in shift.split('/'):
                    try:
                        s, e = part.split('-')
                        s_idx = time_labels_map.get(s.strip())
                        e_idx = len(time_labels) if e.strip() == '24:00' else time_labels_map.get(e.strip())
                        if s_idx is not None and e_idx is not None:
                            coverage_data[d_str][s_idx:e_idx] += 1
                    except: continue
        
        w_summary = " | ".join([f"{k}: {v:g}h" for k,v in sorted(weekly_hours.items())])
        raw_contract = float(agent.scheduling_rule.weekly_hours) if agent.scheduling_rule else 0
        
        schedule_data_list.append({
            'agent_id': agent.id, 'nombre_completo': agent.nombre_completo,
            'identificacion': agent.identificacion, 'contrato': f"{raw_contract}h",
            'raw_contract_hours': raw_contract, 'turno_sugerido': agent.turno_sugerido,
            'weekly_hours_summary': w_summary, 'schedule': agent_sched
        })

    chart_data = {"labels": time_labels, "days": {}}
    for d in date_range:
        d_str = d.strftime('%Y-%m-%d')
        chart_data["days"][d_str] = {
            "need": needs_by_day.get(d, [0]*len(time_labels)),
            "coverage": coverage_data[d_str].tolist()
        }

    bmed_count = sum(1 for s in schedules if s.shift == 'BMED')
    vac_count = sum(1 for s in schedules if s.shift == 'VAC')
    days_count = len(date_range)
    
    kpi_summary = {
        'active_agents': len(all_agents),
        'avg_bmed': round(bmed_count / days_count, 1) if days_count > 0 else 0,
        'avg_vac': round(vac_count / days_count, 1) if days_count > 0 else 0
    }

    return {
        "schedule": schedule_data_list,
        "chart_data": chart_data,
        "agent_map": {a.nombre_completo: a.id for a in all_agents},
        "kpi_summary": kpi_summary,
        "daily_forecast": daily_forecast,
        "time_labels": time_labels
    }