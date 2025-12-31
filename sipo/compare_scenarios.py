
import os
import json
import sqlite3
import pandas as pd

def compare_scenarios(id1, id2):
    project_root = os.getcwd()
    db_path = os.path.join(project_root, 'instance', 'sipo_dev.db')
    
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    for sid in [id1, id2]:
        print(f"\n{'='*20} SCENARIO {sid} {'='*20}")
        cursor.execute("SELECT id, name, parameters, calls_forecast, agents_online, aht_forecast FROM dimensioning_scenarios WHERE id = ?", (sid,))
        scenario = cursor.fetchone()
        
        if not scenario:
            print(f"Scenario {sid} not found.")
            continue
            
        params = json.loads(scenario[2])
        calls = json.loads(scenario[3])
        reqs = json.loads(scenario[4])
        aht = json.loads(scenario[5])
        
        print(f"Name: {scenario[1]}")
        print(f"Params: {params}")
        
        # Analyze Calls
        if isinstance(calls, list):
            df_calls = pd.DataFrame(calls)
            print(f"Calls (List): {len(df_calls)} rows. Columns: {df_calls.columns.tolist()[:10]}...")
            if 'Fecha' in df_calls.columns:
                print(f"Dates in Calls: {df_calls['Fecha'].unique()[:5]}")
        
        # Analyze Reqs
        if isinstance(reqs, list):
            df_reqs = pd.DataFrame(reqs)
            print(f"Reqs (List): {len(df_reqs)} rows.")
            
        # Analyze AHT
        if isinstance(aht, list):
            df_aht = pd.DataFrame(aht)
            print(f"AHT (List): {len(df_aht)} rows.")

        # Check total calls
        total_vol = 0
        if isinstance(calls, list):
            # Sum columns that look like times (HH:MM)
            time_cols = [c for c in df_calls.columns if ':' in str(c)]
            total_vol = df_calls[time_cols].sum().sum()
        print(f"TOTAL CALL VOLUME: {total_vol:.2f}")

    conn.close()

if __name__ == "__main__":
    compare_scenarios(177, 178)
