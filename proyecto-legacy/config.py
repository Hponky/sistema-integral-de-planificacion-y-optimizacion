# config.py (en la raíz de tu proyecto, carpeta PP)

import os
import sys

# Determina la ruta base, funciona tanto en desarrollo como en el .exe de PyInstaller
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
    instance_path = os.path.join(BASE_DIR, 'instance')
else:
    # __file__ se refiere a este archivo (config.py). dirname() nos da el directorio raíz.
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    instance_path = os.path.join(BASE_DIR, 'instance')

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'mi-clave-secta-muy-dificil-de-adivinar-12345'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # La URI de la base de datos ahora usa la variable 'instance_path' que definimos arriba
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(instance_path, 'wfm.db')

# --- AÑADE ESTA SECCIÓN PARA EL PLANIFICADOR ---

# --- Parámetros del Solucionador OR-Tools ---
SOLVER_PARAMS = {
    'max_time_in_seconds': 300.0,
    'linearization_level': 0,
}

# --- Constantes de la Aplicación ---
VALID_AUSENCIA_CODES = ['VAC', 'BMED', 'BAJA', 'AUSENCIA']