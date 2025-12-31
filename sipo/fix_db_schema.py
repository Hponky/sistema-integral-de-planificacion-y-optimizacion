from app import create_app
from models import db
from sqlalchemy import text

def fix_schema():
    app = create_app()
    with app.app_context():
        try:
            print("Intentando agregar la columna CURVE_ID a la tabla FORECASTED_DISTRIBUTION...")
            # Oracle syntax for adding a column
            db.session.execute(text('ALTER TABLE FORECASTED_DISTRIBUTION ADD CURVE_ID NUMBER'))
            db.session.commit()
            print("Columna CURVE_ID agregada exitosamente.")
        except Exception as e:
            db.session.rollback()
            if "ORA-01430" in str(e) or "already exists" in str(e).lower():
                print("La columna CURVE_ID ya existe.")
            else:
                print(f"Error al agregar la columna: {e}")

        try:
            print("Intentando agregar la restricción de llave foránea...")
            # Oracle syntax for adding a foreign key
            db.session.execute(text('ALTER TABLE FORECASTED_DISTRIBUTION ADD CONSTRAINT fk_forecast_curve FOREIGN KEY (CURVE_ID) REFERENCES FORECASTING_CURVE(ID)'))
            db.session.commit()
            print("Restricción de llave foránea agregada exitosamente.")
        except Exception as e:
            db.session.rollback()
            if "ORA-02275" in str(e) or "already exists" in str(e).lower():
                print("La restricción de llave foránea ya existe.")
            else:
                print(f"Error al agregar la restricción: {e}")

if __name__ == "__main__":
    fix_schema()
