"""
Script para inicializar la base de datos con datos de prueba.
Ejecutar con: python sipo/init_db.py
"""

import os
import sys
import datetime

# Agregar el directorio raíz del proyecto al path para importar módulos
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from sipo.app import create_app, db
from sipo.models import User, Campaign, Segment

def init_database():
    """Inicializa la base de datos con datos de prueba"""
    app = create_app('development')
    
    # Verificar y crear directorio instance antes de crear la base de datos
    # Usar la misma lógica que en app.py para consistencia
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    instance_path = os.path.join(project_root, 'instance')
    os.makedirs(instance_path, exist_ok=True)
    print(f"[OK] Directorio instance verificado: {instance_path}")
    
    with app.app_context():
        print("Creando tablas de base de datos...")
        try:
            db.create_all()
            print("[OK] Tablas creadas exitosamente")
        except Exception as e:
            print(f"[ERROR] No se pudieron crear las tablas: {e}")
            print(f"[INFO] Verificando directorio instance: {instance_path}")
            print(f"[INFO] Permisos de escritura: {os.access(instance_path, os.W_OK)}")
            return
        
        # Verificar si ya existen datos
        try:
            if User.query.first() is None:
                print("Poblando base de datos con datos de prueba...")
                
                # Crear usuario admin
                admin_user = User(
                    username='admin',
                    role='admin'
                )
                admin_user.set_password('password123')
                db.session.add(admin_user)
                print("[OK] Usuario admin creado (username: admin, password: password123)")
                
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
                
                # Asignar campañas al usuario admin
                admin_user.campaigns.extend([campaign1, campaign2])
                print("[OK] Campañas asignadas al usuario admin")
                
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
        print(f"Usuarios: {User.query.count()}")
        print(f"Campañas: {Campaign.query.count()}")
        print(f"Segmentos: {Segment.query.count()}")
        print("-----------------------------------")
        
        print("\n[OK] Base de datos inicializada correctamente")

if __name__ == '__main__':
    init_database()