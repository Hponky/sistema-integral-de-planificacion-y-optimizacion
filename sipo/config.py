"""
Configuración de la aplicación SIPO
"""

import os
from dotenv import load_dotenv

# Cargar variables de entorno desde archivo .env
load_dotenv()

class Config:
    """Configuración base de la aplicación"""
    
    # Clave secreta para sesiones y tokens
    SECRET_KEY = 'mi-clave-secta-muy-dificil-de-adivinar-12345'
    
    # Configuración de base de datos - SQLite por defecto para desarrollo
    # Se configura dinámicamente en app.py usando app.instance_path
    SQLALCHEMY_DATABASE_URI = None
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuración de plantillas
    TEMPLATES_AUTO_RELOAD = True
    
    # Configuración de sesiones
    SESSION_COOKIE_SECURE = False  # Cambiar a True en producción con HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'None'  # Cambiado a 'None' para permitir cookies en solicitudes cross-origin
    
    # Configuración CORS para desarrollo
    CORS_ORIGINS = ['http://localhost:4200', 'http://127.0.0.1:4200']


class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Configuración para producción"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True


class TestingConfig(Config):
    """Configuración para pruebas"""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///:memory:')
    SECRET_KEY = os.getenv('SECRET_KEY', 'test-secret-key-for-testing-only-12345')
    WTF_CSRF_ENABLED = os.getenv('WTF_CSRF_ENABLED', 'False').lower() == 'true'
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:4200,http://127.0.0.1:4200').split(',')


# Configuración por defecto
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}