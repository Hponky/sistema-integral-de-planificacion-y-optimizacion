"""
Módulo principal de la aplicación Flask 
Aquí se inicializa la aplicación, la base de datos y se registran los blueprints.
"""

import os
from flask import Flask, jsonify, request
from flask_migrate import Migrate
from flask_cors import CORS
from config import config as app_config
from models import db

# Inicializar Oracle Client para modo Thick (requerido para password verifiers antiguos)
try:
    import oracledb
    lib_dir = r"C:\oracle\instantclient_19_25"
    if os.path.exists(lib_dir):
        oracledb.init_oracle_client(lib_dir=lib_dir)
        print(f"[INFO] Oracle Client inicializado desde: {lib_dir}")
    else:
        # Fallback: intentar sin ruta específica (por si está en PATH)
        oracledb.init_oracle_client()
        print("[INFO] Oracle Client inicializado (ubicación por defecto)")
except Exception as e:
    # Si falla la inicialización, continuar (puede que no se esté usando Oracle)
    print(f"[WARN] No se pudo inicializar Oracle Client: {e}")
    print("[INFO] Si usa Oracle DB, asegúrese de tener Oracle Instant Client instalado")

migrate = Migrate()

def create_app(config_name='default'):
    """
    Crea y configura una instancia de la aplicación Flask.

    Args:
        config_name (str): El nombre de la configuración a cargar (e.g., 'development', 'production', 'testing').

    Returns:
        Flask: La instancia de la aplicación Flask configurada.
    """
    app = Flask(__name__, instance_relative_config=True)
    
    # Cargar configuración desde el objeto de configuración
    app.config.from_object(app_config[config_name])
    
    # Configurar la URI de la base de datos para usar siempre la ruta correcta
    # La base de datos correcta está en instance/sipo_dev.db en la raíz del proyecto
    if app.config.get('SQLALCHEMY_DATABASE_URI') is None:
        # Obtener la ruta raíz del proyecto de forma consistente
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(project_root, 'instance', 'sipo_dev.db')
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
    
    # Configurar CORS para permitir requests desde el frontend
    CORS(app,
         resources={r"/*": {"origins": app.config.get('CORS_ORIGINS', ['http://localhost:4200', 'http://127.0.0.1:4200'])}},
         supports_credentials=True,
         allow_headers=['Content-Type', 'Authorization', 'X-Requested-With'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
         expose_headers=['Content-Type', 'Authorization'],
         vary_header=False)

    # Inicializar extensiones
    db.init_app(app)
    migrate.init_app(app, db)

    # Configurar la carpeta de plantillas explícitamente
    # Esto es importante si la estructura de carpetas es diferente a la predeterminada de Flask
    app.template_folder = os.path.join(app.root_path, 'templates')
    app.static_folder = os.path.join(app.root_path, 'static')

    # Registrar Blueprints
    # Importar aquí para evitar importaciones circulares
    # from routes.auth import auth_bp # Removed as auth is now handled externally
    # from routes.admin import admin_bp # TODO: Descomentar cuando se cree el blueprint de admin
    from routes.calculator import calculator_bp
    from routes.forecasting_routes import forecasting_bp
    # from routes.scheduling import scheduling_bp # TODO: Descomentar cuando se cree el blueprint de scheduling
    # from routes.summary import summary_bp # TODO: Descomentar cuando se cree el blueprint de summary

    # app.register_blueprint(auth_bp) # Removed
    # app.register_blueprint(admin_bp) # TODO: Descomentar cuando se cree el blueprint de admin
    app.register_blueprint(calculator_bp)
    app.register_blueprint(forecasting_bp)
    # app.register_blueprint(scheduling_bp) # TODO: Descomentar cuando se cree el blueprint de scheduling
    # app.register_blueprint(summary_bp) # TODO: Descomentar cuando se cree el blueprint de summary
    
    from routes.auth_routes import auth_bp
    app.register_blueprint(auth_bp)

    from routes.planning_routes import planning_bp
    app.register_blueprint(planning_bp)

    # Agregar endpoint de health check
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({"status": "healthy", "message": "SIPO backend is running"})

    # Manejar solicitudes OPTIONS para CORS
    # Manejador after_request eliminado ya que Flask-CORS se encarga de los headers
    # @app.after_request
    # def after_request(response):
    #     return response

    return app

if __name__ == '__main__':
    app = create_app('development')
    app.run(debug=True, host='0.0.0.0', port=5000)
