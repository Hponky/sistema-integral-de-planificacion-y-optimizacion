"""
Script para inicializar la base de datos con datos de prueba.
Ejecutar con: python sipo/init_db.py
"""

import os
import sys
import datetime
from sqlalchemy import text
import oracledb

# Agregar el directorio raíz del proyecto al path para importar módulos
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Intentar habilitar el modo Thick de oracledb
# Nota: Thick mode es necesario para conectarse a bases de datos Oracle con
# password verifiers antiguos (10G). Si falla, se usará Thin mode.
THICK_MODE_ENABLED = False
try:
    # Intentar inicializar especificando la ruta de Oracle Instant Client
    # Esto es necesario si no está en el PATH o si hay conflictos
    lib_dir = r"C:\oracle\instantclient_19_25"
    if os.path.exists(lib_dir):
        oracledb.init_oracle_client(lib_dir=lib_dir)
        print(f"[INFO] Oracle Client inicializado desde: {lib_dir}")
    else:
        # Fallback: intentar sin ruta específica (por si está en PATH)
        oracledb.init_oracle_client()
        print("[INFO] Oracle Client inicializado (ubicación por defecto)")
        
    THICK_MODE_ENABLED = True
    print("[INFO] Oracle Client inicializado exitosamente (Thick mode)")
    print("[INFO] Usando Thick mode - Compatible con todos los tipos de password verifiers")
except Exception as e:
    print(f"[WARN] No se pudo inicializar Oracle Client (Thick mode): {e}")
    print("[INFO] Se intentará usar Thin mode")
    print("[WARN] Thin mode NO soporta password verifiers antiguos (10G)")
    print("")
    print("=" * 80)
    print("Si obtiene error DPY-3015 (password verifier not supported), tiene 2 opciones:")
    print("")
    print("OPCIÓN 1: Instalar Oracle Instant Client (Recomendado)")
    print("  1. Descargar de: https://www.oracle.com/database/technologies/instant-client/downloads.html")
    print("  2. Descargar 'Basic Package' para Windows x64")
    print("  3. Extraer en C:\\oracle\\instantclient_XX_X")
    print("  4. Agregar al PATH del sistema")
    print("")
    print("OPCIÓN 2: Actualizar password del usuario en Oracle")
    print("  Solicitar al DBA ejecutar: ALTER USER WFM_SIPO IDENTIFIED BY <nueva_password>;")
    print("  Esto regenerará el password verifier a una versión moderna (11G+)")
    print("=" * 80)
    print("")

from app import create_app, db
from models import Campaign, Segment

def check_connection(app):
    """Verifica la conexión a la base de datos"""
    print("Verificando conexión a la base de datos...")
    try:
        with app.app_context():
            # Intentar una consulta simple
            # 'SELECT 1 FROM DUAL' es estándar en Oracle
            db.session.execute(text('SELECT 1 FROM DUAL'))
            print("[OK] Conexión a Oracle exitosa")
            return True
    except Exception as e:
        print(f"[ERROR] Falló la conexión a la base de datos: {e}")
        
        # Proporcionar ayuda específica para errores comunes
        error_str = str(e)
        if "DPY-3015" in error_str:
            print("")
            print("=" * 80)
            print("ERROR: Password verifier no soportado (DPY-3015)")
            print("")
            if not THICK_MODE_ENABLED:
                print("El usuario de Oracle está usando un password verifier antiguo (10G)")
                print("que NO es compatible con Thin mode.")
                print("")
                print("SOLUCIÓN: Instalar Oracle Instant Client para usar Thick mode")
                print("Ver instrucciones arriba.")
            print("=" * 80)
        elif "DPI-1047" in error_str:
            print("")
            print("=" * 80)
            print("ERROR: Oracle Client no encontrado (DPI-1047)")
            print("")
            print("Instalar Oracle Instant Client:")
            print("1. https://www.oracle.com/database/technologies/instant-client/downloads.html")
            print("2. Descargar 'Basic Package' para Windows x64")
            print("3. Extraer y agregar al PATH")
            print("=" * 80)
        
        return False

def drop_all_tables_safely(app):
    """Elimina todas las tablas y secuencias de forma segura, manejando restricciones de Oracle"""
    with app.app_context():
        print("Eliminando tablas y secuencias existentes...")
        
        # Lista de tablas en orden de dependencias (de más dependiente a menos)
        tables = [
            'schedule',
            'staffing_result',
            'dimensioning_scenario',
            'actuals_data',
            'agent',
            'segment',
            'campaign',
            'break_rule',
            'workday_rule',
            'scheduling_rule',
            'user_campaign_permission',
            '"user"'  # user es palabra reservada en Oracle
        ]
        
        # Lista de secuencias
        sequences = [
            'user_id_seq',
            'campaign_id_seq',
            'segment_id_seq',
            'dim_scenario_id_seq',
            'staffing_result_id_seq',
            'actuals_data_id_seq',
            'agent_id_seq',
            'scheduling_rule_id_seq',
            'workday_rule_id_seq',
            'schedule_id_seq',
            'break_rule_id_seq'
        ]
        
        # Eliminar tablas
        for table in tables:
            try:
                db.session.execute(text(f'DROP TABLE {table} CASCADE CONSTRAINTS'))
                db.session.commit()
            except Exception as e:
                if 'ORA-00942' in str(e):  # Tabla no existe
                    pass  # Ignorar si la tabla no existe
                else:
                    print(f"[WARN] Error al eliminar tabla {table}: {e}")
                db.session.rollback()
        
        # Eliminar secuencias
        for seq in sequences:
            try:
                db.session.execute(text(f'DROP SEQUENCE {seq}'))
                db.session.commit()
            except Exception as e:
                if 'ORA-02289' in str(e):  # Secuencia no existe
                    pass  # Ignorar si la secuencia no existe
                else:
                    print(f"[WARN] Error al eliminar secuencia {seq}: {e}")
                db.session.rollback()
        
        print("[OK] Tablas y secuencias eliminadas")

def init_database():
    """Inicializa la base de datos con datos de prueba"""
    app = create_app('development')
    
    # Verificar conexión antes de proceder
    if not check_connection(app):
        print("\nAbortando inicialización debido a error de conexión.")
        return

    # Verificar y crear directorio instance antes de crear la base de datos
    # Usar la misma lógica que en app.py para consistencia
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    instance_path = os.path.join(project_root, 'instance')
    os.makedirs(instance_path, exist_ok=True)
    print(f"[OK] Directorio instance verificado: {instance_path}")
    
    with app.app_context():
        print("Creando tablas de base de datos...")
        try:
            # Eliminar tablas existentes de forma segura
            drop_all_tables_safely(app)
            
            # Crear todas las tablas
            db.create_all()
            print("[OK] Tablas creadas exitosamente")
        except Exception as e:
            print(f"[ERROR] No se pudieron crear las tablas: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # Verificar si ya existen datos
        try:
            if Campaign.query.first() is None:
                print("Poblando base de datos con datos de prueba...")
                
                # Crear campañas de ejemplo
                campaign1 = Campaign(
                    name='Banco de Bogotá',
                    country='Colombia',
                    code='BBOG'
                )
                
                campaign2 = Campaign(
                    name='Ventas España',
                    country='España',
                    code='VESP'
                )
                
                db.session.add_all([campaign1, campaign2])
                print("[OK] Campañas de ejemplo creadas")
                
                # Crear segmentos de ejemplo
                segment1 = Segment(
                    name='SAC',
                    campaign=campaign1,
                    lunes_apertura='08:00', lunes_cierre='22:00',
                    martes_apertura='08:00', martes_cierre='22:00',
                    miercoles_apertura='08:00', miercoles_cierre='22:00',
                    jueves_apertura='08:00', jueves_cierre='22:00',
                    viernes_apertura='08:00', viernes_cierre='22:00',
                    sabado_apertura='09:00', sabado_cierre='18:00',
                    domingo_apertura='09:00', domingo_cierre='15:00',
                    weekend_policy='REQUIRE_ONE_DAY_OFF',
                    min_full_weekends_off_per_month=2
                )
                
                segment2 = Segment(
                    name='Facturación',
                    campaign=campaign1,
                    lunes_apertura='08:00', lunes_cierre='18:00',
                    martes_apertura='08:00', martes_cierre='18:00',
                    miercoles_apertura='08:00', miercoles_cierre='18:00',
                    jueves_apertura='08:00', jueves_cierre='18:00',
                    viernes_apertura='08:00', viernes_cierre='18:00',
                    sabado_apertura='09:00', sabado_cierre='14:00',
                    domingo_apertura='09:00', domingo_cierre='14:00',
                    weekend_policy='FLEXIBLE',
                    min_full_weekends_off_per_month=1
                )
                
                segment3 = Segment(
                    name='General',
                    campaign=campaign2,
                    lunes_apertura='09:00', lunes_cierre='20:00',
                    martes_apertura='09:00', martes_cierre='20:00',
                    miercoles_apertura='09:00', miercoles_cierre='20:00',
                    jueves_apertura='09:00', jueves_cierre='20:00',
                    viernes_apertura='09:00', viernes_cierre='20:00',
                    sabado_apertura='10:00', sabado_cierre='16:00',
                    domingo_apertura='10:00', domingo_cierre='16:00',
                    weekend_policy='REQUIRE_ONE_DAY_OFF',
                    min_full_weekends_off_per_month=2
                )
                
                db.session.add_all([segment1, segment2, segment3])
                print("[OK] Segmentos de ejemplo creados")
                
                # Commit de todos los cambios
                db.session.commit()
                print("[OK] Base de datos poblada exitosamente")
            else:
                print("[OK] La base de datos ya contiene datos, no se requiere población inicial")
        except Exception as e:
            print(f"[ERROR] Error al poblar la base de datos: {e}")
            db.session.rollback()
            return
        
        # Mostrar resumen
        print("\n--- RESUMEN DE LA BASE DE DATOS ---")
        try:
            print(f"Campañas: {Campaign.query.count()}")
            print(f"Segmentos: {Segment.query.count()}")
        except Exception as e:
            print(f"Error al consultar resumen: {e}")
        print("-----------------------------------")
        
        print("\n[OK] Base de datos inicializada correctamente")

if __name__ == '__main__':
    init_database()