# app/services/rule_engine.py

import logging
from ortools.sat.python import cp_model

# Importar desde config, no desde models
from config import VALID_AUSENCIA_CODES 

logger = logging.getLogger(__name__)

class RuleEngine:
    """
    Aplica las reglas de planificación basadas en la jerarquía:
    SchedulingRule (Contrato) -> Segment (Operación) -> Agent (Individual).
    """
    def __init__(self, all_days, weeks_data, time_labels_map):
        self.all_days = all_days
        self.weeks_data = weeks_data
        self.time_labels_map = time_labels_map
        self.total_penalties = []

    def apply_agent_rules(self, model, agent, works_on_day, shift_vars, shift_map):
        """
        Punto de entrada para aplicar todas las reglas a un agente específico.
        """
        rule = agent.scheduling_rule
        segment = agent.segment

        if not rule or not segment:
            logger.warning(f"Agente {agent.id} no tiene regla de contrato o segmento asignado. Omitiendo.")
            return

        # 1. Regla de Contrato: Objetivo de Horas Semanales (Siempre es un objetivo "blando")
        self._apply_weekly_hours_target(model, agent, works_on_day, shift_vars, shift_map, rule)

        # 2. Regla de Contrato: Días Consecutivos (Restricción "dura")
        if rule.max_consecutive_work_days:
            self._apply_max_consecutive_days_rule(model, agent, works_on_day, rule)

        # 3. Regla de Segmento: Política de Fines de Semana
        if segment.weekend_policy:
            self._apply_weekend_policy(model, agent, works_on_day, segment)

    def get_penalties(self):
        """Devuelve la lista de penalizaciones para la función objetivo."""
        return self.total_penalties

    # --- Implementaciones de Reglas Específicas ---

    def _apply_weekly_hours_target(self, model, agent, works_on_day, shift_vars, shift_map, rule):
        """Aplica el objetivo de horas semanales definido en el contrato del agente."""
        target_hours = rule.weekly_hours
        logger.info(f"Agente {agent.id}: Aplicando objetivo de {target_hours} horas semanales.")
        
        for week_num, week_days in self.weeks_data.items():
            total_hours_expr = sum(
                shift_vars.get((agent.id, d, s), 0) * shift_map[s]['hours'] 
                for d in week_days 
                for s in shift_map if s > 0 and (agent.id, d, s) in shift_vars
            )
            
            # --- CORRECCIÓN CLAVE: Asegurarse de que el objetivo sea un entero ---
            target_hours_int_x10 = int(target_hours * 10)
            
            diff = model.NewIntVar(-1000, 1000, f'hours_diff_{agent.id}_{week_num}')
            model.Add(diff == total_hours_expr - target_hours_int_x10)
            abs_diff = model.NewIntVar(0, 1000, f'abs_hours_diff_{agent.id}_{week_num}')
            model.AddAbsEquality(abs_diff, diff)
            self.total_penalties.append(abs_diff * 100)

    def _apply_max_consecutive_days_rule(self, model, agent, works_on_day, rule):
        """Aplica la restricción de días consecutivos del contrato."""
        max_days = rule.max_consecutive_work_days
        logger.info(f"Agente {agent.id}: Aplicando máximo de {max_days} días consecutivos.")
        
        for i in range(len(self.all_days) - max_days):
            work_window = [works_on_day.get((agent.id, self.all_days[j]), 0) for j in range(i, i + max_days + 1)]
            model.Add(sum(work_window) <= max_days)

    def _apply_weekend_policy(self, model, agent, works_on_day, segment):
        """Aplica la política de fines de semana definida para el segmento."""
        policy = segment.weekend_policy
        min_off = segment.min_full_weekends_off_per_month
        
        logger.info(f"Agente {agent.id} (Segmento: {segment.name}): Aplicando política de finde '{policy}' (Mín: {min_off}).")

        if policy == 'REQUIRE_FULL_WEEKEND_OFF':
            self._apply_full_weekend_off(model, agent, works_on_day, min_off)
        elif policy == 'REQUIRE_ONE_DAY_OFF':
            self._apply_one_weekend_day_off(model, agent, works_on_day, min_off)
        else:
            logger.info(f"Política de finde '{policy}' no requiere restricciones específicas.")
            return

    def _apply_full_weekend_off(self, model, agent, works_on_day, min_off):
        """Lógica para requerir fines de semana completos libres."""
        weekends_off_vars = []
        for week_num, week_days in self.weeks_data.items():
            sat_date = next((d for d in week_days if d.weekday() == 5), None)
            sun_date = next((d for d in week_days if d.weekday() == 6), None)
            if not sat_date or not sun_date: continue

            work_sat = works_on_day.get((agent.id, sat_date), 0)
            work_sun = works_on_day.get((agent.id, sun_date), 0)

            if work_sat == 0 and work_sun == 0:
                weekends_off_vars.append(1)
                continue
            
            is_weekend_off = model.NewBoolVar(f'w_off_{agent.id}_{week_num}')
            model.Add(work_sat + work_sun == 0).OnlyEnforceIf(is_weekend_off)
            model.Add(work_sat + work_sun > 0).OnlyEnforceIf(is_weekend_off.Not())
            weekends_off_vars.append(is_weekend_off)

        if weekends_off_vars:
            model.Add(sum(weekends_off_vars) >= min_off)

    def _apply_one_weekend_day_off(self, model, agent, works_on_day, min_off):
        """Lógica para requerir al menos un día (sábado o domingo) libre por fin de semana."""
        weekends_off_vars = []
        for week_num, week_days in self.weeks_data.items():
            sat_date = next((d for d in week_days if d.weekday() == 5), None)
            sun_date = next((d for d in week_days if d.weekday() == 6), None)
            if not sat_date or not sun_date: continue

            work_sat = works_on_day.get((agent.id, sat_date), 0)
            work_sun = works_on_day.get((agent.id, sun_date), 0)

            is_weekend_off = model.NewBoolVar(f'w_off_{agent.id}_{week_num}')
            model.Add(work_sat == 0).OnlyEnforceIf(is_weekend_off)
            model.Add(work_sun == 0).OnlyEnforceIf(is_weekend_off)
            model.Add(work_sat + work_sun > 0).OnlyEnforceIf(is_weekend_off.Not())
            weekends_off_vars.append(is_weekend_off)

        if weekends_off_vars:
            model.Add(sum(weekends_off_vars) >= min_off)