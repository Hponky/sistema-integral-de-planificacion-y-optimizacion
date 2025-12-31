import os
import sys

# Agregar el directorio raíz del proyecto al path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app import create_app, db
from sqlalchemy import text

app = create_app()

def update_schema():
    with app.app_context():
        print("Intentando actualizar la tabla planning_scenario...")
        
        # Check if columns exist to avoid duplicate error, or catch exception
        try:
            # Oracle SQL to add columns
            # Note: Oracle handles case sensitivity. Usually tables are UPPERCASE but SQLAlchemy might quote them lowercase.
            # The error message showed "PLANNING_SCENARIO" (quoted).
            
            # Adding is_temporary
            try:
                print("Agregando columna is_temporary...")
                db.session.execute(text("ALTER TABLE planning_scenario ADD is_temporary NUMBER(1) DEFAULT 0"))
                print("Columna is_temporary agregada.")
            except Exception as e:
                print(f"Error agregando is_temporary (puede que ya exista): {e}")

            # Adding expires_at
            try:
                print("Agregando columna expires_at...")
                db.session.execute(text("ALTER TABLE planning_scenario ADD expires_at TIMESTAMP"))
                print("Columna expires_at agregada.")
            except Exception as e:
                print(f"Error agregando expires_at (puede que ya exista): {e}")

            db.session.commit()
            print("Actualización de esquema finalizada.")
            
        except Exception as e:
            print(f"Error general en actualización: {e}")
            db.session.rollback()

if __name__ == "__main__":
    update_schema()
