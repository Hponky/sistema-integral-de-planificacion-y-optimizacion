"""
Motor de optimización CP-SAT para la planificación de horarios.
Utiliza Google OR-Tools para encontrar soluciones óptimas o factibles.
"""

from datetime import timedelta, datetime
from ortools.sat.python import cp_model
import json
import logging
from .utils import compute_earliest_start
from .preprocessor import SchedulerPreprocessor

logger = logging.getLogger(__name__)

class CPSATSolver:
    """
    Solucionador basado en restricciones (Constraint Programming).
    """

    def __init__(self):
        self.preprocessor = SchedulerPreprocessor()

    def solve(self, agents, start_date, days_count, rules_config, requirements, calls_forecast):
        """
        Resuelve el problema de planificación usando CP-SAT.
        """
        model = cp_model.CpModel()
        all_dates = [start_date + timedelta(days=i) for i in range(days_count)]
        
        # 1. Normalización y Preprocesamiento
        max_call_vol = 1.0
        for d in all_dates:
             d_str = d.strftime("%Y-%m-%d")
             calls = calls_forecast.get(d_str, [])
             if calls:
                 m = max(calls)
                 if m > max_call_vol: max_call_vol = m

        absence_maps = {a_idx: self.preprocessor.get_absence_map(agent) 
                       for a_idx, agent in enumerate(agents)}
        
        valid_shifts = {}
        for a_idx, agent in enumerate(agents):
            for d_idx, date in enumerate(all_dates):
                if date.date() in absence_maps[a_idx]:
                    continue
                shifts = self.preprocessor.get_canonical_shifts(agent, date)
                if shifts:
                    valid_shifts[(a_idx, d_idx)] = shifts
        
        # 2. Variables de decisión
        shift_vars = {}
        works_on_day = {}
        
        for (a_idx, d_idx), shifts in valid_shifts.items():
            day_vars = []
            for s_idx, shift in enumerate(shifts):
                var = model.NewBoolVar(f"s_{a_idx}_{d_idx}_{s_idx}")
                shift_vars[(a_idx, d_idx, s_idx)] = var
                day_vars.append(var)
            
            if day_vars:
                model.Add(sum(day_vars) <= 1)
                works_var = model.NewBoolVar(f"w_{a_idx}_{d_idx}")
                model.Add(works_var == sum(day_vars))
                works_on_day[(a_idx, d_idx)] = works_var
        
        # 3. Restricciones
        max_sundays = int(rules_config.get('maxSundays', 2))
        obj_terms = []
        
        for a_idx, agent in enumerate(agents):
            country = agent.get('country', 'ES')
            work_day_limit = 5 if country == 'ES' else 6
            
            # Días de trabajo y fines de semana
            # Agrupar por semanas ISO (Lunes-Domingo)
            week_groups = {}
            for d_idx, date in enumerate(all_dates):
                iso_year, iso_week, _ = date.isocalendar()
                week_key = (iso_year, iso_week)
                if week_key not in week_groups:
                    week_groups[week_key] = []
                week_groups[week_key].append(d_idx)

            # Restricción de días máximos de trabajo por semana calendario
            for w_key, week_days_indices in week_groups.items():
                week_work_vars = [works_on_day[(a_idx, d)] for d in week_days_indices if (a_idx, d) in works_on_day]
                if week_work_vars:
                    model.Add(sum(week_work_vars) <= work_day_limit)
                
                # Restricción de fines de semana (Sábado y Domingo de la misma semana)
                weekend_indices = [d for d in week_days_indices if all_dates[d].weekday() in [5, 6]]
                weekend_vars = [works_on_day[(a_idx, d)] for d in weekend_indices if (a_idx, d) in works_on_day]
                # Si hay ambos días (Sáb y Dom), limitar a trabajar máximo 1 (si esa es la regla deseada, o dejar libre)
                # La regla original decía: si len(weekend_vars) == 2 -> sum <= 1. Mantenemos eso.
                if len(weekend_vars) == 2:
                    model.Add(sum(weekend_vars) <= 1)
            
            # Regla de Domingos
            sunday_indices = [d for d in range(days_count) if all_dates[d].weekday() == 6]
            sunday_vars = [works_on_day[(a_idx, d)] for d in sunday_indices if (a_idx, d) in works_on_day]
            
            if sunday_vars:
                # España: Max definidos en config (generalmente 2)
                # Colombia: ESTRICTAMENTE Máx 2 domingos al mes
                actual_max_sundays = 2 if country != 'ES' else max_sundays
                model.Add(sum(sunday_vars) <= actual_max_sundays)
            
            # Reglas de Días Libres / Jornada (Colombia vs España)
            # Colombia: 
            # - Base: 6 días de trabajo (1 libranza).
            # - Excepción: Si tiene turno de 10h (600min) -> 5 días de trabajo (2 libranzas).
            if country != 'ES':
                for w_key, week_days_indices in week_groups.items():
                    # Variables de trabajo para esta semana (días disponibles)
                    week_work_vars = [works_on_day[(a_idx, d)] for d in week_days_indices if (a_idx, d) in works_on_day]
                    
                    if not week_work_vars: continue

                    # Detectar turnos de 10h
                    week_10h_vars = []
                    for d_idx in week_days_indices:
                        if (a_idx, d_idx) not in valid_shifts: continue
                        for s_idx, shift in enumerate(valid_shifts[(a_idx, d_idx)]):
                            if shift['duration_minutes'] >= 600: 
                                if (a_idx, d_idx, s_idx) in shift_vars:
                                    week_10h_vars.append(shift_vars[(a_idx, d_idx, s_idx)])
                    
                    # Lógica estricta
                    # 1. Definir si hay turno de 10h
                    has_10h = model.NewBoolVar(f'has10h_{a_idx}_{w_key}')
                    if week_10h_vars:
                       model.Add(sum(week_10h_vars) >= 1).OnlyEnforceIf(has_10h)
                       model.Add(sum(week_10h_vars) == 0).OnlyEnforceIf(has_10h.Not())
                    else:
                       model.Add(has_10h == 0)

                    # 2. Constraints de Días Trabajados basados en Disponibilidad Real (Excluyendo ausencias)
                    available_days_count = len(week_work_vars)
                    
                    if available_days_count > 0:
                        # Regla 1: Si hay turno de 10h -> Deben tener 2 días de libranza (Max Work = Available - 2)
                        # Nota: Se permite menos si no hay carga, pero el límite superior es estricto.
                        limit_10h = max(0, available_days_count - 2)
                        model.Add(sum(week_work_vars) <= limit_10h).OnlyEnforceIf(has_10h)

                        # Regla 2: Si NO hay turno de 10h -> Sólo 1 día de libranza (Min Work = Available - 1)
                        # Esta regla es de "Robustez": forzar a trabajar lo máximo permitido (6 días).
                        # Solo se aplica si el contrato es "Full Time" (>= 36h semanales) para evitar infactibilidad en Part Time.
                        contract_hours_weekly = float(agent.get('contract_hours', 40) or 40)
                        
                        if contract_hours_weekly >= 36:
                            limit_normal_min = max(0, available_days_count - 1)
                            # Forzamos: Trabajo >= Disponibles - 1 (Es decir, Max 1 día libre)
                            model.Add(sum(week_work_vars) >= limit_normal_min).OnlyEnforceIf(has_10h.Not())
                            
                            # También implícitamente respetamos la ley de 1 día libre (Max Work <= Available - 1)
                            # Esto usualmente lo maneja work_day_limit o weekly_hours, pero para asegurar:
                            # model.Add(sum(week_work_vars) <= limit_normal_min).OnlyEnforceIf(has_10h.Not()) # Opcional, pero seguro.


            
            # Horas mensuales (Cumplimiento Estricto)
            contract_hours = float(agent.get('contract_hours', 40) or 40)
            if contract_hours <= 0: contract_hours = 40.0
            
            # Cálculo de horas proporcionales al periodo
            monthly_target_min = int(contract_hours * (days_count / 7) * 60)
            
            hours_terms = []
            for d_idx in range(days_count):
                if (a_idx, d_idx) not in valid_shifts: continue
                for s_idx, shift in enumerate(valid_shifts[(a_idx, d_idx)]):
                    if (a_idx, d_idx, s_idx) in shift_vars:
                        hours_terms.append(shift_vars[(a_idx, d_idx, s_idx)] * shift['duration_minutes'])
            
            if hours_terms:
                # España: Tolerancia Casi Cero (0 min a +15 min) - Cumplimiento Exacto
                # Colombia: Tolerancia Flexibilidad Baja (-4h a +15 min)
                if country == 'ES':
                     tolerance_under = 0   # No permitir menos
                     tolerance_over = 0    # Estricto: Nunca más de contrato
                else:
                     tolerance_under = 240 # 4h margen inferior (flexibilidad CO)
                     tolerance_over = 0    # Estricto: Nunca más de contrato

                is_active = model.NewBoolVar(f'active_{a_idx}')
                total_minutes = sum(hours_terms)
                
                # Definir rango aceptable
                min_limit = int(max(0, monthly_target_min - tolerance_under))
                max_limit = int(monthly_target_min + tolerance_over)
                
                # Si está activo, cumplir con el rango. Si no, 0 horas.
                # IMPORTANTE: Restricción dura de NO exceder el contrato
                model.Add(total_minutes <= max_limit).OnlyEnforceIf(is_active)
                model.Add(total_minutes >= min_limit).OnlyEnforceIf(is_active)
                model.Add(total_minutes == 0).OnlyEnforceIf(is_active.Not())
                
                # Incentivo fuerte para estar activo (cumplir contrato)
                obj_terms.append(is_active * 500000)

                # Penalizar distancia al objetivo exacto (minimizar diferencia)
                # diff_pos = total - target (si total > target)
                # diff_neg = target - total (si total < target)
                diff_pos = model.NewIntVar(0, tolerance_over, f'diff_p_{a_idx}')
                diff_neg = model.NewIntVar(0, tolerance_under, f'diff_n_{a_idx}')
                model.Add(total_minutes - monthly_target_min == diff_pos - diff_neg).OnlyEnforceIf(is_active)
                # Penalizar desviaciones fuertemente (paga más ser exacto)
                obj_terms.append((diff_pos + diff_neg) * -5000)
            
            # Descanso de 12h
            for d_idx in range(days_count - 1):
                if (a_idx, d_idx) not in valid_shifts or (a_idx, d_idx + 1) not in valid_shifts: continue
                shifts_d1 = valid_shifts[(a_idx, d_idx)]
                shifts_d2 = valid_shifts[(a_idx, d_idx + 1)]
                
                for i1, shift1 in enumerate(shifts_d1):
                    if shift1['end_min'] <= 12 * 60: continue
                    earliest_start_d2 = compute_earliest_start(shift1['end_min'])
                    conflicting_vars = [shift_vars.get((a_idx, d_idx+1, i2)) for i2, s2 in enumerate(shifts_d2) 
                                       if s2['start_min'] < earliest_start_d2]
                    conflicting_vars = [v for v in conflicting_vars if v]
                    if conflicting_vars:
                        model.Add(shift_vars[(a_idx, d_idx, i1)] + sum(conflicting_vars) <= 1)
        
        # 4. Función Objetivo - Cobertura
        for d_idx, date in enumerate(all_dates):
            d_str = date.strftime("%Y-%m-%d")
            reqs = requirements.get(d_str, [0] * 48)
            calls = calls_forecast.get(d_str, [0] * 48)
            
            slot_scores = []
            for i in range(48):
                 vol_weight = calls[i] / max_call_vol
                 score = (1000 + int(vol_weight * 2000)) if reqs[i] > 0 else -5
                 slot_scores.append(score)

            for a_idx in range(len(agents)):
                if (a_idx, d_idx) not in valid_shifts: continue
                for s_idx, shift in enumerate(valid_shifts[(a_idx, d_idx)]):
                    if (a_idx, d_idx, s_idx) not in shift_vars: continue
                    s_slot = shift['start_min'] // 30
                    e_slot = min(shift['end_min'] // 30, 48)
                    score = sum(slot_scores[i] for i in range(s_slot, e_slot))
                    obj_terms.append(shift_vars[(a_idx, d_idx, s_idx)] * score)

        model.Maximize(sum(obj_terms))
        
        # 5. Resolución
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 30.0
        solver.parameters.num_search_workers = 4
        
        status = solver.Solve(model)
        
        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            results = []
            for a_idx, agent in enumerate(agents):
                sched_map = {}
                for d_idx, date in enumerate(all_dates):
                    d_str = date.strftime("%Y-%m-%d")
                    if date.date() in absence_maps[a_idx]:
                        abs_info = absence_maps[a_idx][date.date()]
                        sched_map[d_str] = {
                            "type": "ABSENCE", "label": abs_info["type"],
                            "duration_minutes": 0, "description": abs_info.get("description", "")
                        }
                        continue
                    
                    found = False
                    if (a_idx, d_idx) in valid_shifts:
                        for s_idx, shift in enumerate(valid_shifts[(a_idx, d_idx)]):
                            if (a_idx, d_idx, s_idx) in shift_vars and solver.Value(shift_vars[(a_idx, d_idx, s_idx)]) == 1:
                                sched_map[d_str] = shift
                                found = True
                                break
                    if not found:
                        sched_map[d_str] = {"type": "OFF", "label": "LIBRE", "duration_minutes": 0}
                results.append({"agent": agent, "shifts": sched_map})
            return results
        
        return None
