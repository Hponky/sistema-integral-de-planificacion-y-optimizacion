
from app import create_app
from models import DimensioningScenario
import json

app = create_app()

def inspect_aht():
    with app.app_context():
        scenario = DimensioningScenario.query.order_by(DimensioningScenario.created_at.desc()).first()
        if not scenario: return
        
        data = json.loads(scenario.aht_forecast)
        if isinstance(data, list) and len(data) > 0:
            row = data[0]
            print(f"Scenario {scenario.id} - Date: {row.get('Fecha')}")
            # Filter time keys and sort them
            time_keys = sorted([k for k in row.keys() if ':' in str(k)])
            for k in time_keys:
                if '08:' in k or '09:' in k:
                    print(f"  Key '{k}': Value type={type(row[k])}, Value={row[k]}")

if __name__ == "__main__":
    inspect_aht()
