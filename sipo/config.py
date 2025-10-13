"""
Configuración de la aplicación SIPO
"""

import os

class Config:
    """Configuración base de la aplicación"""
    
    # Clave secreta para sesiones y tokens
    SECRET_KEY = 'mi-clave-secta-muy-dificil-de-adivinar-12345'
    
    # Configuración de base de datos - SQLite por defecto para desarrollo
    SQLALCHEMY_DATABASE_URI = 'sqlite:///sipo_dev.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuración de plantillas
    TEMPLATES_AUTO_RELOAD = True
    
    # Configuración de sesiones
    SESSION_COOKIE_SECURE = False  # Cambiar a True en producción con HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
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
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


# Configuración por defecto
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}