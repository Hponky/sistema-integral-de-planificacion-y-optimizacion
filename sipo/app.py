"""
Módulo principal de la aplicación Flask SIPO.
Aquí se inicializa la aplicación, la base de datos y se registran los blueprints.
"""

import os
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from sipo.config import config as app_config

db = SQLAlchemy()
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
    
    # Configurar CORS para permitir requests desde el frontend
    CORS(app,
         resources={r"/*": {"origins": app.config.get('CORS_ORIGINS', ['http://localhost:4200', 'http://127.0.0.1:4200'])}},
         supports_credentials=True,
         allow_headers=['Content-Type', 'Authorization'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
    
    # Cargar configuración desde el objeto de configuración
    app.config.from_object(app_config[config_name])

    # Inicializar extensiones
    db.init_app(app)
    migrate.init_app(app, db)

    # Configurar la carpeta de plantillas explícitamente
    # Esto es importante si la estructura de carpetas es diferente a la predeterminada de Flask
    app.template_folder = os.path.join(app.root_path, 'templates')
    app.static_folder = os.path.join(app.root_path, 'static')

    # Registrar Blueprints
    # Importar aquí para evitar importaciones circulares
    from sipo.routes.auth import auth_bp
    # from sipo.routes.admin import admin_bp # TODO: Descomentar cuando se cree el blueprint de admin
    from sipo.routes.calculator import calculator_bp
    # from sipo.routes.forecasting import forecasting_bp # TODO: Descomentar cuando se cree el blueprint de forecasting
    # from sipo.routes.scheduling import scheduling_bp # TODO: Descomentar cuando se cree el blueprint de scheduling
    # from sipo.routes.summary import summary_bp # TODO: Descomentar cuando se cree el blueprint de summary

    app.register_blueprint(auth_bp)
    # app.register_blueprint(admin_bp) # TODO: Descomentar cuando se cree el blueprint de admin
    app.register_blueprint(calculator_bp)
    # app.register_blueprint(forecasting_bp) # TODO: Descomentar cuando se cree el blueprint de forecasting
    # app.register_blueprint(scheduling_bp) # TODO: Descomentar cuando se cree el blueprint de scheduling
    # app.register_blueprint(summary_bp) # TODO: Descomentar cuando se cree el blueprint de summary

    # Agregar endpoint de health check
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({"status": "healthy", "message": "SIPO backend is running"})

    # Manejar solicitudes OPTIONS para CORS
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:4200')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response

    return app

if __name__ == '__main__':
    app = create_app('development')
    app.run(debug=True, host='0.0.0.0', port=5000)
