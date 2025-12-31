# app/__init__.py

import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# 1. Inicializamos las extensiones globalmente
db = SQLAlchemy()
migrate = Migrate()

def create_app():
    """
    Crea y configura una instancia de la aplicación Flask.
    Este es el patrón Application Factory.
    """
    
    # 2. Lógica para determinar rutas en desarrollo vs. ejecutable .exe
    if getattr(sys, 'frozen', False):
        # Si la aplicación está 'congelada' (es un .exe de PyInstaller)
        BASE_DIR = os.path.dirname(sys.executable)
        template_folder = os.path.join(BASE_DIR, 'templates')
        static_folder = os.path.join(BASE_DIR, 'static')
        instance_path = os.path.join(BASE_DIR, 'instance')
        app = Flask(__name__, instance_path=instance_path, template_folder=template_folder, static_folder=static_folder)
    else:
        # Modo de desarrollo normal
        app = Flask(__name__, instance_relative_config=True)

    # 3. Cargar la configuración desde nuestro archivo config.py
    # Asegúrate de que el archivo config.py está en el directorio raíz del proyecto.
    app.config.from_object('config.Config')

    # 4. Asegurarse de que la carpeta de instancia exista (donde se guardará la DB)
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass # La carpeta ya existe

    # 5. Inicializar las extensiones con la instancia de la aplicación
    db.init_app(app)
    migrate.init_app(app, db)

    # El contexto de la aplicación es necesario para que los blueprints y modelos funcionen
    with app.app_context():
        # 6. Importar y registrar los Blueprints
        # Cada archivo de rutas se convierte en un módulo que registramos aquí.
        from . import auth_routes
        app.register_blueprint(auth_routes.bp)

        from . import main_routes
        app.register_blueprint(main_routes.bp)
        
        from . import admin_routes
        app.register_blueprint(admin_routes.bp)

        from . import api_routes
        app.register_blueprint(api_routes.bp)

        # Importamos los modelos para que Flask-Migrate (Alembic) los detecte
        from . import models

        # 7. Retornamos la aplicación creada y configurada
        return app