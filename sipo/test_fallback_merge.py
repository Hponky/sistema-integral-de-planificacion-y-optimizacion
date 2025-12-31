
from app import create_app
from services.calculator.calculator_service import CalculatorService
import pandas as pd
import json

app = create_app()

def test_fallback():
    with app.app_context():
        service = CalculatorService()
        segment_id = 1
        start_date = '2025-12-01'
        end_date = '2025-12-31'
        
        print(f"Testing Fallback for Segment {segment_id} ({start_date} to {end_date})")
        df, msg = service.get_fallback_volume(segment_id, start_date, end_date)
        
        if df is not None:
            print(f"Fallback SUCCESS. Rows: {len(df)}")
            print(f"Dates present: {df['Fecha'].unique()}")
            
            # Now simulate merge_data filtering
            config = {'start_date': start_date, 'end_date': end_date}
            from services.calculator.data_processor import DimensioningDataProcessor
            processor = DimensioningDataProcessor()
            
            # We need all_sheets dict
            all_sheets = {'calls': df}
            # Mocking time_labels
            time_labels = [f"{h:02d}:{m:02d}" for h in range(24) for m in [0, 30]]
            
            try:
                # Need to use the private instance since merge_data is not static
                df_merged = processor.merge_data(all_sheets, config, time_labels)
                print(f"Merged Data Rows: {len(df_merged)}")
                if not df_merged.empty:
                    print(f"Merged Dates: {df_merged['Fecha'].min()} to {df_merged['Fecha'].max()}")
            except Exception as e:
                print(f"Merge Error: {e}")
        else:
            print(f"Fallback FAILED: {msg}")

if __name__ == "__main__":
    test_fallback()
