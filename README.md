# Sistema Integral de Planificación y Optimización (SIPO)

## Descripción

SIPO es un sistema integral para la planificación y optimización de recursos que incluye un backend basado en Flask (Python) y un frontend desarrollado en Angular.

## Requisitos del Sistema

- Python 3.9 o superior
- Node.js 16 o superior (para el frontend)
- pip (gestor de paquetes de Python)

## Instalación y Ejecución

### Opción 1: Usar el script automatizado (Recomendado)

Para facilitar la instalación y ejecución en cualquier equipo, hemos creado un script automatizado que realiza todos los pasos necesarios:

1. **Ejecutar el script de instalación y ejecución:**
   ```
   setup_and_run_backend.bat
   ```

   Este script realizará automáticamente:
   - Verificación de la instalación de Python
   - Instalación de todas las dependencias necesarias
   - Inicialización de la base de datos
   - Inicio del servidor backend

2. **Acceder al backend:**
   - API REST: http://localhost:5000
   - Health check: http://localhost:5000/api/health
   - Usuario por defecto: admin
   - Contraseña por defecto: password123

### Opción 2: Instalación Manual

#### Backend

1. **Instalar dependencias de Python:**
   ```
   python -m pip install Flask Flask-SQLAlchemy Flask-CORS Flask-Migrate Werkzeug pandas numpy scipy python-dotenv bcrypt openpyxl
   ```

2. **Inicializar la base de datos:**
   ```
   cd sipo
   python init_db.py
   cd ..
   ```

3. **Ejecutar el backend:**
   ```
   python -m sipo.app
   ```

   O alternativamente:
   ```
   python -c "import sys; sys.path.append('.'); from sipo.app import create_app; app = create_app('development'); app.run(debug=True, host='0.0.0.0', port=5000)"
   ```

   O alternativamente:
   ```
   py -m sipo.app  
   ```

#### Frontend

0. **Permitir comandos npm**
   ```
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   ```

1. **Navegar al directorio del frontend:**
   ```
   cd frontend
   ```

2. **Instalar dependencias de Node.js:**
   ```
   npm install
   ```

3. **Ejecutar el servidor de desarrollo:**
   ```
   ng serve
   ```
   O alternativamente
   ```
   npx ng serve
   ```
4. **Ejecutar pruebas unitarias automatizadas**
   ```
   cd frontend && npm test
   ```
   ó
   ```
   cd frontend && npm test --watch=false --browsers=ChromeHeadless
   ```

4. **Acceder al frontend:**
   - Aplicación web: http://localhost:4200

## Estructura del Proyecto

```
SIPO/
├── sipo/                    # Backend Flask
│   ├── app.py              # Aplicación principal
│   ├── config.py           # Configuración
│   ├── models.py           # Modelos de base de datos
│   ├── init_db.py          # Script de inicialización de BD
│   ├── requirements.txt    # Dependencias de Python
│   ├── routes/             # Endpoints de la API
│   ├── services/           # Lógica de negocio
│   └── utils/              # Utilidades
├── frontend/               # Frontend Angular
│   ├── src/                # Código fuente
│   ├── package.json        # Dependencias de Node.js
│   └── angular.json        # Configuración de Angular
├── setup_and_run_backend.bat  # Script automatizado de instalación
└── README.md               # Este archivo
```

## Datos de Acceso por Defecto

- **Usuario:** admin
- **Contraseña:** password123

## Endpoints Principales del Backend

- `GET /api/health` - Health check del servidor
- `POST /api/auth/login` - Inicio de sesión
- `GET /api/calculator/segments` - Obtener segmentos
- `POST /api/calculator/calculate` - Realizar cálculos

## Troubleshooting

### Problemas Comunes

1. **"Python no se reconoce como comando interno"**
   - Solución: Reinstala Python asegurándote de marcar "Add Python to PATH"

2. **"pip no se reconoce como comando interno"**
   - Solución: Usa `python -m pip` en lugar de `pip`

3. **"ModuleNotFoundError: No module named 'sipo'"**
   - Solución: Ejecuta el backend desde el directorio raíz con `python -m sipo.app`

4. **Problemas con la base de datos**
   - Solución: Elimina el archivo `sipo/instance/sipo_dev.db` y ejecuta `python init_db.py`

### Scripts Disponibles

- `setup_and_run_backend.bat` - Script completo de instalación y ejecución
- `run_backend.bat` - Script simple para ejecutar el backend (requiere dependencias instaladas)
- `run_backend_advanced.bat` - Script con múltiples métodos para encontrar Python
- `run_backend_simple.bat` - Script simplificado para ejecutar el backend

## Desarrollo

### Backend

El backend está desarrollado en Flask y utiliza:
- SQLAlchemy para la base de datos
- Flask-CORS para manejar CORS
- Flask-Migrate para migraciones
- bcrypt para el hashing de contraseñas

### Frontend

El frontend está desarrollado en Angular y utiliza:
- Angular Material para componentes UI
- RxJS para programación reactiva
- HttpClient para comunicación con el backend

## Contribución

1. Fork del proyecto
2. Crear una rama de características (`git checkout -b feature/NuevaCaracteristica`)
3. Commit de los cambios (`git commit -am 'Agregar nueva característica'`)
4. Push a la rama (`git push origin feature/NuevaCaracteristica`)
5. Crear un Pull Request
