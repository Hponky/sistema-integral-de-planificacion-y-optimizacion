
import pandas as pd
from datetime import datetime, time
import re

def safe_date_str(val):
    if pd.isna(val): return None
    # If it's a pandas Timestamp
    if hasattr(val, 'strftime'):
        return val.strftime('%Y-%m-%d')
    return str(val)

class InputParser:
    REQUIRED_COLUMNS = [
        "nombre_completo", "contrato", "turno_sugerido", 
        "ventana_lunes", "ventana_martes", "ventana_miercoles", 
        "ventana_jueves", "ventana_viernes", "ventana_sabado", "ventana_domingo"
    ]


    def parse_excel(self, file_path, country_override=None):
        """
        Parses the uploaded Excel file and extracts agent data and constraints.
        """
        # Robustly find the header row
        # 1. Read first few rows without header
        preview = pd.read_excel(file_path, header=None, nrows=20)
        header_idx = 0
        
        for idx, row in preview.iterrows():
            # Convert row values to string and check for key column
            row_str = [str(val).strip().lower() for val in row.values]
            if "nombre_completo" in row_str or "nombre" in row_str:
                header_idx = idx
                break
        
        # 2. Read actual dataframe with correct header
        df = pd.read_excel(file_path, header=header_idx)
        
        # Normalize column names (strip, lower)
        df.columns = [str(c).strip() for c in df.columns]
        # logger.debug(f"Excel Columns Detected: {list(df.columns)}")
        
        # Helper to get column case-insensitive 
        def get_col(row, *aliases):
            for a in aliases:
                for c in df.columns:
                    if c.lower() == a.lower():
                        return row.get(c)
            return None
            


        agents_data = []

        for _, row in df.iterrows():
            dni_val = get_col(row, "identificacion", "id", "dni", "nif", "documento", "matricula", "cedula")
            name = get_col(row, "nombre_completo", "nombre")
            
            if pd.isna(name) and pd.isna(dni_val):
                continue
            
            dni_val = str(dni_val).strip() if not pd.isna(dni_val) else f"NO_ID_{_}"

            # Parse 'semanas_libres_finde' (e.g., "1,3,5")
            semanas_libres_raw = get_col(row, "semanas_libres_finde", "semanas_libres")
            semanas_libres = []
            if semanas_libres_raw and not pd.isna(semanas_libres_raw):
                try:
                    semanas_libres = [int(x.strip()) for x in str(semanas_libres_raw).split(',') if x.strip().isdigit()]
                except:
                    pass

            # Parse rotation
            rotacion_domingo = get_col(row, "rotacion_mensual_domingo")
            max_sundays = 10 if str(rotacion_domingo).upper() == "PRIORITARIO" else 2
            
            # Country Inference
            country = 'ES'
            if country_override:
                country = country_override
            else:
                center_val = str(get_col(row, "centro", "site", "plataforma", "ubicacion", "campaña") or "").upper()
                if "COLOMBIA" in center_val or "BOGOTA" in center_val or "MEDELLIN" in center_val:
                    country = 'CO'
                elif "ESPAÑA" in center_val or "MADRID" in center_val or "BARCELONA" in center_val:
                    country = 'ES'

            contrato_raw = get_col(row, "contrato", "horas", "jornada", "h/s")
            contrato = 0
            if contrato_raw and not pd.isna(contrato_raw):
                try:
                    s_raw = str(contrato_raw).strip()
                    # If HH:MM format, take HH
                    if ':' in s_raw:
                        s_raw = s_raw.split(':')[0]
                    # Remove non-numeric except dot and comma
                    clean_str = re.sub(r'[^0-9.,]', '', s_raw).replace(',', '.')
                    contrato = float(clean_str)
                except:
                    contrato = 0
            
            agent = {
                "id": dni_val, 
                "name": name,
                "dni": dni_val, 
                "center": get_col(row, "centro", "site", "plataforma", "ubicacion", "campaña"),
                "service": get_col(row, "Segmento", "servicio"),
                "contract_hours": contrato,
                "suggested_shift": get_col(row, "turno_sugerido"),
                "modalidad_finde": str(get_col(row, "modalidad_finde")).upper(),
                "rotacion_mensual_domingo": rotacion_domingo,
                "semanas_libres_finde": semanas_libres,
                "country": country,
                "max_sundays": max_sundays,
                "windows": {
                    0: self._parse_window(get_col(row, "ventana_lunes")),
                    1: self._parse_window(get_col(row, "ventana_martes")),
                    2: self._parse_window(get_col(row, "ventana_miercoles")),
                    3: self._parse_window(get_col(row, "ventana_jueves")),
                    4: self._parse_window(get_col(row, "ventana_viernes")),
                    5: self._parse_window(get_col(row, "ventana_sabado")),
                    6: self._parse_window(get_col(row, "ventana_domingo"))
                },
                "entry_date": safe_date_str(get_col(row, "Fecha Alta")),
                "exit_date": safe_date_str(get_col(row, "Fecha Baja")),
                "absences": []
            }

            # VALIDATOR DE TURNO SUGERIDO
            # "Si el turno sugerido y la ventana horaria coincide con las horas de su contrato, se debe de poner ese mismo turno sugerido"
            sug_shift_str = agent["suggested_shift"]
            contract_hours = agent["contract_hours"]
            forced_shift = None
            validation_msg = None

            if sug_shift_str and not pd.isna(sug_shift_str) and str(sug_shift_str).strip() not in ["-", "LIBRE"]:
                try:
                    # Calcular duración del turno sugerido (considera turnos partidos)
                    parts = str(sug_shift_str).split('/')
                    total_minutes = 0
                    for part in parts:
                        match = re.search(r'(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})', part)
                        if match:
                            s_str, e_str = match.groups()
                            sh, sm = map(int, s_str.split(':'))
                            eh, em = map(int, e_str.split(':'))
                            minutes = (eh * 60 + em) - (sh * 60 + sm)
                            total_minutes += minutes
                    
                    shift_hours = total_minutes / 60
                    # Asumimos días de trabajo estándar según el país para la validación "habitualidad"
                    # España: 5 días, Colombia: 6 días 
                    work_days = 5 if agent["country"] == 'ES' else 6
                    projected_hours = shift_hours * work_days
                    
                    # Tolerancia de validación pequeña (0.5h)
                    if abs(projected_hours - contract_hours) < 0.5:
                        forced_shift = sug_shift_str # Match! Forzar este turno
                    elif "ES" in agent['country'] and abs(projected_hours - contract_hours) > 2.0:
                         # Advertencia si la proyección difiere mucho del contrato (solo ES por ahora como ejemplo crítico)
                         validation_msg = f"Advertencia: El turno sugerido '{sug_shift_str}' proyecta {projected_hours}h/semana, pero el contrato es de {contract_hours}h."
                    
                except Exception as e:
                    print(f"Error validando turno sugerido: {e}")

            agent["forced_shift"] = forced_shift
            agent["validation_warning"] = validation_msg
            
            agents_data.append(agent)

        return agents_data

    def _parse_window(self, window_str):
        """
        Parses strings like '09:00-15:00' or '09:00-14:00/15:00-18:00' or '-'
        Returns a list of tuples [(start_time, end_time), ...] or None if Closed/Free
        """
        if pd.isna(window_str):
            return None
        
        s = str(window_str).strip().upper()
        if s in ["-", "LIBRE", "DESCANSO"]:
            return None
            
        intervals = []
        # Split by '/' for split shifts if needed (though initial request focuses on continuous mainly, legacy supports split)
        parts = s.split('/')
        
        for part in parts:
            # Match HH:MM-HH:MM
            match = re.search(r'(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})', part)
            if match:
                start_str, end_str = match.groups()
                intervals.append((start_str, end_str))
        
        return intervals if intervals else None
        
    def parse_absences(self, file_path):
        """
        Parses the Absences/Novelties Excel file.
        Returns a dictionary: { dni: [ {start_date, end_date, type, description}, ... ] }
        """
        try:
            # Similar header logic
            preview = pd.read_excel(file_path, header=None, nrows=20)
            header_idx = 0
            for idx, row in preview.iterrows():
                 # Look for a common column like 'dni' or 'fecha'
                 row_str = [str(x).lower() for x in row.values]
                 row_joined = ' '.join(row_str)
                 if "dni" in row_joined or "fecha inicio" in row_joined or "nombre incidencia" in row_joined:
                     header_idx = idx
                     break
            
            df = pd.read_excel(file_path, header=header_idx)
            df.columns = [str(c).strip() for c in df.columns]
            
            # logger.debug(f"DEBUG Absences: Columns detected: {list(df.columns)}")
            
            absences_map = {}
            
            def safe_date_str(val):
                if pd.isna(val): return None
                if hasattr(val, 'strftime'): return val.strftime('%Y-%m-%d')
                # Try to parse string dates
                try:
                    from dateutil import parser as date_parser
                    parsed = date_parser.parse(str(val), dayfirst=True)
                    return parsed.strftime('%Y-%m-%d')
                except:
                    pass
                return str(val)

            # Find column indices dynamically
            dni_col = None
            start_col = None
            end_col = None
            type_col = None
            
            for c in df.columns:
                cl = c.lower()
                if dni_col is None and ("dni" in cl or "identificacion" in cl or "codigo empleado" in cl):
                    dni_col = c
                if start_col is None and ("fecha inicio incidencia" in cl or "fecha de absentismo" in cl or "fecha inicio" in cl):
                    start_col = c
                if end_col is None and ("fecha fin incidencia" in cl or "fecha fin" in cl):
                    end_col = c
                # Be more specific for type column - avoid "tipo de contrato"
                if type_col is None and ("nombre incidencia" in cl or "nombre absentismo" in cl):
                    type_col = c
            
            # Fallback for type_col only if not found and there's a generic "tipo" that's not "tipo de contrato"
            if type_col is None:
                for c in df.columns:
                    cl = c.lower()
                    if "tipo" in cl and "contrato" not in cl:
                        type_col = c
                        break
            
            # logger.debug(f"DEBUG Absences: dni_col={dni_col}, start_col={start_col}, end_col={end_col}, type_col={type_col}")
            
            if not dni_col or not start_col or not end_col:
                # logger.error("ERROR: Could not identify required columns in absences file.")
                return {}

            for _, row in df.iterrows():
                dni_val = row.get(dni_col)
                
                if not dni_val or pd.isna(dni_val): continue
                dni_val = str(dni_val).strip()
                
                f_ini = row.get(start_col)
                f_fin = row.get(end_col)
                tipo_inc = row.get(type_col) if type_col else "AUS"
                
                if f_ini and f_fin and not pd.isna(f_ini) and not pd.isna(f_fin):
                    start_str = safe_date_str(f_ini)
                    end_str = safe_date_str(f_fin)
                    
                    # Skip invalid dates (except 4000 which is used as a placeholder for unknown end date)
                    if not start_str or not end_str or "1800" in start_str:
                        continue
                    
                    inc_type = str(tipo_inc if not pd.isna(tipo_inc) else "AUS").strip().upper()
                    
                    # DEBUG: Print raw type to debug mapping
                    # logger.debug(f"DEBUG Absence Parsing: dni={dni_val}, raw type='{inc_type}', dates={start_str} to {end_str}")

                    # Map to standard codes

                    code = 'AUS'
                    if 'VAC' in inc_type or 'DISFRUTE' in inc_type or 'COMPENSADO' in inc_type:
                        code = 'VAC'
                    elif 'ENFERMEDAD' in inc_type or 'HOSPITAL' in inc_type or 'MEDIC' in inc_type:
                        code = 'BMED'
                    elif 'BAJA' in inc_type or 'IT' in inc_type or 'INCAPACIDAD' in inc_type:
                        code = 'BMED'
                    elif 'MATERNIDAD' in inc_type or 'PATERNIDAD' in inc_type or 'RIESGO' in inc_type or 'ACCIDENTE' in inc_type or 'PARENTAL' in inc_type:
                        code = 'BMED'
                    elif 'NACIMIENTO' in inc_type or 'QUIRURG' in inc_type or 'MUTUA' in inc_type or 'SALUD' in inc_type or 'REPOSO' in inc_type or 'INTERVENCION' in inc_type:
                        code = 'BMED'
                    elif 'CONSULTA' in inc_type or 'MALESTAR' in inc_type or 'DOLOR' in inc_type or 'GRIPE' in inc_type or 'COVID' in inc_type:
                        code = 'BMED'
                    
                    # DEBUG: Confirm classification
                    # logger.debug(f"DEBUG Absence Mapped: '{inc_type}' -> {code}")

                    if dni_val not in absences_map: 
                        absences_map[dni_val] = []
                    
                    absences_map[dni_val].append({
                        "start_date": start_str,
                        "end_date": end_str,
                        "type": code,
                        "description": inc_type
                    })
            
            # logger.debug(f"DEBUG Absences: Parsed {len(absences_map)} agents with absences.")
            return absences_map
            
        except Exception as e:
            print(f"Error parsing absences file: {e}")
            import traceback
            traceback.print_exc()
            return {}
