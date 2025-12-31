#!/usr/bin/env python3
"""
Script para ejecutar pruebas unitarias con configuración de entorno adecuada
"""

import os
import sys
import subprocess

def main():
    """Función principal para ejecutar pruebas con entorno de testing"""
    
    # Establecer variables de entorno para testing
    os.environ['FLASK_ENV'] = 'testing'
    
    # Directorio raíz del proyecto
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.environ['PYTHONPATH'] = project_root
    
    # Cargar variables desde archivo .env.test si existe
    env_test_path = os.path.join(project_root, '.env.test')
    if os.path.exists(env_test_path):
        from dotenv import load_dotenv
        load_dotenv(env_test_path)
        print(f"Variables de entorno cargadas desde {env_test_path}")
    else:
        print("Advertencia: Archivo .env.test no encontrado, usando variables por defecto")
    
    # Ejecutar pytest con configuración específica
    try:
        result = subprocess.run([
            sys.executable, '-m', 'pytest', 
            '-v',  # Verbose
            '--tb=short',  # Traceback corto
            '--cov=.',  # Cobertura para el módulo actual
            '--cov-report=html',  # Reporte HTML
            '--cov-report=term-missing',  # Reporte en terminal
            '--cov-fail-under=85',  # Fallar si cobertura < 85%
            'tests/'  # Directorio de pruebas
        ], check=True)
        
        if result.returncode == 0:
            print("[OK] Pruebas ejecutadas exitosamente")
            print(f"[INFO] Reporte de cobertura generado en htmlcov/index.html")
        else:
            print(f"[ERROR] Falló la ejecución de pruebas (código: {result.returncode})")
            sys.exit(result.returncode)
               
    except FileNotFoundError:
        print("[ERROR] pytest no encontrado. Asegúrate de que está instalado:")
        print("pip install pytest pytest-cov pytest-flask factory-boy")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Error inesperado: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()