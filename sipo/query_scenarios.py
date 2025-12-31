
from app import create_app
from models import DimensioningScenario
import json
import pandas as pd

app = create_app()

def analyze_scenario(sid):
    with app.app_context():
        from models import db
        s = db.session.get(DimensioningScenario, sid)
        if not s:
            print(f"Scenario {sid} not found")
            return
        
        print(f"\n{'='*20} SCENARIO {sid} {'='*20}")
        print(f"Created: {s.created_at}")
        
        def check_data(blob, name):
            if not blob:
                print(f"{name}: Empty")
                return
            try:
                data = json.loads(blob)
                if isinstance(data, list):
                    df = pd.DataFrame(data)
                    index_cols = ['Fecha', 'Dia', 'Semana', 'Tipo', 'id', 'agent_id', 'total']
                    val_cols = [c for c in df.columns if c not in index_cols and not str(c).startswith('_')]
                    
                    print(f"{name}: {len(df)} rows.")
                    print(f"Columns Map (Sample 5): {val_cols[:5]}")
                    
                    # Numeric sum
                    total = 0
                    for col in val_cols:
                        total += pd.to_numeric(df[col], errors='coerce').sum()
                    print(f"{name} Total Numeric Volume: {total:.2f}")
                    
                    if 'Fecha' in df.columns:
                         dates = sorted(df['Fecha'].unique())
                         print(f"Dates ({len(dates)}): {dates[0]} to {dates[-1]}")
                else:
                    print(f"{name}: Dict with {len(data)} keys")
            except Exception as e:
                print(f"{name}: Error decoding JSON - {e}")

        check_data(s.calls_forecast, "Calls")
        check_data(s.agents_online, "Requirements")
        # check_data(s.aht_forecast, "AHT")
        
        if s.kpis_data:
            k = json.loads(s.kpis_data)
            if 'global' in k:
                print(f"Global KPI NDA: {k['global'].get('nda_global', k['global'].get('sla_global'))}%")

if __name__ == "__main__":
    analyze_scenario(177)
    analyze_scenario(178)
