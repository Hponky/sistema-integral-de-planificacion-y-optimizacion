"""
Módulo de preprocesamiento para el Scheduler.
Se encarga de transformar ventanas horarias y filtrar turnos válidos.
"""

from .constants import CANONICAL_SHIFTS_ES, CANONICAL_SHIFTS_CO

class SchedulerPreprocessor:
    """
    Gestiona la preparación de datos de agentes para el motor de optimización.
    """

    def preprocess_agent_windows(self, agents):
        """
        Convierte ventanas horarias en formato string a minutos para acceso rápido.
        """
        for agent in agents:
            raw_wins = agent.get('windows', {})
            parsed = {} # day_int -> list of (start_min, end_min)
            
            def parse_list(w_list):
                res = []
                for (s_str, e_str) in w_list:
                    try:
                        sh, sm = map(int, s_str.split(':'))
                        eh, em = map(int, e_str.split(':'))
                        start_min = sh * 60 + sm
                        end_min = eh * 60 + em
                        if end_min <= start_min: end_min += 24*60
                        res.append((start_min, end_min))
                    except: continue
                return res

            if isinstance(raw_wins, dict):
                 for k, v in raw_wins.items():
                     try:
                         d_int = int(k)
                         parsed[d_int] = parse_list(v)
                     except: pass
            
            agent['_parsed_windows'] = parsed

    def get_canonical_shifts(self, agent, date):
        """
        Obtiene los turnos canónicos aplicables para un agente en una fecha dada.
        Si el agente no tiene ventanas para fines de semana, usa las del viernes o lunes.
        """
        country = agent.get('country', 'ES')
        shifts = CANONICAL_SHIFTS_CO if country == 'CO' else CANONICAL_SHIFTS_ES
        max_hours = 10 if country == 'CO' else 8
        
        w_day = date.weekday()  # 0=Lunes, 6=Domingo
        parsed_windows = agent.get('_parsed_windows', {})
        windows = parsed_windows.get(w_day, [])
        
        # Si no hay ventanas para domingo (6), usar las del sábado o viernes
        if not windows and w_day == 6:
            windows = parsed_windows.get(5, [])  # Usar sábado
            if not windows:
                windows = parsed_windows.get(4, [])  # Usar viernes
            if not windows:
                windows = parsed_windows.get(0, [])  # Usar lunes como último recurso
        
        # Si no hay ventanas para sábado (5), usar las del viernes o domingo
        if not windows and w_day == 5:
            windows = parsed_windows.get(4, [])  # Usar viernes
            if not windows:
                windows = parsed_windows.get(6, [])  # Usar domingo
            if not windows:
                windows = parsed_windows.get(0, [])  # Usar lunes
        
        if not windows:
            return []
        
        # Lógica de Turno Forzado (Sugerido validado)
        forced_shift_str = agent.get('forced_shift')
        if forced_shift_str and '/' not in str(forced_shift_str): # Solo soportar turnos simples por ahora
             try:
                 # "08:00-15:00" -> start_min, end_min
                 s_str, e_str = forced_shift_str.split('-')
                 sh, sm = map(int, s_str.split(':'))
                 eh, em = map(int, e_str.split(':'))
                 f_start = sh * 60 + sm
                 f_end = eh * 60 + em
                 f_dur = (f_end - f_start)
                 
                 # Validar si cabe en ventana
                 fits_window = False
                 for (win_start, win_end) in windows:
                     if f_start >= win_start and f_end <= win_end:
                         fits_window = True
                         break
                 
                 if fits_window:
                     # Retornar SOLO este turno para obligar/priorizar
                     return [{
                        'start_min': f_start,
                        'end_min': f_end,
                        'duration_minutes': f_dur,
                        'label': forced_shift_str,
                        'type': 'WORK'
                     }]
             except Exception:
                 pass # Fallback a normal

        valid_shifts = []
        
        for start_h, dur_h, label in shifts:
            if dur_h < 4 or dur_h > max_hours:
                continue
                
            start_min = start_h * 60
            end_min = start_min + dur_h * 60
            
            for (win_start, win_end) in windows:
                if start_min >= win_start and end_min <= win_end:
                     valid_shifts.append({
                        'start_min': start_min,
                        'end_min': end_min,
                        'duration_minutes': dur_h * 60,
                        'label': label,
                        'type': 'WORK'
                    })
                     break
        
        return valid_shifts

    def get_absence_map(self, agent):
        """
        Genera un mapa de ausencias por fecha para un agente.
        """
        from datetime import datetime, timedelta
        absence_map = {}  # date -> {type, description}
        for abs_rec in agent.get("absences", []):
            try:
                s_d = datetime.strptime(abs_rec["start_date"], "%Y-%m-%d").date()
                e_d = datetime.strptime(abs_rec["end_date"], "%Y-%m-%d").date()
                abs_type = abs_rec.get("type", "AUS")
                abs_desc = abs_rec.get("description", "")
                current = s_d
                while current <= e_d:
                    absence_map[current] = {
                        "type": abs_type,
                        "description": abs_desc
                    }
                    current += timedelta(days=1)
            except:
                continue
        return absence_map
