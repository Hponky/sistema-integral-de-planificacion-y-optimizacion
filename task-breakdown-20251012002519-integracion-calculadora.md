# Planificación de Integración: Calculadora de Dimensionamiento en /sipo

## Objetivo
Integrar la funcionalidad de la calculadora de dimensionamiento de agentes, actualmente en `Planificador-WFM-main/templates/calculator.html` y su lógica asociada en `Planificador-WFM-main/app.py`, dentro de la nueva estructura del proyecto `/sipo` (backend Flask) y el proyecto `frontend/` (Angular), siguiendo los mejores estándares de desarrollo.

## Arquitectura de Carpetas Propuesta para `/sipo` (Backend Flask)
```
sipo/
├── __init__.py
├── app.py
├── config.py
├── models.py
├── routes/
│   ├── __init__.py
│   ├── auth.py             # Rutas de autenticación (login, logout)
│   ├── admin.py            # Rutas de administración (usuarios, campañas, segmentos, reglas) - Expondrá APIs REST
│   ├── calculator.py       # Rutas y lógica específica de la calculadora - Expondrá APIs REST
│   ├── forecasting.py      # Rutas y lógica de forecasting - Expondrá APIs REST
│   ├── scheduling.py       # Rutas y lógica de scheduling - Expondrá APIs REST
│   └── summary.py          # Rutas y lógica de resumen - Expondrá APIs REST
├── services/
│   ├── __init__.py
│   ├── calculator_service.py # Funciones de cálculo de dimensionamiento (vba_erlang, procesar_plantilla_unica, etc.)
│   ├── scheduling_service.py # Lógica del Scheduler
│   └── forecasting_service.py # Lógica de forecasting (ponderación, distribución)
├── templates/              # Plantillas Jinja2 (solo para páginas básicas o de fallback, la UI principal será Angular)
│   ├── base.html           # Plantilla base (puede ser eliminada si Angular maneja toda la UI)
│   └── auth/
│       └── login.html      # Página de login (puede ser reemplazada por un componente Angular)
├── static/                 # Archivos estáticos (CSS, JS, imágenes)
│   ├── css/
│   ├── js/
│   └── img/
├── migrations/             # Migraciones de base de datos (Flask-Migrate)
├── tests/                  # Pruebas unitarias e de integración
│   ├── __init__.py
│   ├── unit/
│   │   ├── test_calculator_service.py
│   │   └── test_scheduling_service.py
│   └── integration/
│       └── test_routes.py
├── utils/                  # Utilidades generales (decoradores, helpers)
│   ├── __init__.py
│   └── decorators.py       # Decoradores como admin_required
├── requirements.txt        # Dependencias de Python
└── wsgi.py                 # Punto de entrada para servidores WSGI (Gunicorn)
```

## Arquitectura de Carpetas Propuesta para `frontend/` (Frontend Angular)
```
frontend/
├── src/
│   ├── app/
│   │   ├── core/
│   │   │   ├── services/
│   │   │   │   └── api.service.ts        # Servicio para interactuar con el backend Flask
│   │   │   │   └── auth.service.ts       # Servicio de autenticación (manejo de tokens, estado de login)
│   │   │   └── guards/
│   │   │       └── auth.guard.ts         # Guard para proteger rutas
│   │   ├── features/
│   │   │   ├── calculator/               # Módulo de la calculadora
│   │   │   │   ├── calculator.component.ts
│   │   │   │   ├── calculator.component.html
│   │   │   │   ├── calculator.component.css
│   │   │   │   ├── calculator.service.ts # Servicio específico para la lógica de la calculadora
│   │   │   │   └── calculator-routing.module.ts
│   │   │   ├── auth/                     # Módulo de autenticación (si se implementa en Angular)
│   │   │   │   ├── login/
│   │   │   │   │   ├── login.component.ts
│   │   │   │   │   ├── login.component.html
│   │   │   │   │   └── login.component.css
│   │   │   │   └── auth-routing.module.ts
│   │   │   ├── dashboard/
│   │   │   ├── planning/
│   │   │   ├── admin/                    # Módulo de administración
│   │   │   ├── forecasting/              # Módulo de forecasting
│   │   │   ├── scheduling/               # Módulo de scheduling
│   │   │   └── summary/                  # Módulo de resumen
│   │   └── shared/
│   │       ├── components/
│   │       ├── interfaces/
│   │       └── shared.module.ts
│   └── environments/
```

## Proceso de Implementación Requerido

### Sub-tarea 1: Establecer la Estructura Base de `/sipo` (Backend)
- [x] Crear las carpetas y archivos iniciales según la arquitectura propuesta (`sipo/__init__.py`, `sipo/app.py`, `sipo/config.py`, `sipo/models.py`, `sipo/routes/__init__.py`, `sipo/services/__init__.py`, `sipo/templates/base.html`, `sipo/static/`).
- [x] Migrar la configuración básica de Flask de `Planificador-WFM-main/app.py` a `sipo/app.py` y `sipo/config.py`.
- [x] Migrar los modelos de SQLAlchemy de `Planificador-WFM-main/app.py` a `sipo/models.py`.

### Sub-tarea 2: Migrar Lógica de la Calculadora (Backend - APIs REST)
- [x] Crear `sipo/services/calculator_service.py`.
- [x] Mover las funciones de cálculo VBA (`vba_erlang_b`, `vba_erlang_c`, `vba_sla`, `vba_agents_required`) y `procesar_plantilla_unica` de `Planificador-WFM-main/app.py` a `sipo/services/calculator_service.py`.
- [x] Adaptar las importaciones y referencias necesarias en `calculator_service.py`.
- [x] Crear `sipo/routes/calculator.py`.
- [x] Mover la lógica de la ruta `/calculator` (GET) para obtener segmentos y la lógica de la ruta `/calcular` (POST) para procesar el cálculo de `Planificador-WFM-main/app.py` a `sipo/routes/calculator.py`.
- [x] Adaptar la lógica de las rutas para usar las funciones del `calculator_service.py` y los modelos de `sipo/models.py`, **exponiendo estas funcionalidades como APIs RESTful que serán consumidas por el frontend Angular.**
- [x] Registrar el blueprint de `calculator.py` en `sipo/app.py`.

### Sub-tarea 3: Implementar Componente de Calculadora (Frontend Angular)
- [x] Crear el módulo `frontend/src/app/features/calculator/`.
- [x] Generar el componente `CalculatorComponent` (`.ts`, `.html`, `.css`) dentro de este módulo.
- [x] Implementar el formulario de la calculadora en `calculator.component.html`, replicando la funcionalidad de `Planificador-WFM-main/templates/calculator.html`.
- [x] Desarrollar la lógica en `calculator.component.ts` para:
    - Obtener la lista de segmentos del backend a través de una API.
    - Manejar la carga del archivo Excel y los parámetros de cálculo.
    - Enviar los datos del formulario (incluyendo el archivo) a la API de cálculo del backend.
    - Recibir y mostrar los resultados (KPIs y tablas) de la API del backend.
    - Implementar la lógica de UI (loader, mensajes de error/éxito) en el frontend.
- [x] Crear un `calculator.service.ts` para encapsular las llamadas a la API del backend relacionadas con la calculadora.
- [x] Definir las interfaces TypeScript necesarias para los datos de entrada y salida de la calculadora.
- [x] Configurar el enrutamiento para el componente de la calculadora.

### Sub-tarea 4: Migrar Lógica de Autenticación y Base (Backend y Frontend)
- [x] Crear `sipo/routes/auth.py` y mover las rutas `/` (login) y `/logout`).
- [x] Crear `sipo/templates/auth/login.html` y mover `Planificador-WFM-main/templates/login.html`.
- [x] Adaptar `sipo/templates/base.html` de `Planificador-WFM-main/templates/base.html` a la nueva estructura.
- [x] Mover el decorador `admin_required` a `sipo/utils/decorators.py`.
- [ ] **(Frontend Angular)** Si se decide que la autenticación se maneje completamente en Angular:
    - Crear un módulo `frontend/src/app/features/auth/login/` con `LoginComponent`.
    - Implementar la lógica de login en Angular, consumiendo una API de autenticación del backend.
    - Desarrollar un `auth.service.ts` en `frontend/src/app/core/services/` para manejar la autenticación (login, logout, tokens, estado del usuario).
    - Implementar un `auth.guard.ts` en `frontend/src/app/core/guards/` para proteger las rutas de Angular.
    - Eliminar `sipo/templates/auth/login.html` y `sipo/templates/base.html` si ya no son necesarios.

### Sub-tarea 5: Migrar Otras Rutas y Lógica Relacionada (Backend y Frontend)
- [ ] **(Backend Flask)** Mover las rutas y lógica de negocio de `admin`, `history`, `scheduling`, `summary`, `forecasting`, `intraday_forecaster`, `breaks` a sus respectivos módulos en `sipo/routes/` y `sipo/services/`.
- [ ] **(Backend Flask)** Asegurar que todas estas funcionalidades expongan APIs RESTful para ser consumidas por el frontend Angular.
- [ ] **(Frontend Angular)** Crear los módulos y componentes Angular correspondientes para `admin`, `history`, `scheduling`, `summary`, `forecasting`, `intraday_forecaster`, `breaks` en `frontend/src/app/features/`.
- [ ] **(Frontend Angular)** Implementar la lógica de UI y la interacción con las APIs del backend en estos componentes.

### Sub-tarea 6: Configurar Dependencias y Entorno
- [ ] Crear `sipo/requirements.txt` y copiar las dependencias de `Planificador-WFM-main/requirements.txt`.
- [ ] Actualizar `sipo/app.py` para inicializar Flask-SQLAlchemy y Flask-Migrate correctamente.
- [ ] Configurar el `DATABASE_URL` en `sipo/config.py` o como variable de entorno.
- [ ] Configurar el proxy de Angular para redirigir las llamadas a la API al backend Flask.

### Sub-tarea 7: Implementar Pruebas Unitarias e de Integración
- [ ] Crear `sipo/tests/unit/test_calculator_service.py` y escribir pruebas para las funciones de cálculo.
- [ ] Crear `sipo/tests/integration/test_calculator_routes.py` y escribir pruebas para las APIs de la calculadora.
- [ ] Asegurar una cobertura de pruebas adecuada para la lógica migrada del backend.
- [ ] Escribir pruebas unitarias para los servicios y componentes de Angular.

### Sub-tarea 8: Verificación y Refactorización
- [ ] Ejecutar la aplicación Flask en `/sipo` y el proyecto Angular en `frontend/`.
- [ ] Verificar que la calculadora funciona correctamente a través de la interfaz de Angular.
- [ ] Realizar pruebas manuales de la funcionalidad completa.
- [ ] Revisar el código (backend y frontend) para asegurar que cumple con los principios de calidad (DRY, modularidad, legibilidad, SOLID, etc.).
- [ ] Eliminar cualquier código duplicado o innecesario.
- [ ] Asegurar que no se introduzcan nuevos errores o advertencias del linter en ambos proyectos.

## Criterios de Finalización
- La calculadora de dimensionamiento funciona completamente a través del componente Angular, consumiendo las APIs RESTful del backend Flask.
- El código del backend Flask está organizado según la arquitectura propuesta, exponiendo APIs REST.
- El código del frontend Angular está organizado según los estándares de Angular, con componentes, servicios y enrutamiento adecuados.
- Se han implementado pruebas unitarias y de integración para la lógica de la calculadora (backend y frontend).
- No hay errores de ejecución ni advertencias del linter en ambos proyectos.
- El archivo `task-breakdown-20251012002519-integracion-calculadora.md` está actualizado con el estado de las sub-tareas.