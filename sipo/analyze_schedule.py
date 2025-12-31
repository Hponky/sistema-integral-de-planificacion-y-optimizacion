
import pandas as pd
import os
import re

schedule_path = r"c:\Users\hagudelor\VSCode\em_sipo\horarios (3).xlsx"
agents_path = r"c:\Users\hagudelor\VSCode\em_sipo\Plantilla_Agentes_Leroy.xlsx"

print(f"Analyzing {schedule_path}...")

try:
    # 1. READ AGENTS (CONTRACTS)
    print("Reading Agents file...")
    prev = pd.read_excel(agents_path, header=None, nrows=20)
    h_idx = 0
    for idx, row in prev.iterrows():
        rstr = [str(v).lower() for v in row.values]
        if "nombre_completo" in rstr or "nombre" in rstr:
            h_idx = idx
            break
            
    df_agents = pd.read_excel(agents_path, header=h_idx)
    df_agents.columns = [str(c).strip().lower() for c in df_agents.columns]
    
    # Robust column detection for agents
    id_col = next((c for c in df_agents.columns if any(x in c for x in ["identificacion", "id", "dni", "nif", "documento", "identificaci"])), None)
    contract_col = next((c for c in df_agents.columns if any(x in c for x in ["contrato", "horas", "jornada"])), None)
    
    contracts = {}
    if id_col and contract_col:
        for _, row in df_agents.iterrows():
             if pd.isna(row[id_col]): continue
             uid = str(row[id_col]).strip().upper()
             # Normalize IDs that might be float-strings like "123.0"
             if uid.endswith('.0'): uid = uid[:-2]
             
             try:
                 val = row[contract_col]
                 if isinstance(val, str) and ':' in val:
                     h = float(val.split(':')[0])
                 else:
                     h = float(str(val).replace(',', '.'))
                 contracts[uid] = h
             except:
                 pass
    print(f"Loaded {len(contracts)} contracts.")


    # 2. READ SCHEDULE
    print("Reading Schedule file...")
    df_sched = pd.read_excel(schedule_path)
    # Don't strip too much yet, just for detection
    orig_cols = list(df_sched.columns)
    
    # Improved ID column detection for schedule
    sched_id_col = next((c for c in orig_cols if any(x in c.lower() for x in ["identificaci", "id", "dni", "agent_id"])), None)
    # Improved total hours column detection (Horas Per. = Horas Periodo)
    total_col = next((c for c in orig_cols if "horas per" in c.lower() or ("total" in c.lower() and "horas" in c.lower())), None)
    
    print(f"Detected columns - ID: {sched_id_col}, Total: {total_col}")
    
    violations = []
    
    if sched_id_col and total_col:
        for _, row in df_sched.iterrows():
            uid = str(row[sched_id_col]).strip().upper()
            if uid.endswith('.0'): uid = uid[:-2]
            
            if uid in contracts:
                contract_target = contracts[uid]
                # If we are analyzing a schedule for a period (e.g. 15 days), 
                # we need to know what the target SHOULD be for those 15 days.
                # Usually contract is weekly hours.
                
                actual = 0
                try:
                    actual = float(str(row[total_col]).replace(',', '.'))
                except:
                    continue
                
                # We need to know the number of days in the schedule to calculate proportional target
                # Let's count columns that start with "día"
                day_cols = [c for c in orig_cols if "día" in c.lower() or "dia" in c.lower()]
                num_days = len(day_cols)
                
                # Weekly hours to Period hours (Target = weekly_hours / 7 * num_days) - Wait, usually it's weekly / 5 * worked_days?
                # Actually, the scheduler uses monthly_target_min which is proportional.
                # Let's see what the "contrato" column in the SCHEDULE says.
                # Calculate Period Target based on Weekly Contract and Number of Days
                if num_days > 0:
                    period_target = (contract_target / 7.0) * num_days
                else:
                    period_target = contract_target # Fallback if no days detected
                
                # Strict check
                if actual > period_target + 0.01:
                    violations.append({
                        "id": uid,
                        "name": row.get('agente', 'Unknown'),
                        "target": period_target,
                        "actual": actual,
                        "diff": actual - period_target
                    })

    if violations:
        print(f"\nCRITICAL: Found {len(violations)} agents working MORE than contract!")
        print(f"{'AGENT':<25} | {'TARGET':<10} | {'ACTUAL':<10} | {'DIFF':<10}")
        print("-" * 65)
        for v in violations:
            print(f"{str(v['name'])[:24]:<25} | {v['target']:<10.2f} | {v['actual']:<10.2f} | +{v['diff']:.2f}")
    else:
        print("\nSUCCESS: All agents are within contract limits.")

except Exception as e:
    print(f"Analysis Error: {e}")
    import traceback
    traceback.print_exc()
