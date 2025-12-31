# Documentación de Estado Actual: Funcionalidades Integradas (SIPO)

Este documento detalla los componentes, arquitecturas y funcionalidades que ya han sido migrados y se encuentran operativos en los repositorios `em_sipo` (Frontend) y `em_sipo_api_rest` (Backend). La estructura sigue los estándares de ingeniería de software profesional aplicados durante la transición desde el proyecto legacy.

---

## 1. Arquitectura Base y Fundamentos Técnicos

### 1.1. Backend: Em_sipo_api_rest (Python/Flask)
Se ha establecido una infraestructura robusta basada en Flask con una clara separación de responsabilidades:
- **Estructura de Servicios:** Uso de la capa `services` para la lógica de negocio pesada, manteniendo las `routes` limpias y enfocadas en la orquestación de peticiones.
- **Persistencia Avanzada (SQLAlchemy):** Implementación de una arquitectura relacional sólida en Oracle, superando el modelo plano del legacy. Se utilizan `db.Sequence` para la gestión de IDs y relaciones `backref` para navegación fluida entre objetos.
- **Motor de Aislamiento del Scheduler:** Ejecución del motor de planificación en un subproceso independiente (`scheduler_isolate.py`). Esto permite:
    - Evitar bloqueos del bucle de eventos de Flask durante cálculos intensivos.
    - Gestión de memoria aislada.
    - Mayor facilidad para escalado horizontal futuro.
- **Seguridad JWT:** Implementación de autenticación basada en tokens (HS256) con capacidad de renovación y validación proactiva en cada endpoint.

### 1.2. Frontend: Em_sipo (Angular 18+)
La aplicación web utiliza las últimas capacidades de Angular para una experiencia de usuario de alto nivel:
- **Standalone Components:** Eliminación de módulos complejos en favor de componentes independientes, mejorando la mantenibilidad y el tree-shaking.
- **Gestión de Estado Reactiva (Signals):** Migración total desde patrones imperativos hacia Signals de Angular. Esto garantiza que la UI se actualice de forma atómica y eficiente solo cuando los datos cambian.
- **Service Facades:** Implementación del patrón Facade (ej: `SchedulingFacade`) para centralizar la comunicación entre la UI y los servicios de API, ocultando la complejidad de los observables y transformaciones de datos.
- **Sistema de Diseño Glassmorphism:** Implementación de una identidad visual premium basada en variables CSS, gradientes complejos y efectos de desenfoque, alineada con estéticas modernas de SaaS.

---

## 2. Motor de Dimensionamiento (Calculadora)

### 2.1. Ingesta de Datos y Parsing de Requisitos
- **Parser de Excel Robusto:** Integración de un servicio de parsing capaz de detectar automáticamente cabeceras de intervalos, volúmenes de llamadas y AHT desde archivos Excel con formatos variables.
- **Validación de Datos:** Módulo que normaliza intervalos de tiempo (ej: convertir "8:00" a "08:00") y asegura que los valores de demanda sean numéricos, evitando fallos silenciosos en el cálculo.

### 2.2. Algoritmo de Cálculo Central (`DimensioningCalculator`)
- **Pipeline de Métricas:** Sistema que calcula la "Cadena de Reducción" completa:
    1.  **Dimensionados:** Headcount necesario de plantilla.
    2.  **Presentes:** Aplicación automática del porcentaje de absentismo.
    3.  **Logados:** Aplicación de factores de adherencia/shrinkage.
    4.  **Efectivos:** Aplicación de auxiliares.
- **Erlang-C:** Implementación del algoritmo Erlang-C para determinar el nivel de servicio proyectado y el tiempo medio de respuesta basándose en la intensidad de tráfico.

### 2.3. Persistencia de Escenarios de Dimensionamiento
- **Snapshots de Cálculo:** Capacidad de guardar el resultado completo de un dimensionamiento en la tabla `DimensioningScenario`. Esto incluye no solo los totales, sino los blobs de datos por intervalo para su posterior consulta sin necesidad de recalcular.
- **Historial de Cálculos:** Componente UI que permite listar, buscar y cargar cálculos previos, facilitando la comparativa entre diferentes hipótesis de demanda.

---

## 3. Motor de Planificación (Scheduling)

### 3.1. Generación de Turnos Base
- **Algoritmo de Optimización:** Integración de un motor que asigna tramos horarios basándose en las curvas de requerimiento cargadas desdde los escenarios de dimensionamiento.
- **Respeto de Reglas Contractuales:** Lógica que valida las horas semanales y jornadas diarias máximas definidas en los perfiles de los agentes durante la fase de generación.

### 3.2. Gestión de Agentes Ficticios (Simulación)
- **Modo de Simulación "Inyectada":** Funcionalidad integrada en el frontend y backend que permite añadir agentes efímeros con configuraciones personalizadas para probar la capacidad de cobertura sin necesidad de cargar una plantilla real.
- **Eliminación y Gestión de Scopes:** Capacidad técnica de filtrar y limpiar agentes simulados antes de persistir planes oficiales.

---

## 4. Servicios de Apoyo y Orquestación

### 4.1. Input Parser (Procesamiento de Archivos)
- **Normalización de Identidificación:** Algoritmo integrado que limpia DNIs/NIEs eliminando decimales (.0), espacios y ceros a la izquierda, asegurando la integridad al cruzar datos de diferentes fuentes.
- **Merge de Absentismos (Volátil):** Servicio que permite combinar en memoria un archivo de agentes y un archivo de ausencias durante el proceso de planificación, aplicando las ausencias como "bloqueos" en tiempo de ejecución.
- **Detección de Columnas Difusa:** Lógica que identifica columnas de Excel incluso si los nombres varían ligeramente (ej: "DNI", "IDENTIFICACION", "CODIGO EMPLEADO").

### 4.2. Activity Allocator (Gestor de Actividades Secundarias)
- **Estructura Reutilizable:** Aunque actualmente se encuentra en modo "Dormant" (deshabilitado por flag), el servicio ya cuenta con la arquitectura para inyectar objetos de actividad (BREAK, PVD) dentro de los turnos planificados.
- **Formateo de Tramos:** Funcionalidad integrada para convertir minutos transcurridos a etiquetas horarias legibles (HH:MM) para el usuario final.

---

## 5. Visualización Avanzada y KPIs en Tiempo Real

### 5.1. Dashboard de KPIs Reactivos (Frontend)
- **Cálculo On-the-fly:** La UI recalcula automáticamente indicadores de Nivel de Servicio (SL) y Nivel de Atención (NDA) cada vez que se modifica la planificación o se añaden agentes simulados.
- **Tarjetas de Resumen (KPI Cards):** Componentes integrados que muestran el promedio de horas, número de agentes activos y promedios de absentismo (VAC/BMED) detectados en el plan actual.

### 5.2. Tabla de Planificación Dinámica
- **Detección de Conflictos Visuales:** Sistema de coloreado que identifica tramos manuales vs tramos automáticos y resalta ausencias cargadas en el sistema.
- **Gestión de Selección de Agentes:** Implementación de Signals para manejar la selección múltiple de agentes y permitir acciones en bloque (como la exportación filtrada).

---

## 6. Exportación y Entrega de Resultados

### 6.1. Export Service (Excel)
- **Generación Multi-Agente:** Motor capaz de generar archivos `.xlsx` detallados con una fila por agente y columnas dinámicas por día del período planificado.
- **Exportación de Métricas:** Integración del resumen de cobertura e indicadores (Required vs Online) directamente en la pestaña de resultados para facilitar el análisis offline.
- **Almacenamiento Temporizado:** Sistema de guardado en `/static/exports` con nombres únicos basados en timestamp para evitar colisiones de archivos entre usuarios.

---

## 7. Gestión de Escenarios de Planificación y Persistencia

### 7.1. Modelo de Datos `PlanningScenario`
- **Serialización de Resultados:** El sistema permite guardar el estado completo de una planificación (incluyendo el calendario de todos los agentes, sus métricas intradía y los KPIs globales) en una única transacción de base de datos.
- **Soporte para Escenarios Temporales:** Implementación de un sistema de "Expiración Diferida" (`expires_at`), donde el usuario puede marcar un escenario como temporal (ej: para pruebas rápidas) y el sistema lo limpia automáticamente tras un periodo definido (ej. 7-30 días).
- **Vinculación con Dimensionamiento:** Los escenarios de planificación conservan la trazabilidad de qué escenario de dimensionamiento los originó, permitiendo comparar el plan contra los requerimientos originales en cualquier momento.

### 7.2. Interfaz de Historial y Carga Diferida
- **Bandeja de Gestión de Escenarios:** UI integrada para listar los últimos planes guardados, mostrando autor, fecha y tags de estatus (Temporal/Permanente).
- **Recuperación Total de Estado:** Al cargar un escenario previo, el frontend reconstruye no solo la tabla de turnos, sino también todas las gráficas de cobertura y KPIs asociados, permitiendo retomar la sesión de trabajo exactamente donde se dejó.

---

## 8. Seguridad, Autenticación y Control de Acceso

### 8.1. Integración Active Directory (AD) y JWT
- **Intercambio de Tokens (`exchange-token`):** Arquitectura preparada para validar las credenciales del Directorio Activo (Azure AD/AD) y transformarlas en un JWT de backend seguro.
- **Manejo de Metadatos de Usuario:** El token JWT transporta de forma segura el `idLegal`, `username` y `role`, permitiendo que el backend asocie automáticamente cada acción (como guardar un escenario) al usuario real.
- **Renovación Anticipada:** Endpoint de `auth/renew` integrado para refrescar la sesión del usuario sin interrumpir su flujo de trabajo operativo.

### 8.2. Decorador `@token_required` y Seguridad de Ruta
- **Protección de API:** Todas las rutas críticas (planificación, dimensionamiento, bases de datos) están protegidas por un middleware que valida la firma, integridad y expiración del token Bearer en cada petición.
- **Inyección de Identidad (`g.user`):** La identidad del usuario se inyecta en el objeto global de Flask tras la validación, facilitando la auditoría y el filtrado de datos por pertenencia.

---

## 9. Modularización y Mantenibilidad del Código

### 9.1. Organización de Rutas por Dominio
- **Blueprints de Flask:** El backend está organizado en Blueprints independientes (`planning_bp`, `auth_bp`, `calculator_bp`), lo que evita archivos de rutas gigantescos y facilita la colaboración paralela entre desarrolladores.

### 9.2. Servicios Aislados y Utilidades
- **Utils de Formateo:** Centralización de lógica de formateo de fechas y números en utilidades compartidas, asegurando que un "Nivel de Servicio" se calcule y muestre de la misma forma en toda la aplicación.

---
