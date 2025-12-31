
from app import create_app
from services.planning.data_manager import PlanningDataManager
from services.scheduler.metrics_calculator import DimensioningCalculator
import json
import pandas as pd

app = create_app()

def debug_scenario_loading():
    with app.app_context():
        from models import DimensioningScenario
        scenario = DimensioningScenario.query.order_by(DimensioningScenario.created_at.desc()).first()
        if not scenario:
            print("No scenarios found")
            return
        
        print(f"DEBUGGING SCENARIO ID: {scenario.id}")
        
        dm = PlanningDataManager()
        reqs, calls, aht, params = dm.load_scenario_requirements(scenario.id)
        
        print(f"Dates loaded: {len(calls)} days")
        
        if calls:
            first_date = sorted(list(calls.keys()))[0]
            print(f"\nSample Date: {first_date}")
            c_vals = calls[first_date]
            r_vals = reqs[first_date]
            a_vals = aht.get(first_date, [0.0]*48)
            
            print(f"Calls sum: {sum(c_vals)}")
            print(f"AHT sum: {sum(a_vals)}")
            print(f"Reqs sum: {sum(r_vals)}")
            
            if sum(a_vals) == 0:
                print("WARNING: AHT is all zeros for this date!")
                # Inspect the raw blob for AHT
                try:
                    raw_aht = json.loads(scenario.aht_forecast)
                    if isinstance(raw_aht, list) and len(raw_aht) > 0:
                        print(f"Raw AHT First Row Keys: {list(raw_aht[0].keys())}")
                except: pass

            # Test recalculo manually
            if params.get('nda_objetivo'):
                calc = DimensioningCalculator()
                target = params['nda_objetivo']
                print(f"Testing manual recalc for NDA {target}...")
                test_v = calc.calculate_required_agents(35.0, 300.0, target, 20, is_nda=True)
                print(f"Test calculation (35 calls, 300 AHT): {test_v}")

if __name__ == "__main__":
    debug_scenario_loading()
