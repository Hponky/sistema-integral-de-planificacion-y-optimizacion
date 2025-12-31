
import pandas as pd
import io
import datetime

class ExportService:
    def generate_detailed_excel(self, schedule_results, metrics=None, campaign_id_global=None):
        """
        Generates the requested specific Excel format.
        Columns: Centro, Campaign_ID, Id_Legal, Fecha_Entrada, Fecha_Salida, Hora_Entrada, Hora_Salida, ...
        """
        rows = []
        
        # Prepare "susceptible" map from metrics if available
        susceptible_map = {} # (date_str, slot_idx) -> bool
        if metrics and "daily_metrics" in metrics:
             for d_str, d_data in metrics["daily_metrics"].items():
                 for s_idx in d_data.get("susceptible_slots", []):
                     susceptible_map[(d_str, s_idx)] = True
        
        for agent_res in schedule_results:
            agent = agent_res["agent"]
            centro = agent.get("center") or agent.get("centro", "BR") 
            campaign_id = campaign_id_global or agent.get("campaign_id") or agent.get("service") or agent.get("segment", "231001")
            id_legal = agent.get("dni") or agent.get("id", "00000000")
            
            shifts = agent_res["shifts"]
            # Sort by date
            sorted_dates = sorted(shifts.keys())
            
            for date_str in sorted_dates:
                shift = shifts[date_str]
                
                # Format date from YYYY-MM-DD to DD/MM/YYYY
                try:
                    dt_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d')
                    formatted_date = dt_obj.strftime('%d/%m/%Y')
                except:
                    formatted_date = date_str.replace('-', '/')
                
                fecha_entrada = formatted_date
                fecha_salida = formatted_date
                
                # If shift crosses midnight, increment Fecha_Salida
                if shift.get("type") == "WORK" and shift.get("end_min", 0) >= 1440:
                    try:
                        dt_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d')
                        next_day = dt_obj + datetime.timedelta(days=1)
                        fecha_salida = next_day.strftime('%d/%m/%Y')
                    except:
                        pass

                # Default row
                row = {
                    "Centro": centro,
                    "Campaign_ID": campaign_id,
                    "Id_Legal": id_legal,
                    "Fecha_Entrada": fecha_entrada,
                    "Fecha_Salida": fecha_salida,
                }
                
                if shift["type"] == "WORK":
                    start_str = self._min_to_time(shift["start_min"])
                    end_str = self._min_to_time(shift["end_min"])
                    
                    row["Hora_Entrada"] = start_str
                    row["Hora_Salida"] = end_str
                    row["Novedad"] = ""
                    row["Es_Complementario"] = "NO"
                    
                    # Check susceptibility
                    # "El porcentaje de cobertura... mínimo de 25%"
                    # If ANY slot in the shift is susceptible, mark the shift?
                    # Start/End slot
                    s_slot = shift["start_min"] // 30
                    e_slot = shift["end_min"] // 30
                    is_susceptible = False
                    for idx in range(s_slot, e_slot):
                        if susceptible_map.get((date_str, idx)):
                            is_susceptible = True
                            break
                    
                    row["Turno_susceptible_cambio"] = "SI" if is_susceptible else "NO"
                    
                    # Activities
                    breaks = [a for a in shift.get("activities", []) if a["type"] == "BREAK"]
                    pvds = [a for a in shift.get("activities", []) if a["type"] == "PVD"]
                    
                    # Descansos (Breaks)
                    for i, brk in enumerate(breaks):
                        if i >= 2: break # Limit 2 columns provided
                        idx = i + 1
                        row[f"Descanso{idx}_HE"] = self._min_to_time(brk["start"])
                        row[f"Descanso{idx}_HS"] = self._min_to_time(brk["end"])
                        
                    # PVDs
                    for i, pvd in enumerate(pvds):
                        if i >= 10: break
                        idx = i + 1
                        start = self._min_to_time(pvd["start"])
                        end = self._min_to_time(pvd["end"])
                        row[f"PVD{idx}"] = f"{start}-{end}"
                        
                else:
                    # OFF or ABSENCE
                    row["Hora_Entrada"] = "00:00"
                    row["Hora_Salida"] = "23:59" 
                    
                    label = shift.get("label", "FEST")
                    if label == "LIBRE":
                        label = "FEST"
                        
                    row["Novedad"] = label
                    row["Turno_susceptible_cambio"] = "NO"
                    row["Es_Complementario"] = "NO"
                
                rows.append(row)
                
        df = pd.DataFrame(rows)
        
        # Ensure all columns exist and are ordered
        cols_order = [
            "Centro", "Campaign_ID", "Id_Legal", "Fecha_Entrada", "Fecha_Salida", 
            "Hora_Entrada", "Hora_Salida", "Novedad",
            "Formacion1_HE", "Formacion1_HS", "Formacion2_HE", "Formacion2_HS",
            "Descanso1_HE", "Descanso1_HS", "Descanso2_HE", "Descanso2_HS",
            "PVD1", "PVD2", "PVD3", "PVD4", "PVD5", "PVD6", "PVD7", "PVD8", "PVD9", "PVD10",
            "Observacion", "Turno_susceptible_cambio", "Es_Complementario"
        ]
        
        # Add missing columns with empty string
        for col in cols_order:
            if col not in df.columns:
                df[col] = ""
                
        # Reorder and filter
        df = df[cols_order]
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Planificacion')
        
        return output.getvalue()

    def _min_to_time(self, mins):
        h, m = divmod(mins, 60)
        # Handle wraparound 
        h = h % 24
        return f"{h:02d}:{m:02d}"
