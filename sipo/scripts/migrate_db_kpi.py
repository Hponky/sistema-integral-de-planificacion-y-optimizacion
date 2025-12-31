import sys
import os

# Agregar el directorio raíz del proyecto al path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from flask import Flask
from models import db
import sqlalchemy

# Load env or config to get DB URL
# For this task, we assume the app is already configured in the environment.
# We will create a small app context.

def migrate():
    from app import create_app
    app = create_app()
    with app.app_context():
        engine = db.engine
        inspector = sqlalchemy.inspect(engine)
        columns = [c['name'].lower() for c in inspector.get_columns('dimensioning_scenario')]
        
        print(f"Current columns: {columns}")
        
        with engine.connect() as conn:
            if 'calls_forecast' not in columns:
                print("Adding calls_forecast column...")
                try:
                    conn.execute(sqlalchemy.text("ALTER TABLE dimensioning_scenario ADD calls_forecast CLOB"))
                except Exception as e:
                    print(f"Error adding calls_forecast: {e}")
            
            if 'aht_forecast' not in columns:
                print("Adding aht_forecast column...")
                try:
                    conn.execute(sqlalchemy.text("ALTER TABLE dimensioning_scenario ADD aht_forecast CLOB"))
                except Exception as e:
                    print(f"Error adding aht_forecast: {e}")
            
            conn.commit()
            print("Migration completed.")

if __name__ == "__main__":
    migrate()
