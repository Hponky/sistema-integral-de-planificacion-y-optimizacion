@echo off
title SIPO Backend - Setup and Run
color 0A

echo ========================================
echo   SIPO Backend - Setup and Run Script
echo ========================================
echo.

REM Verificar si Python está instalado
echo [1/5] Verificando instalación de Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python no está instalado o no está en el PATH del sistema.
    echo.
    echo Por favor, instala Python desde https://www.python.org/downloads/
    echo Asegúrate de marcar la opción "Add Python to PATH" durante la instalación.
    echo.
    pause
    exit /b 1
)

echo Python encontrado: 
python --version
echo.

REM Instalar dependencias
echo [2/5] Instalando dependencias de Python...
echo Esto puede tomar varios minutos...
python -m pip install Flask Flask-SQLAlchemy Flask-CORS Flask-Migrate Werkzeug pandas numpy scipy python-dotenv bcrypt openpyxl --no-warn-script-location
if %errorlevel% neq 0 (
    echo ERROR: No se pudieron instalar las dependencias.
    pause
    exit /b 1
)
echo Dependencias instaladas correctamente.
echo.

REM Inicializar la base de datos
echo [3/5] Inicializando la base de datos...
cd sipo
python init_db.py
if %errorlevel% neq 0 (
    echo ERROR: No se pudo inicializar la base de datos.
    pause
    exit /b 1
)
echo Base de datos inicializada correctamente.
echo.

REM Iniciar el backend
echo [4/5] Iniciando el backend de SIPO...
echo El backend estará disponible en: http://localhost:5000
echo Health check: http://localhost:5000/api/health
echo.
echo Usuario por defecto: admin
echo Contraseña por defecto: password123
echo.
echo Presiona Ctrl+C para detener el backend.
echo ========================================
echo.

REM Volver al directorio raíz para ejecutar el módulo correctamente
cd ..
python -m sipo.app

echo.
echo ========================================
echo Backend detenido.
echo ========================================
pause