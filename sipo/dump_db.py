
import os
import json
import sqlite3

def dump_distributions():
    project_root = os.getcwd()
    db_path = os.path.join(project_root, 'instance', 'sipo_dev.db')
    
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get last 5 distributions
    cursor.execute("SELECT id, segment_id, start_date, end_date, created_at, is_selected FROM forecast_distribution ORDER BY created_at DESC LIMIT 5")
    rows = cursor.fetchall()
    
    print("Recent Distributions:")
    print("-" * 80)
    for row in rows:
        print(f"ID: {row[0]}, Segment: {row[1]}, Dates: {row[2]} to {row[3]}, Created: {row[4]}, Selected: {row[5]}")
        
    if rows:
        last_id = rows[0][0]
        cursor.execute("SELECT distribution_data, time_labels FROM forecast_distribution WHERE id = ?", (last_id,))
        data_row = cursor.fetchone()
        if data_row:
            data = json.loads(data_row[0])
            labels = json.loads(data_row[1])
            print("\nSample Data for ID", last_id)
            print("Time Labels (first 5):", labels[:5])
            dates = sorted(list(data.keys()))
            if dates:
                first_date = dates[0]
                print(f"First Date: {first_date}")
                print(f"Volumes for {first_date}:", {k: data[first_date][k] for k in list(data[first_date].keys())[:5]})
    
    conn.close()

if __name__ == "__main__":
    dump_distributions()
