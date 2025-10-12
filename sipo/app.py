"""
Módulo principal de la aplicación Flask SIPO.
Aquí se inicializa la aplicación, la base de datos y se registran los blueprints.
"""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
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

    return app

if __name__ == '__main__':
    app = create_app('development')
    app.run(debug=True, host='0.0.0.0', port=5000)
