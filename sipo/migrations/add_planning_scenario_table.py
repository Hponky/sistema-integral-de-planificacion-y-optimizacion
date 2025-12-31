"""
Migration script to add PlanningScenario table to the database.
Run this script to create the new table for storing planning scenarios (schedule history).
"""

import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db, PlanningScenario
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_planning_scenario_table():
    """Create the PlanningScenario table if it doesn't exist."""
    # Create app instance
    app = create_app('development')
    
    with app.app_context():
        try:
            # Create the table
            db.create_all()
            logger.info("✅ Tabla PlanningScenario creada exitosamente")
            
            # Verify the table was created
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            # Note: SQLAlchemy might convert camelCase to snake_case. 
            # The model is PlanningScenario -> planning_scenario
            
            if 'planning_scenario' in tables:
                logger.info("✅ Verificación exitosa: Tabla 'planning_scenario' existe en la base de datos")
                
                # Show columns
                columns = inspector.get_columns('planning_scenario')
                logger.info(f"📋 Columnas de la tabla planning_scenario:")
                for col in columns:
                    logger.info(f"  - {col['name']}: {col['type']}")
            else:
                logger.warning("⚠️  Tabla 'planning_scenario' no encontrada después de la creación")
                
        except Exception as e:
            logger.error(f"❌ Error creando tabla PlanningScenario: {e}")
            import traceback
            traceback.print_exc()
            raise

if __name__ == '__main__':
    logger.info("🚀 Iniciando migración para agregar tabla PlanningScenario...")
    add_planning_scenario_table()
    logger.info("✨ Migración completada")
