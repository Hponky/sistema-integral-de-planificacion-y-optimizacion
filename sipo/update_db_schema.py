import sqlite3
import os

# Path inferred from app.py logic
db_path = os.path.join(os.getcwd(), 'instance', 'sipo_dev.db')
print(f"Connecting to database at: {db_path}")

try:
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Check if column exists
    c.execute("PRAGMA table_info(forecasted_distribution)")
    columns = [info[1] for info in c.fetchall()]
    
    if 'is_selected' in columns:
        print("Column 'is_selected' already exists.")
    else:
        print("Adding column 'is_selected'...")
        c.execute("ALTER TABLE forecasted_distribution ADD COLUMN is_selected BOOLEAN DEFAULT 0")
        conn.commit()
        print("Column added successfully.")
        
except Exception as e:
    print(f"Error: {e}")
finally:
    if 'conn' in locals():
        conn.close()
