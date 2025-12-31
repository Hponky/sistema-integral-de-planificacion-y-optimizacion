"""
Algoritmo Greedy optimizado para la planificación de horarios.
"""

from datetime import timedelta
from collections import defaultdict
from .utils import compute_earliest_start
from .preprocessor import SchedulerPreprocessor

class GreedyScheduler:
    """
    Motor de planificación basado en un enfoque codicioso (greedy).
    Ideal para grandes volúmenes de agentes.
    """

    def __init__(self):
        self.preprocessor = SchedulerPreprocessor()

    def solve(self, agents, start_date, days_count, rules_config, requirements, calls_forecast):
        """
        Ejecuta el algoritmo greedy con complejidad O(A × D × C).
        """
        all_dates = [start_date + timedelta(days=i) for i in range(days_count)]
        
        # Pre-computar requerimientos y llamadas
        req_arrays = {}
        call_arrays = {}
        max_call_vol = 1.0

        for d in all_dates:
            d_str = d.strftime("%Y-%m-%d")
            reqs = requirements.get(d_str, [])
            if len(reqs) < 48: reqs = reqs + [0] * (48 - len(reqs))
            req_arrays[d_str] = reqs
            
            calls = calls_forecast.get(d_str, [])
            if len(calls) < 48: calls = calls + [0] * (48 - len(calls))
            call_arrays[d_str] = calls
            
            day_max = max(calls) if calls else 0
            if day_max > max_call_vol: max_call_vol = day_max
        
        # Estado de cobertura
        coverage_state = {d.strftime("%Y-%m-%d"): [0] * 48 for d in all_dates}
        results = []
        
        for agent in agents:
            absence_map = self.preprocessor.get_absence_map(agent)
            schedule = {"agent": agent, "shifts": {}}
            
            # Estado del agente
            contract_hours = float(agent.get('contract_hours', 40) or 40)
            if contract_hours <= 0: contract_hours = 40.0
            monthly_target_min = contract_hours * (days_count / 7) * 60
            
            total_minutes = 0
            week_work_days = defaultdict(int)
            week_has_10h = defaultdict(bool)
            sundays_worked = 0
            last_shift_end = None
            max_sundays = int(rules_config.get('maxSundays', 2))
            
            for d_idx, date in enumerate(all_dates):
                d_str = date.strftime("%Y-%m-%d")
                iso_year, iso_week, _ = date.isocalendar()
                week_idx = f"{iso_year}-{iso_week}"
                
                # 1. Ausencias
                if date.date() in absence_map:
                    abs_info = absence_map[date.date()]
                    schedule["shifts"][d_str] = {
                        "type": "ABSENCE",
                        "label": abs_info["type"],
                        "duration_minutes": 0,
                        "description": abs_info.get("description", "")
                    }
                    week_work_days[week_idx] += 1
                    continue
                
                # 2. Obtener turnos
                available_shifts = self.preprocessor.get_canonical_shifts(agent, date)
                if not available_shifts:
                    schedule["shifts"][d_str] = {"type": "OFF", "label": "LIBRE", "duration_minutes": 0}
                    continue
                
                # 3. Reglas básicas
                country = agent.get('country', 'ES')
                base_limit = 5 if country == 'ES' else 6
                
                # Regla CO: Si hay turno 10h, max 5 días
                current_limit = base_limit
                if country != 'ES' and week_has_10h[week_idx]:
                    current_limit = 5

                is_weekend = date.weekday() in [5, 6]
                is_sunday = date.weekday() == 6
                
                # Regla CO: Max 2 domingos
                effective_max_sundays = 2 if country != 'ES' else max_sundays

                can_work = True
                if week_work_days[week_idx] >= current_limit: can_work = False
                if is_sunday and sundays_worked >= effective_max_sundays: can_work = False
                if total_minutes >= monthly_target_min: can_work = False
                
                if not can_work:
                    schedule["shifts"][d_str] = {"type": "OFF", "label": "LIBRE", "duration_minutes": 0}
                    continue
                
                # 4. Selección del mejor turno
                earliest_start = compute_earliest_start(last_shift_end)
                day_reqs = req_arrays[d_str]
                day_calls = call_arrays[d_str]
                coverage = coverage_state[d_str]
                
                day_scores_unmet = [(10 + (day_calls[i] / max_call_vol) * 20) for i in range(48)]
                day_scores_met = [-0.5 for i in range(48)]

                best_shift = None
                best_score = 0 
                
                for shift in available_shifts:
                    if shift['start_min'] < earliest_start: continue
                    
                    # Regla CO: Anticipar restricción de 10h
                    if country != 'ES' and shift['duration_minutes'] >= 600:
                        # Si elegimos este turno >= 10h, el límite de la semana será 5.
                        # Si ya hemos trabajado 5 días (o más), no podemos asignarlo.
                        if week_work_days[week_idx] >= 5: continue

                    # Definir tolerancia superior CERO para evitar sobrepasar contrato
                    tolerance_over = 0
                    if total_minutes + shift['duration_minutes'] > (monthly_target_min + tolerance_over): continue
                    
                    s_idx = shift['start_min'] // 30
                    e_idx = min(shift['end_min'] // 30, 48)
                    score = sum(day_scores_unmet[i] if day_reqs[i] > coverage[i] else day_scores_met[i] 
                               for i in range(s_idx, e_idx))
                    
                    if score > best_score:
                        best_score = score
                        best_shift = shift
                
                if best_shift:
                    # Para España forzar al 100%, otros al 95%
                    coverage_threshold = 1.0 if country == 'ES' else 0.95
                    should_take = (best_score > 0) or (total_minutes < (monthly_target_min * coverage_threshold))
                    
                    if should_take:
                        schedule["shifts"][d_str] = best_shift
                        total_minutes += best_shift['duration_minutes']
                        week_work_days[week_idx] += 1
                        
                        if country != 'ES' and best_shift['duration_minutes'] >= 600:
                            week_has_10h[week_idx] = True

                        last_shift_end = best_shift['end_min']
                        if is_sunday:
                            sundays_worked += 1
                        
                        s_idx = best_shift['start_min'] // 30
                        e_idx = min(best_shift['end_min'] // 30, 48)
                        for i in range(s_idx, e_idx):
                            coverage_state[d_str][i] += 1
                    else:
                        schedule["shifts"][d_str] = {"type": "OFF", "label": "LIBRE", "duration_minutes": 0}
                else:
                    schedule["shifts"][d_str] = {"type": "OFF", "label": "LIBRE", "duration_minutes": 0}
            
            results.append(schedule)
        
        return results
