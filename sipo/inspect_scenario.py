
from app import create_app
from models import DimensioningScenario
import json
import pandas as pd

app = create_app()

def inspect_last_scenario():
    with app.app_context():
        scenario = DimensioningScenario.query.order_by(DimensioningScenario.created_at.desc()).first()
        if not scenario:
            print("No scenarios found")
            return
        
        print(f"Scenario ID: {scenario.id}")
        
        def check_blob(blob_str, name):
            if not blob_str:
                print(f"{name}: EMPTY")
                return
            data = json.loads(blob_str)
            if isinstance(data, list) and len(data) > 0:
                print(f"{name}: {len(data)} rows. First row keys: {list(data[0].keys())}")
                # Count time keys (keys with :)
                time_keys = [k for k in data[0].keys() if ':' in str(k)]
                print(f"    - Time keys found: {len(time_keys)}")
            else:
                print(f"{name}: {type(data)} with {len(data)} elements")

        check_blob(scenario.calls_forecast, "Calls")
        check_blob(scenario.agents_online, "Effective Agents")

if __name__ == "__main__":
    inspect_last_scenario()
