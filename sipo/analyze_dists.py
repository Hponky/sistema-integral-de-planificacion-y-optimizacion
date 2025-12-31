
from app import create_app
from models import ForecastedDistribution
import json
import pandas as pd

app = create_app()

def analyze_distributions(segment_id):
    with app.app_context():
        from models import db
        dists = ForecastedDistribution.query.filter_by(segment_id=segment_id).order_by(ForecastedDistribution.created_at.desc()).limit(5).all()
        
        for d in dists:
            print(f"\n{'='*20} DISTRIBUTION {d.id} {'='*20}")
            print(f"Created: {d.created_at}")
            print(f"Dates: {d.start_date} to {d.end_date}")
            
            try:
                data = json.loads(d.distribution_data)
                dates = sorted(list(data.keys()))
                print(f"Number of dates in JSON: {len(dates)}")
                if dates:
                    print(f"Actual dates in JSON: {dates[0]} to {dates[-1]}")
                    first_date = dates[0]
                    cols = list(data[first_date].keys())
                    print(f"Columns Map (Sample 5): {cols[:5]}")
                    
                    # Numeric sum for first date
                    first_day_sum = sum(pd.to_numeric([data[first_date][k] for k in cols if ':' in k], errors='coerce'))
                    print(f"First day total volume: {first_day_sum:.2f}")
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    analyze_distributions(1)
