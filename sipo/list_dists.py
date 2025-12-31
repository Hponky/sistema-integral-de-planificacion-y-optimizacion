
from app import create_app
from models import ForecastedDistribution
import json
import pandas as pd

app = create_app()

def list_all_dists(segment_id):
    with app.app_context():
        from models import db
        dists = ForecastedDistribution.query.filter_by(segment_id=segment_id).order_by(ForecastedDistribution.created_at.desc()).all()
        
        print(f"Found {len(dists)} distributions for Segment {segment_id}")
        for d in dists:
            try:
                data = json.loads(d.distribution_data)
                num_days = len(data)
                print(f"ID: {d.id}, Active: {d.is_selected}, Created: {d.created_at}, Days: {num_days}, Range: {d.start_date} to {d.end_date}")
            except:
                print(f"ID: {d.id}, Error parsing data")

if __name__ == "__main__":
    list_all_dists(1)
