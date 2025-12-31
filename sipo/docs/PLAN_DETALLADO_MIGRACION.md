# Plan de Migración Detallado SIPO (Legacy -> Profesional)

Este documento detalla la hoja de ruta para la migración a los nuevos repositorios `em_sipo` (Frontend) y `em_sipo_api_rest` (Backend).

---

## Módulo 1: Administración, Estructura Organizacional y Maestros
*Foco: Centralización de la configuración operativa y legal.*

### 1.1. Refactorización y Extensión del Modelo de Datos `Campaign` (Backend)
- **Descripción:** Migrar la entidad `Campaign` desde el legacy a `em_sipo_api_rest` añadiendo metadatos críticos: código de país (ISO), zona horaria (para despliegues internacionales) y centro de coste. Se debe asegurar que el campo `code` sea único y se utilice como identificador lógico en las rutas de exportación.
- **Justificación:** Las campañas son el nodo raíz de toda la jerarquía. Sin la zona horaria y el país, los cálculos de festivos y horas legales fallarían.
- **Complejidad:** Baja (3/10)
- **Estimación:** 6 horas
- **Pruebas:** 
  - Unitarias: Validación de formatos de código de país.
  - Integración: Persistencia en base de datos Oracle con Constraints de unicidad.

### 1.2. Motor de Persistencia de Segmentos y Tipos de Servicio (Backend)
- **Descripción:** Implementar en la API el CRUD para `Segment`. Se debe tipificar el servicio: `INBOUND`, `OUTBOUND`, `BACKOFFICE` o `BLEND`. Cada tipo de servicio activará o desactivará diferentes algoritmos de cálculo.
- **Justificación:** El motor de planificación necesita saber qué "clase de trabajo" está calculando (Erlang-C vs Productividad Lineal).
- **Complejidad:** Media (5/10)
- **Estimación:** 8 horas
- **Pruebas:** 
  - Unitarias: Verificación de que el cambio de tipo de servicio actualiza correctamente las propiedades permitidas.
  - Integración: Relación Many-to-One con Campañas.

### 1.3. Lógica de Ventanas Operativas por Día de la Semana (Backend)
- **Descripción:** Desarrollo del servicio que valida las horas de apertura y cierre para los 7 días de la semana. Incluye la utilidad `is_within_operating_hours(date, time)` para evitar asignaciones fuera de horario.
- **Justificación:** Previene errores comunes del legacy donde se asignaban tramos posteriores al cierre del centro.
- **Complejidad:** Media (6/10)
- **Estimación:** 9 horas
- **Pruebas:** 
  - Unitarias: Testeo de bordes (apertura 08:00 vs solicitud 07:59).
  - Integración: API Query de horarios por segmento.

### 1.4. Sistema de Políticas de Fines de Semana y Descansos (Backend)
- **Descripción:** Implementación de la lógica de negocio para `min_full_weekends_off_per_month` y `weekend_policy` (`REQUIRE_ONE_DAY_OFF`, `FIXED_OFF_DAYS`). Requiere algoritmos de análisis de calendario mensual.
- **Justificación:** Garantizar los fines de semana libres pactados es vital para el cumplimiento legal y el clima laboral.
- **Complejidad:** Alta (8/10)
- **Estimación:** 9 horas
- **Pruebas:** 
  - Unitarias: Algoritmo de conteo de fines de semana en meses de 4 y 5 semanas.

### 1.5. Desarrollo del "Master-Detail UI" para Campañas/Segmentos (Frontend)
- **Descripción:** Crear en Angular los componentes para gestionar la jerarquía Campaña-Segmento usando Signals y estética premium glassmorphism.
- **Justificación:** Reduce el error humano al permitir al usuario visualizar la estructura antes de planificar.
- **Complejidad:** Media (5/10)
- **Estimación:** 8 horas
- **Pruebas:** 
  - E2E: Flujo de navegación desde el Dashboard hasta un segmento específico.

### 1.6. Formulario Reactivo de Configuración Horaria (Frontend)
- **Descripción:** Componente UI para editar horarios con TimePicker, incluyendo validaciones cruzadas (Inicio < Fin).
- **Justificación:** Evita configuraciones inválidas que bloqueaban el motor de planificación en el legacy.
- **Complejidad:** Media (4/10)
- **Estimación:** 7 horas
- **Pruebas:** 
  - E2E: Validación visual de mensajes de error en horarios incongruentes.

### 1.7. Grid de Gestión de Reglas Contractuales (`SchedulingRules`) (Frontend)
- **Descripción:** Interfaz para gestionar límites legales de contratos, integrada con los endpoints de la API.
- **Justificación:** Permite al analista verificar rápidamente los parámetros legales aplicados a cada grupo de agentes.
- **Complejidad:** Media (5/10)
- **Estimación:** 8 horas
- **Pruebas:** 
  - Integración: Consumo de endpoints con estados de carga (skeletons).

### 1.8. Parser de Importación Masiva de Maestros (Backend)
- **Descripción:** Servicio de procesamiento de Excel para carga masiva de la estructura organizativa con detección de duplicados.
- **Justificación:** Agiliza la puesta en marcha de nuevos clientes/campañas sin carga manual.
- **Complejidad:** Media (7/10)
- **Estimación:** 9 horas
- **Pruebas:** 
  - Unitarias: Mock de archivos Excel corruptos o con columnas faltantes.

### 1.9. Middleware de Auditoría Base (Backend)
- **Descripción:** Implementar decorador/middleware para capturar logs de auditoría (Quién, Cuándo y Qué cambió) en tablas maestros.
- **Justificación:** Obligatorio en entornos profesionales para trazabilidad de cambios críticos.
- **Complejidad:** Media (6/10)
- **Estimación:** 8 horas
- **Pruebas:** 
  - Integración: Verificación de entrada en tabla de auditoría tras un cambio en un segmento.

---

## Módulo 2: Gestión Operativa de Novedades y Motor de Absentismo (BDB)
*Foco: Persistencia y gestión inteligente de las ausencias legales y operativas.*

### 2.1. Refactorización del Modelo `Absence` y Relaciones (Backend)
- **Descripción:** Rediseñar la tabla `Absence` para soportar relaciones directas con `Agent` y `Segment`. Incluir campos de auditoría (quién cargó la novedad) y tipos de incidencia normalizados (VAC, BMED, LIC, etc.).
- **Justificación:** Una estructura relacional robusta permite consultas rápidas por segmento.
- **Complejidad:** Media (4/10)
- **Estimación:** 7 horas
- **Pruebas:** 
  - Unitarias: Validación de unicidad para evitar duplicados.
  - Integración: Test de integridad referencial.

### 2.2. API REST: CRUD de Novedades Individuales (Backend)
- **Descripción:** Implementar los endpoints estandarizados para Crear, Leer, Actualizar y Eliminar ausencias de forma individual.
- **Justificación:** Permite la corrección manual rápida de novedades sin necesidad de procesar archivos masivos.
- **Complejidad:** Baja (3/10)
- **Estimación:** 8 horas
- **Pruebas:** 
  - Unitarias: Validación de rangos de fecha lógicos.
  - Integración: Verificación de respuesta HTTP en cambios de estado.

### 2.3. Motor de Consolidación y Resolución de Solapamientos (Backend)
- **Descripción:** Lógica de negocio que procesa la carga de ausencias y resuelve solapamientos según jerarquía de ausencias definida.
- **Justificación:** Evita inconsistencias cuando un agente tiene múltiples novedades el mismo día.
- **Complejidad:** Alta (7/10)
- **Estimación:** 9 horas
- **Pruebas:** 
  - Unitarias: Casos de prueba con solapamientos múltiples.

### 2.4. Componente de Visualización de Novedades por Agente (Frontend)
- **Descripción:** Pantalla detallada que muestra el histórico de ausencias de un agente con filtros dinámicos.
- **Justificación:** Facilita al supervisor la revisión del historial de un colaborador.
- **Complejidad:** Media (5/10)
- **Estimación:** 8 horas
- **Pruebas:** 
  - E2E: Verificación de carga de datos al seleccionar un agente.

### 2.5. Lógica de "Protección de Fecha" en el Motor de Turnos (Backend)
- **Descripción:** Modificar el `Scheduler` para que respete las ausencias registradas, bloqueando la asignación de turnos en esos días.
- **Justificación:** Garantiza que el scheduler no sobrescriba vacaciones o bajas médicas.
- **Complejidad:** Alta (8/10)
- **Estimación:** 9 horas
- **Pruebas:** 
  - Unitarias: Ejecución del scheduler con agentes en baja médica.

### 2.6. Endpoint de Detección Proactiva de Conflictos (Backend)
- **Descripción:** Servicio que compara novedades entrantes con turnos planificados y reporta discrepancias.
- **Justificación:** Permite anticipar el impacto operativo de nuevas ausencias.
- **Complejidad:** Media (6/10)
- **Estimación:** 8 horas
- **Pruebas:** 
  - Unitarias: Validación de lógica de comparación de turnos vs ausencias.

### 2.7. Modal INTERACTIVO de Resolución de Conflictos (Frontend)
- **Descripción:** Interfaz para que el analista decida cómo resolver cada conflicto (sobrescribir o mantener turno).
- **Justificación:** Proporciona flexibilidad y control humano sobre la planificación automática.
- **Complejidad:** Alta (7/10)
- **Estimación:** 9 horas
- **Pruebas:** 
  - E2E: Flujo completo de carga de conflicto y resolución manual.

### 2.8. Generador de Reporte de Absentismo para RRHH (Backend)
- **Descripción:** Generación de reportes Excel consolidados para procesos de nómina y recursos humanos.
- **Justificación:** Asegura que la planificación sea la fuente de verdad para pagos.
- **Complejidad:** Media (4/10)
- **Estimación:** 7 horas
- **Pruebas:** 
  - Integración: Validación de formato y datos en el archivo Excel generado.

---

## Módulo 3: Detalle Intradía (Actividades Secundarias: Breaks y PVDs)
*Foco: Micro-planificación de intervalos de descanso y cumplimiento de normativa de salud laboral.*

### 3.1. Refactorización del Generador de Breaks (Backend)
- **Descripción:** Migrar y limpiar la lógica de `breaks_service.py` del legacy hacia un servicio profesional en `em_sipo_api_rest`. Implementar el cálculo de duración de break según la longitud del turno (ej: 6h -> 20min, 8h -> 30min).
- **Justificación:** Es el motor base que decide *cuánta* pausa le corresponde a cada agente según su jornada.
- **Complejidad:** Media (5/10)
- **Estimación:** 8 horas
- **Pruebas:** 
  - Unitarias: Verificación de tramos de descanso para jornadas de 4h, 5h, 6h y 8h.

### 3.2. Implementación de Lógica de PVDs (Pantalla Visual de Descanso) (Backend)
- **Descripción:** Desarrollar el algoritmo que asigna un PVD de 5 minutos por cada hora de trabajo efectivo, asegurando que se distribuyan uniformemente.
- **Justificación:** Cumplimiento normativo de salud laboral para trabajadores que usan pantallas. En el legacy esta lógica era inconsistente.
- **Complejidad:** Media (6/10)
- **Estimación:** 9 horas
- **Pruebas:** 
  - Unitarias: Verificación de que un turno de 6h tiene exactamente 6 PVDs.

### 3.3. Algoritmo de Distribución Inteligente de Gaps (Backend)
- **Descripción:** Implementar el motor de espaciado que asegura un gap de entre 45 y 75 minutos entre cada actividad secundaría (Break o PVD).
- **Justificación:** Evita que el sistema agrupe todos los descansos al principio o al final de la jornada, lo cual invalidaría la cobertura operativa.
- **Complejidad:** Alta (8/10)
- **Estimación:** 9 horas
- **Pruebas:** 
  - Unitarias: Validación de "mínimo gap" y "máximo gap" entre actividades consecutivas.

### 3.4. Motor de Concurrencia de Descansos por Segmento (Backend)
- **Descripción:** Lógica que limita cuántos agentes pueden salir a descanso simultáneamente para no dejar el servicio desatendido. Debe balancear la "necesidad de descanso" vs el "NDA objetivo".
- **Justificación:** Evita caídas críticas en el nivel de servicio producidas por una mala distribución de pausas.
- **Complejidad:** Alta (9/10)
- **Estimación:** 9 horas
- **Pruebas:** 
  - Unitarias: Simulación de 50 agentes y validación de máximo X% en estado de descanso por intervalo.

### 3.5. Visualización Gantt Intradía: Estructura Base (Frontend)
- **Descripción:** Crear el componente de visualización tipo Timeline (Gantt) en Angular para mostrar las 24 horas del día. Uso de CSS Grid o Canvas para optimizar el rendimiento con muchos agentes.
- **Justificación:** Herramienta visual indispensable para que el supervisor vea "la foto" intradía de su equipo.
- **Complejidad:** Alta (8/10)
- **Estimación:** 9 horas
- **Pruebas:** 
  - E2E: Renderizado correcto de 100 agentes sin LAG en el scroll.

### 3.6. Pintado de Actividades en el Gantt (Signals & Micro-Styling) (Frontend)
- **Descripción:** Implementar el renderizado de los bloques de colores para Jornada, Break y PVDs dentro del componente Gantt, utilizando Signals para actualizaciones reactivas.
- **Justificación:** La claridad visual (colores diferenciados) es clave para identificar rápidamente el estado de la operación.
- **Complejidad:** Media (6/10)
- **Estimación:** 8 horas
- **Pruebas:** 
  - E2E: Verificación de que las horas de inicio/fin en el Gantt coinciden con el API.

### 3.7. Interacción de Edición de Actividades (Drag & Drop) (Frontend)
- **Descripción:** Habilitar la edición manual de descansos en el Gantt. El usuario puede mover un break de un intervalo a otro de forma visual.
- **Justificación:** Permite al supervisor reaccionar a imprevistos (colas de llamadas) moviendo los descansos manualmente.
- **Complejidad:** Alta (9/10)
- **Estimación:** 9 horas
- **Pruebas:** 
  - E2E: Arrastrar un break y verificar que la nueva hora se envía correctamente al backend.

### 3.8. Validador de Reglas en Edición Manual (Backend & Frontend)
- **Descripción:** Sistema que avisa al usuario si, al mover un descanso manualmente, está rompiendo una regla legal (ej: break muy cerca del inicio de jornada) o de cobertura.
- **Justificación:** Previene que la intervención humana degrade la calidad de la planificación o incumpla convenios.
- **Complejidad:** Media (7/10)
- **Estimación:** 8 horas
- **Pruebas:** 
  - Unitarias: Validador de "ventana prohibida" para descansos.

---

## Módulo 4: Workflow de Cambios (Autoservicio TL y Analista)
*Foco: Autonomía operativa y control de calidad en los cambios de turno de última hora.*

### 4.1. Modelado de Solicitudes y Máquina de Estados (Backend)
- **Descripción:** Definir la entidad `ShiftChangeRequest` con estados: `PENDING`, `APPROVED`, `REJECTED`, `CANCELLED`. Implementar la lógica de transición de estados para asegurar que una solicitud no se pueda aprobar dos veces.
- **Justificación:** Es la base del flujo de trabajo de "autoservicio" que permite descentralizar la operación.
- **Complejidad:** Media (5/10)
- **Estimación:** 8 horas
- **Pruebas:** 
  - Unitarias: Verificación de transiciones prohibidas (ej: de `REJECTED` a `APPROVED`).

### 4.2. API: Creación de Solicitudes (Perfil TL) (Backend)
- **Descripción:** Endpoint seguro para que un Team Leader cree una petición de cambio de turno para un agente de su equipo, incluyendo el motivo del cambio y comentarios.
- **Justificación:** Permite capturar la intención del cambio desde la fuente (el TL) de manera estructurada.
- **Complejidad:** Baja (4/10)
- **Estimación:** 7 horas
- **Pruebas:** 
  - Integración: Validación de permisos (JWT) para asegurar que solo TLs/Admins accedan.

### 4.3. Buscador de Agentes y Turnos Actuales para TLs (Backend)
- **Descripción:** Servicio optimizado para que el TL busque agentes por nombre o DNI y obtenga su turno actual para el día solicitado antes de generar el cambio.
- **Justificación:** Proporciona visibilidad inmediata al TL sobre "qué está intentando cambiar".
- **Complejidad:** Baja (3/10)
- **Estimación:** 6 horas
- **Pruebas:** 
  - Integración: Prueba de rendimiento con búsqueda parcial (ilike).

### 4.4. API: Bandeja de Gestión de Solicitudes (Analista) (Backend)
- **Descripción:** Endpoints para listar solicitudes pendientes filtradas por segmento y para procesar (Aprobar/Rechazar) una solicitud específica.
- **Justificación:** Centraliza el trabajo del analista de planificación en una "bandeja de entrada" operativa.
- **Complejidad:** Media (5/10)
- **Estimación:** 8 horas
- **Pruebas:** 
  - Integración: Auditoría automática del usuario que procesa la solicitud.

### 4.5. Motor Automático de Aplicación de Cambios (Backend)
- **Descripción:** Al aprobar una solicitud, el sistema debe actualizar automáticamente la tabla `Schedule` con el nuevo turno y recalcular las horas del agente, marcando el registro como `is_manual_edit=True`.
- **Justificación:** Elimina la necesidad de que el analista aplique el cambio dos veces (una en el workflow y otra en la planificación).
- **Complejidad:** Alta (7/10)
- **Estimación:** 9 horas
- **Pruebas:** 
  - Integración: Verificar persistencia en `Schedule` tras aprobación de `ShiftChangeRequest`.

### 4.6. UI: Dashboard de Mis Solicitudes (Vista TL) (Frontend)
- **Descripción:** Pantalla en Angular para el TL con el listado de sus peticiones enviadas y su estado actual mediante indicadores visuales de colores.
- **Justificación:** El TL necesita saber si sus peticiones ya fueron gestionadas para informar a sus agentes.
- **Complejidad:** Media (6/10)
- **Estimación:** 9 horas
- **Pruebas:** 
  - E2E: Flujo de creación de solicitud y verificación de aparición en la lista.

### 4.7. UI: Inbox de Aprobaciones (Vista Analista) (Frontend)
- **Descripción:** Interfaz tipo "Bandeja de Entrada" para el analista, con capacidad de ver detalles del cambio propuesto y botones de acción rápida.
- **Justificación:** Agiliza el proceso de aprobación masiva de cambios diarios.
- **Complejidad:** Media (6/10)
- **Estimación:** 9 horas
- **Pruebas:** 
  - E2E: Procesamiento de una solicitud y desaparición automática de la bandeja de pendientes.

### 4.8. Detalle del Cambio y Comparativa (Frontend)
- **Descripción:** Vista modal que muestra el "Antes" y "Después" del cambio solicitado, incluyendo el impacto potencial en la cobertura si se habilitan métricas en tiempo real.
- **Justificación:** Ayuda al analista a tomar una decisión informada basada en datos.
- **Complejidad:** Baja (4/10)
- **Estimación:** 7 horas
- **Pruebas:** 
  - E2E: Verificación visual de los tramos horarios comparados.

---

## Módulo 5: Seguimiento y Dashboard Forecaster (Actuals)
*Foco: Comparar el pronóstico con la realidad operativa para ajustar estrategias futuras.*

### 5.1. Refactorización Modelo `ActualsData` y Consolidación (Backend)
- **Descripción:** Migrar y optimizar la tabla para almacenar métricas reales (Llamadas, Atendidas, NDS, AHT) por intervalo de 30 min. Incluir índices por fecha y segmento para reportes rápidos.
- **Justificación:** Es el repositorio histórico que permite evaluar la calidad del pronóstico.
- **Complejidad:** Baja (3/10)
- **Estimación:** 6 horas
- **Pruebas:** 
  - Integración: Test de carga con grandes volúmenes de datos por intervalo.

### 5.2. API: Carga Masiva de Actuals (Multi-Sheet Excel) (Backend)
- **Descripción:** Desarrollar el parser para archivos Excel con múltiples hojas (ENTRANTES, ATENDIDAS, NDS, AHT). Debe normalizar los formatos de fecha y hora provenientes de diferentes sistemas CTI.
- **Justificación:** Automatiza la ingesta de datos reales sin entrada manual.
- **Complejidad:** Media (7/10)
- **Estimación:** 9 horas
- **Pruebas:** 
  - Unitarias: Validación de lectura de todas las pestañas y manejo de datos faltantes.

### 5.3. Servicio de Cálculo de Desviaciones Forecaster (Backend)
- **Descripción:** Motor de cálculo que compara `StaffingResult` (lo que se planeó) vs `ActualsData` (lo que pasó). Debe calcular la desviación absoluta y porcentual.
- **Justificación:** Identifica si el modelo de forecasting necesita recalibración.
- **Complejidad:** Media (6/10)
- **Estimación:** 8 horas
- **Pruebas:** 
  - Unitarias: Validar cálculo de desviación con muestras de datos reales vs planeados.

### 5.4. API: Endpoint de Resumen de Seguimiento (Backend)
- **Descripción:** Endpoint que entrega los datos comparativos listos para graficar, agrupados por día o rango de fechas.
- **Justificación:** Optimiza el envío de datos al frontend mediante agregaciones eficientes.
- **Complejidad:** Media (5/10)
- **Estimación:** 7 horas
- **Pruebas:** 
  - Integración: Verificación de estructura JSON optimizada para Chart.js.

### 5.5. UI: Dashboard de Seguimiento de Pronóstico (Frontend)
- **Descripción:** Desarrollo de gráficas comparativas (Llamadas Planeadas vs Reales) utilizando Chart.js en Angular, con filtros dinámicos por segmento.
- **Justificación:** Proporciona una visión ejecutiva inmediata de la efectividad del forecast.
- **Complejidad:** Alta (7/10)
- **Estimación:** 9 horas
- **Pruebas:** 
  - E2E: Cambio de filtros y actualización reactiva de las gráficas.

### 5.6. UI: Tabla de Cumplimiento por Intervalo (Heatmap) (Frontend)
- **Descripción:** Grid dinámico que resalta en colores las celdas con desviaciones críticas (ej: >15% en rojo, <5% en verde).
- **Justificación:** Permite al analista identificar exactamente en qué tramos del día falló el pronóstico.
- **Complejidad:** Media (6/10)
- **Estimación:** 8 horas
- **Pruebas:** 
  - E2E: Verificación de colores correctos según el umbral de desviación.

### 5.7. Exportador de Reporte de Calidad del Forecast (Backend)
- **Descripción:** Servicio para generar un archivo Excel detallado con todas las métricas de seguimiento y desviaciones para análisis externo.
- **Justificación:** Facilita la distribución de resultados a los interesados sin acceso a la plataforma.
- **Complejidad:** Baja (4/10)
- **Estimación:** 7 horas
- **Pruebas:** 
  - Integración: Validación de formato y cálculos en el archivo generado.

---

## Módulo 6: Reporting Ejecutivo y Resumen de KPIs
*Foco: Consolidación de métricas de alto nivel para la toma de decisiones gerenciales.*

### 6.1. Engine de Agregación de Cobertura por Intervalo (Backend)
- **Descripción:** Implementar el servicio que suma los agentes presentes en cada intervalo de 30 min y aplica la cadena de resta de reductores (absentismo, shrinkage, auxiliares) para obtener el "Headcount Efectivo".
- **Justificación:** Es el dato de entrada fundamental para cualquier cálculo de nivel de servicio.
- **Complejidad:** Media (6/10)
- **Estimación:** 8 horas
- **Pruebas:** 
  - Unitarias: Validación de la suma de agentes cruzada con la tabla de `Schedule`.

### 6.2. Lógica de Métricas Backoffice (Backend)
- **Descripción:** Implementar cálculos específicos para segmentos que no son de llamadas: Productividad, Déficit/Superávit de tareas y capacidad de gestión horaria.
- **Justificación:** El sistema debe ser capaz de medir la eficiencia en canales no asíncronos (emails, backoffice).
- **Complejidad:** Media (5/10)
- **Estimación:** 7 horas
- **Pruebas:** 
  - Unitarias: Validación de cálculo de capacidad basada en horas efectivas y AHT de tarea.

### 6.3. API: Generador de Tablas de Resumen Multi-Día (Backend)
- **Descripción:** Endpoint que unifica todas las métricas (Planificado, Efectivo, Llamadas, SL, NDA) en un JSON estructurado por días para un rango de fechas.
- **Justificación:** Optimiza la carga en el frontend al entregar los datos pre-procesados y listos para mostrar.
- **Complejidad:** Media (6/10)
- **Estimación:** 8 horas
- **Pruebas:** 
  - Integración: Test de tiempo de respuesta para rangos de 31 días (un mes completo).

### 6.4. UI: Grid Dinámico de Resumen de Operación (Frontend)
- **Descripción:** Desarrollo de la tabla maestra en Angular que muestra las métricas por intervalo. Debe soportar el cambio entre diferentes tablas (Planificados, Efectivos, SLA, etc.).
- **Justificación:** Es la "hoja de balance" que el planificador consulta constantemente para validar su trabajo.
- **Complejidad:** Alta (8/10)
- **Estimación:** 9 horas
- **Pruebas:** 
  - E2E: Verificación de que el cambio entre tablas no recarga la página y es instantáneo (Signals).

### 6.5. Sistema de Heatmap de KPIs (Frontend)
- **Descripción:** Implementar la lógica de pintado dinámico en la tabla de KPIs. Las celdas deben colorearse automáticamente según si cumplen o no el objetivo definido en el dimensionamiento.
- **Justificación:** Proporciona una señal visual inmediata de los tramos horarios críticos que necesitan refuerzo.
- **Complejidad:** Media (6/10)
- **Estimación:** 8 horas
- **Pruebas:** 
  - E2E: Verificación de que un SL del 70% se pinta en rojo si el objetivo es 80%.

### 6.6. Dashboard de KPIs de Adherencia y Absentismo (Frontend)
- **Descripción:** Creación de tarjetas de resumen ejecutivo (Cards) que muestran porcentajes globales del período solicitado: Adherencia Bruta/Neta y promedio de ausencias (VAC/BMED).
- **Justificación:** Ofrece una visión rápida del "estado de salud" del segmento planificado.
- **Complejidad:** Baja (4/10)
- **Estimación:** 8 horas
- **Pruebas:** 
  - E2E: Comparativa de totales de la tabla vs totales de las tarjetas de resumen.

### 6.7. Exportador XLS de Resumen Ejecutivo (Backend)
- **Descripción:** Generación de un archivo Excel con múltiples pestañas, replicando todas las tablas del resumen operativo para informes externos.
- **Justificación:** Es el entregable final que el analista suele enviar a la dirección operativa.
- **Complejidad:** Media (5/10)
- **Estimación:** 7 horas
- **Pruebas:** 
  - Integración: Validación de que las fórmulas en Excel coinciden con los cálculos internos del sistema.

---

## Módulo 7: Gestión de Agentes y Administración Operativa
*Foco: Mantenimiento de la base de datos de personal y control de acceso.*

### 7.1. Refactorización del Modelo `Agent` y Perfilado (Backend)
- **Descripción:** Migrar la entidad `Agent` añadiendo campos profesionales: centro de coste, modalidad de contrato, fecha de alta/baja y vinculación con reglas de planificación.
- **Justificación:** Un modelo de agente enriquecido permite segmentar la planificación según habilidades y costos.
- **Complejidad:** Baja (3/10)
- **Estimación:** 6 horas
- **Pruebas:** 
  - Unitarias: Validación de formatos de identificación (DNI/NIE).
  - Integración: Test de integridad relacional con segmentos.

### 7.2. API: CRUD de Agentes y Cambio de Segmento (Backend)
- **Descripción:** Endpoints para la creación, edición y eliminación de agentes. Incluye la lógica para mover un agente de un segmento a otro manteniendo su histórico.
- **Justificación:** La movilidad interna entre campañas es constante en un BPO; el sistema debe gestionarlo sin perder datos.
- **Complejidad:** Media (4/10)
- **Estimación:** 7 horas
- **Pruebas:** 
  - Unitarias: Verificación de que al mover un agente no se dupliquen sus registros en la nueva campaña.

### 7.3. UI: Gestión de Plantilla (Grid Maestro) (Frontend)
- **Descripción:** Tabla interactiva en Angular para visualizar a todos los agentes. Incluye búsqueda global, filtros por campaña y acciones rápidas (editar/baja).
- **Justificación:** Es la herramienta principal para mantener actualizada la plantilla operativa.
- **Complejidad:** Media (5/10)
- **Estimación:** 8 horas
- **Pruebas:** 
  - E2E: Flujo de búsqueda de agente, edición de su jornada y guardado exitoso.

### 7.4. Lógica de "Bajas Programadas" (Backend)
- **Descripción:** Implementar la lógica para que el sistema deje de planificar a un agente a partir de su `fecha_baja`, sin borrar sus datos históricos previos.
- **Justificación:** Evita errores operativos de planificar a personas que ya no pertenecen a la empresa.
- **Complejidad:** Media (5/10)
- **Estimación:** 8 horas
- **Pruebas:** 
  - Unitarias: Verificación de que el Scheduler ignora agentes tras su fecha de baja.

### 7.5. Sistema de Control de Acceso por Roles (RBAC) (Backend)
- **Descripción:** Implementar permisos granulares en la API: `ADMIN` (acceso total), `ANALISTA` (solo planificación) y `SOLICITANTE/TL` (solo cambios de turno).
- **Justificación:** Garantiza la seguridad de la información y evita cambios no autorizados en la configuración global.
- **Complejidad:** Media (6/10)
- **Estimación:** 9 horas
- **Pruebas:** 
  - Integración: Intento de acceso a rutas administrativas con token de perfil bajo.

### 7.6. UI: Panel de Administración de Usuarios y Permisos (Frontend)
- **Descripción:** Interfaz para que los administradores vinculen usuarios de AD con campañas específicas.
- **Justificación:** Configuración de silos de información: un supervisor de "Campaña A" no debe ver datos de la "Campaña B".
- **Complejidad:** Media (6/10)
- **Estimación:** 8 horas
- **Pruebas:** 
  - E2E: Asignación de permisos a un usuario y verificación de visibilidad de campañas en su sesión.

### 7.7. Importador Masivo de Agentes con Mapeo de Campos (Backend)
- **Descripción:** Parser avanzado de Excel que permite cargar cientos de agentes a la vez, validando en tiempo real si su configuración horaria es compatible con su segmento.
- **Justificación:** Imprescindible para el "Onboarding" masivo de nuevas campañas.
- **Complejidad:** Media (7/10)
- **Estimación:** 9 horas
- **Pruebas:** 
  - Integración: Carga de archivo con 500 agentes y validación de tiempos de procesamiento.

---

## Resumen de Estimación Final

| Módulo | Total Horas |
| :--- | :--- |
| Módulo 1: Administración y Maestros | 72h |
| Módulo 2: Gestión de Ausencias (BDB) | 65h |
| Módulo 3: Detalle Intradía (Breaks/PVD) | 69h |
| Módulo 4: Workflow de Cambios | 63h |
| Módulo 5: Seguimiento (Actuals) | 54h |
| Módulo 6: Reporting Ejecutivo | 55h |
| Módulo 7: Gestión de Agentes | 55h |
| **TOTAL ESTIMADO** | **433 Horas** |

**Tiempo total estimado de desarrollo:** Aproximadamente **9.8 semanas** (basado en una jornada laboral de 44 horas semanales).
