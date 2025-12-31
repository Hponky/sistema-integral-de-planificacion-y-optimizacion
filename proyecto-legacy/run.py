# run.py

from app import create_app, db
from app.models import User, Campaign, Segment, SchedulingRule, BreakRule
from werkzeug.security import generate_password_hash
import click

# Creamos la instancia de la aplicación usando nuestra fábrica
app = create_app()

# ==============================================================================
# Definición de Comandos de Línea de Comandos (CLI)
# ==============================================================================

@click.group()
def db_cli():
    """Comandos personalizados para la gestión de la base de datos."""
    pass

@db_cli.command('create-all')
def db_create_all():
    """Crea todas las tablas de la base de datos."""
    with app.app_context():
        db.create_all()
        print("Base de datos y tablas creadas con éxito.")

@db_cli.command('seed')
def db_seed():
    """Puebla la base de datos con datos iniciales (admin, campañas, etc.)."""
    with app.app_context():
        # Crear usuario admin si no existe
        if not User.query.filter_by(username='admin').first():
            admin_user = User(username='admin', password_hash=generate_password_hash('password123', method='pbkdf2:sha256'), role='admin')
            db.session.add(admin_user)
            print("Usuario 'admin' creado con contraseña 'password123'.")
        
        # Crear campañas y segmentos de ejemplo si no existen
        if not Campaign.query.first():
           c1 = Campaign(name='Banco de Bogotá', country='Colombia')
           c2 = Campaign(name='Ventas España', country='España')
           s1 = Segment(name='SAC', campaign=c1, lunes_apertura='08:00', lunes_cierre='22:00', martes_apertura='08:00', martes_cierre='22:00', miercoles_apertura='08:00', miercoles_cierre='22:00', jueves_apertura='08:00', jueves_cierre='22:00', viernes_apertura='08:00', viernes_cierre='22:00', sabado_apertura='09:00', sabado_cierre='18:00', domingo_apertura='09:00', domingo_cierre='15:00')
           s2 = Segment(name='Facturación', campaign=c1)
           s3 = Segment(name='General', campaign=c2)
           db.session.add_all([c1, c2, s1, s2, s3])
           print("Campañas y Segmentos de ejemplo creados.")
        
        db.session.commit()
        print("Base de datos poblada con datos iniciales.")

@db_cli.command('seed-breaks')
def db_seed_breaks():
    """Puebla la BD con reglas de descanso para Colombia y España."""
    with app.app_context():
        BreakRule.query.delete()
        colombia_rules = [ BreakRule(name=f'COL {h} Horas', country='Colombia', min_shift_hours=h, max_shift_hours=h+0.99, break_duration_minutes=d) for h, d in zip(range(4, 11), [10, 15, 20, 25, 30, 35, 40]) ]
        spain_rules = [
            BreakRule(name='ESP 4-6 Horas', country='España', min_shift_hours=4.0, max_shift_hours=6.99, break_duration_minutes=10, pvd_minutes_per_hour=5, number_of_pvds=2),
            BreakRule(name='ESP 7 Horas', country='España', min_shift_hours=7.0, max_shift_hours=7.99, break_duration_minutes=20, pvd_minutes_per_hour=5, number_of_pvds=3),
            BreakRule(name='ESP 8-10 Horas', country='España', min_shift_hours=8.0, max_shift_hours=10.99, break_duration_minutes=30, pvd_minutes_per_hour=5, number_of_pvds=4),
        ]
        db.session.add_all(colombia_rules)
        db.session.add_all(spain_rules)
        db.session.commit()
        print("Reglas de descanso para Colombia y España creadas con éxito.")

# Registramos nuestro grupo de comandos en la aplicación Flask
app.cli.add_command(db_cli, 'db-custom')


# ==============================================================================
# Punto de Entrada para Ejecutar la Aplicación
# ==============================================================================

if __name__ == '__main__':
    # host='0.0.0.0' permite que la aplicación sea accesible desde otras máquinas en la red.
    # debug=True es útil para desarrollo, pero debe ser False en producción.
    app.run(host='0.0.0.0', port=5000, debug=True)