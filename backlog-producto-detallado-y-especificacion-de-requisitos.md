Plan de Desarrollo del Backlog de Producto Detallado  (SIPO MVP)

Fase 1: Fundación y Configuración (Semanas 1-4)
Objetivo General de la Fase: Construir una aplicación funcionalmente esquelética que maneje toda la entrada y configuración de datos. Al final de la fase, la aplicación podrá aceptar todos los inputs del usuario, pero aún no procesará la lógica de negocio principal.
Semana 1 de 15: Establecimiento de Cimientos Técnicos
Horas de la Semana: 44
Objetivo de la Semana: Crear, configurar y desplegar una versión "Hola Mundo" de la aplicación, estableciendo el flujo CI/CD básico.
Tareas de Desarrollo:
Backend (Spring Boot) - Setup (12h):
Inicializar el proyecto Spring Boot con Spring Initializr (dependencias: Spring Web, Lombok).
Crear la estructura de paquetes (controller, service, model, config).
Crear un HealthCheckController simple que retorne {"status": "UP"}.
Configurar application.properties para el puerto del servidor.
Frontend (Angular) - Setup (12h):
Inicializar el proyecto Angular con ng new.
Crear la estructura de módulos y componentes base (ej. layout, header, home-page).
Configurar el enrutamiento básico (app-routing.module.ts).
Configurar el proxy (proxy.conf.json) para redirigir las llamadas a la API al backend en el entorno de desarrollo.
Dockerización (12h):
Crear un Dockerfile para el backend que compile el proyecto Maven y ejecute el JAR.
Crear un Dockerfile multi-etapa para el frontend que compile la aplicación Angular y sirva los archivos estáticos con Nginx.
Integración y Despliegue Inicial (8h):
Crear un archivo docker-compose.yml que levante ambos servicios (frontend y backend).
Verificar que la aplicación Angular puede hacer una llamada al endpoint de HealthCheck del backend y mostrar el estado en la página principal.
Semana 2 de 15: Implementación Robusta de Carga de Archivos
Horas de la Semana: 44
Objetivo de la Semana: Construir la funcionalidad de carga de archivos de demanda y horarios, incluyendo validaciones exhaustivas en el backend.
Tareas de Desarrollo:
Backend - Endpoint y Servicio de Archivos (30h):
Añadir la dependencia de Apache POI al pom.xml.
Crear un FileController con un endpoint @PostMapping que acepte MultipartFile.
Crear un ExcelParsingService. Dentro de este servicio:
Función parseDemandFile(file): Itera sobre las filas, valida la presencia y el nombre exacto de las columnas (Fecha, Intervalo_de_Tiempo, etc.), y valida el tipo de dato de cada celda (ej. que Llamadas_Esperadas sea numérico).
Crear DTOs (Data Transfer Objects) para representar los datos de la demanda y las respuestas de error.
Implementar un manejo de excepciones robusto (ej. try-catch para IOException, InvalidFormatException).
Crear pruebas unitarias para el ExcelParsingService con archivos Excel de prueba (uno correcto, uno con columnas faltantes, uno con datos incorrectos).
Frontend - Interfaz de Carga de Demanda (14h):
Crear un FileUploadComponent en Angular.
Diseñar la UI: un área para arrastrar y soltar, un botón de selección de archivo y un área para mostrar mensajes de estado.
Crear un ApiService en Angular para manejar las peticiones HTTP.
Implementar la lógica en el componente para llamar al servicio, gestionar el estado de "cargando" y mostrar los mensajes de éxito o error devueltos por el backend.
Semana 3 de 15: Generalización de Cargas y Configuración de UI
Horas de la Semana: 44
Objetivo de la Semana: Extender la funcionalidad de carga para los otros archivos y construir el formulario de configuración.
Tareas de Desarrollo:
Backend - Extensión del Servicio de Archivos (18h):
Crear nuevos endpoints y funciones en el FileController y ExcelParsingService para los archivos de Horarios Base y Concesiones.
Reutilizar la estructura de parsing y validación, adaptándola a las nuevas columnas y reglas.
Crear pruebas unitarias para las nuevas funciones de parsing.
Frontend - Reutilización de Componentes de Carga (10h):
Adaptar el FileUploadComponent para que sea reutilizable o crear instancias separadas para cada tipo de archivo, conectándolos a sus respectivos endpoints.
Frontend - Formulario de Configuración (16h):
Crear un ConfigurationFormComponent usando ReactiveFormsModule.
Añadir todos los controles (desplegables, inputs numéricos) con sus validaciones del lado del cliente (ej. Validators.required, Validators.min(1)).
Semana 4 de 15: Gestión de Estado y Lógica de UI
Horas de la Semana: 44
Objetivo de la Semana: Unir todas las piezas de la UI, gestionando el estado global de la aplicación para crear una experiencia de usuario coherente.
Tareas de Desarrollo:
Frontend - Servicio de Estado de Planificación (28h):
Crear un PlanningStateService en Angular (usando un BehaviorSubject o una solución de gestión de estado como NgRx/Akita si la complejidad lo justifica).
Este servicio almacenará el estado: ¿se cargó el archivo de demanda? ¿y el de horarios? ¿cuáles son los parámetros del formulario?
Modificar los componentes para que actualicen este servicio centralizado después de cada acción exitosa del usuario.
Frontend - Lógica Condicional de UI (16h):
Implementar la lógica en el ConfigurationFormComponent para que se suscriba al estado y muestre/oculte el campo "Tiempo Medio de Paciencia".
Implementar la lógica en el componente principal para que el botón "Generar Planificación" se suscriba al estado y se habilite/deshabilite automáticamente.
Estado al Final de la Fase 1:
Una aplicación web robusta con un flujo de usuario claro para la carga y configuración de datos.
Validaciones exhaustivas en el backend para garantizar la integridad de los datos de entrada.
Una arquitectura de frontend limpia basada en la gestión de estado.
Fase 2: Implementación del Motor de Reglas (Semanas 5-10)
Objetivo General de la Fase: Implementar, probar y refinar todos los algoritmos de backend necesarios para procesar los datos de entrada y generar una planificación de horarios detallada y optimizada. Al final de la fase, existirá un endpoint de API que, al recibir los datos de entrada, devolverá la planificación completa.
Semana 5 de 15: Arquitectura del Motor y Lógica de Breaks (Parte 1)
Horas de la Semana: 44
Objetivo de la Semana: Diseñar la estructura del motor de procesamiento en el backend y desarrollar la lógica fundamental para el cálculo y asignación de descansos.
Tareas de Desarrollo:
Backend - Diseño de la Arquitectura del Motor (18h):
Crear la clase PlanningOrchestratorService que será el punto de entrada para la generación de la planificación.
Definir los modelos de dominio (POJOs - Plain Old Java Objects) que representarán la estructura de datos: PlanningSession, AdvisorSchedule, TimeSlot, ActivityType (Enum: WORK, BREAK, PVD).
Crear las interfaces para los servicios de reglas: BreakAssignmentRule, PvdAssignmentRule, etc., para fomentar un diseño desacoplado.
Backend - Utilidad de Cálculo de Duración (16h):
Crear una clase de utilidad ShiftCalculator con un método estático calculateDuration(startTime, endTime).
Implementar la lógica para manejar turnos que cruzan la medianoche.
Añadir pruebas unitarias exhaustivas con múltiples casos de borde (ej. turno de 23:00 a 07:00, turno de 1 hora, etc.).
Backend - Implementación de Reglas de Duración de Breaks (10h):
Crear una implementación BreakDurationRuleImpl que tome el país y la duración del turno.
Codificar la lógica switch-case o if-else para las reglas de Colombia y España.
Añadir pruebas unitarias que verifiquen la duración correcta para cada caso en ambos países.
Semana 6 de 15: Algoritmo de Colocación de Breaks (Turnos Continuos)
Horas de la Semana: 44
Objetivo de la Semana: Desarrollar y probar el algoritmo que coloca el descanso en el lugar óptimo para el caso más común: un turno de trabajo continuo.
Tareas de Desarrollo:
Backend - Diseño del Algoritmo (12h):
Definir la estrategia: calcular el punto medio del turno, luego iterar hacia adelante y hacia atrás para encontrar un "slot" que cumpla con las restricciones de tiempo (2h desde el inicio, 1.5h antes del fin).
Backend - Implementación del Algoritmo (24h):
En una clase BreakPlacementServiceImpl, implementar la lógica diseñada.
La función tomará como entrada el objeto AdvisorSchedule y la duración del break, y modificará el horario del asesor para incluir la actividad de "Break".
Backend - Pruebas Unitarias Exhaustivas (8h):
Crear pruebas para turnos de diferentes duraciones, asegurando que el break se coloque siempre en una posición válida y óptima. Probar casos límite (ej. un turno de 4 horas donde el break tiene una ventana de colocación muy pequeña).
Semana 7 de 15: Lógica de Breaks (Turnos Segmentados - Parte 1)
Horas de la Semana: 44
Objetivo de la Semana: Extender la lógica de breaks para manejar el complejo escenario de los turnos segmentados, implementando las diferentes estrategias de colocación.
Tareas de Desarrollo:
Backend - Refactorización para Turnos Segmentados (8h):
Ajustar el modelo AdvisorSchedule para que pueda representar claramente un turno con uno o dos segmentos de trabajo.
Backend - Implementación de Estrategia A (18h):
Implementar la lógica para la "Estrategia A": Asignar el break completo en el segmento de mayor duración. Esto implica reutilizar el algoritmo de la semana 6, pero aplicándolo solo al segmento más largo.
Backend - Implementación de Estrategia B (18h):
Implementar la lógica para la "Estrategia B": Dividir el break en dos (si es divisible) y colocar cada mitad en uno de los segmentos, aplicando las reglas de colocación a cada parte.
Semana 8 de 15: Lógica de Breaks (Turnos Segmentados - Parte 2, Simulación)
Horas de la Semana: 44
Objetivo de la Semana: Construir el "cerebro" de la asignación inteligente: el simulador que decide qué estrategia de colocación de break es la mejor.
Tareas de Desarrollo Detalladas:
Backend - Desarrollo del Simulador (30h):
Crear una clase PlacementSimulator.
Su método principal recibirá el estado actual de la planificación (el sobre_sub por intervalo).
Implementará la lógica para:
Clonar el horario del asesor.
Aplicar la Estrategia A al clon y calcular el sobre_sub resultante.
Clonar de nuevo el horario original.
Aplicar la Estrategia B al segundo clon y calcular su sobre_sub resultante.
Comparar los resultados y devolver la estrategia ganadora.
Backend - Pruebas del Simulador (14h):
Crear pruebas unitarias que preparen un escenario de sobre_sub y verifiquen que el simulador elige la opción correcta.
Semana 9 de 15: Lógica de PVDs y Validaciones Finales
Horas de la Semana: 44
Objetivo de la Semana: Implementar la lógica de negocio específica para España (PVDs) y las validaciones de cumplimiento normativo.
Tareas de Desarrollo:
Backend - Implementación de Asignación de PVDs (30h):
Crear un PvdAssignmentServiceImpl.
Implementar el cálculo del número de PVDs.
Implementar el algoritmo de distribución uniforme, asegurando que respeta el espaciado y no colisiona con el break ya asignado.
(Versión simplificada de la optimización): El algoritmo priorizará colocar los PVDs en intervalos donde el sobre_sub sea más alto.
Backend - Implementación de Validaciones (14h):
Crear un ValidationServiceImpl.
Implementar el método que verifica los límites de horas por país, consultando la lista de concesiones para la excepción de España.
Este servicio no modificará los datos, solo devolverá una lista de objetos Warning.
Semana 10 de 15: Orquestación e Integración del Motor
Horas de la Semana: 44
Objetivo de la Semana: Unir todas las piezas del motor de reglas en un único flujo de trabajo coherente.
Tareas de Desarrollo Detalladas:
Backend - Implementación del Orquestador (30h):
En PlanningOrchestratorService, crear el método generatePlan().
Este método iterará sobre cada AdvisorSchedule cargado.
Verificará si el asesor tiene concesión. Si no:
Llamará al servicio de breaks.
Si el país es España, llamará al servicio de PVDs.
Llamará al servicio de validación para todos los asesores.
Recopilará todos los horarios modificados y las advertencias.
Backend - Creación del Endpoint Principal (14h):
Crear el PlanningController con un endpoint @PostMapping("/generate") que reciba todos los datos de entrada (archivos y configuración).
Este endpoint llamará al orquestador y devolverá el resultado completo en una estructura JSON bien definida.
Estado al Final de la Fase 2:
El backend expone una API RESTful que puede procesar una solicitud de planificación completa y devolver un resultado estructurado.
Toda la lógica de negocio compleja está implementada y cubierta por pruebas unitarias.
La aplicación está lista para que el frontend consuma los resultados.
Fase 3: Análisis, Visualización y Finalización (Semanas 11-15)
Objetivo General de la Fase: Conectar el frontend a la API de generación de planificación, procesar los resultados, presentarlos de manera clara e intuitiva en un dashboard, e implementar las funcionalidades de guardado y exportación. Al final de esta fase, el MVP estará completo y listo para las pruebas de aceptación del usuario (UAT).
Semana 11 de 15: Conexión Frontend-Backend y Cálculos Analíticos
Horas de la Semana: 44
Objetivo de la Semana: Establecer la comunicación entre el frontend y el endpoint de generación del backend, y desarrollar los servicios de cálculo que procesarán la respuesta.
Tareas de Desarrollo:
Backend - Cálculos Analíticos (24h):
Crear un AnalyticsService en el backend.
Este servicio tomará la planificación ya generada (con todos los horarios detallados) y realizará los cálculos finales para cada intervalo: Asesores Efectivos Requeridos (usando una librería Erlang como jErlang), Asesores Dimensionados, Call Capacity, sobre_sub, etc.
Integrar este servicio en el PlanningOrchestratorService para que el DTO de respuesta final incluya todas estas métricas.
Frontend - Integración de API (20h):
En el ApiService de Angular, crear un método generatePlan(planningData).
Este método construirá el objeto de solicitud complejo que necesita el backend (combinando los datos de los archivos y los parámetros del formulario).
Modificar el componente principal para que, al hacer clic en "Generar Planificación", llame a este nuevo método.
Implementar la gestión de la respuesta: recibir el JSON masivo del backend y almacenarlo en el PlanningStateService.
Semana 12 de 15: Construcción del Dashboard (Tabla de Datos)
Horas de la Semana: 44
Objetivo de la Semana: Desarrollar el componente principal de visualización de resultados: la tabla detallada de métricas por intervalo.
Tareas de Desarrollo:
Frontend - Creación del Componente de Dashboard (9h):
Crear una nueva página/ruta en Angular para el DashboardComponent.
El componente se suscribirá a los resultados de la planificación almacenados en el PlanningStateService.
Frontend - Implementación de la Tabla de Métricas (35h):
Utilizar una librería de tablas robusta (como Angular Material Table o AG Grid) para presentar los datos.
Configurar las columnas: Intervalo, Llamadas_Esperadas, Asesores_Requeridos, Asesores_Dimensionados, sobre_sub, etc.
Implementar el formato condicional para la columna sobre_sub (rojo para negativos, verde/azul para positivos).
Añadir funcionalidades a la tabla como ordenación por columna.
Semana 13 de 15: Construcción del Dashboard (Gráficos y Advertencias)
Horas de la Semana: 44
Objetivo de la Semana: Completar el dashboard añadiendo las visualizaciones gráficas y la presentación de advertencias.
Tareas de Desarrollo:
Frontend - Integración de Gráficos (30h):
Integrar una librería de gráficos (como Chart.js o ng2-charts).
Crear un ChartComponent que consuma los datos del estado de la planificación.
Configurar el gráfico de líneas/barras para mostrar Asesores Dimensionados vs. Asesores Efectivos Requeridos a lo largo del tiempo.
Frontend - Visualización de Advertencias (14h):
Crear un WarningsComponent.
Este componente se suscribirá a la lista de advertencias del estado de la planificación.
Mostrará las advertencias de forma clara y visible en la parte superior del dashboard si existen.
Semana 14 de 15: Funcionalidades de Exportación y Guardado
Horas de la Semana: 44
Objetivo de la Semana: Implementar las funcionalidades finales que permiten al usuario actuar sobre la planificación generada.
Tareas de Desarrollo:
Frontend - Modal y Lógica de Filtrado para Exportación (18h):
Crear un modal (ventana emergente) para las "Opciones de Exportación".
Poblar el modal con los filtros de fecha y la lista de asesores con opción de búsqueda.
Backend - Endpoint de Exportación (26h):
Crear un ExportController con un endpoint que reciba los criterios de filtrado.
Implementar la lógica para filtrar la planificación guardada en sesión.
Utilizar Apache POI para generar dinámicamente el archivo .xlsx con la matriz de horarios.
Configurar la respuesta HTTP para que el navegador inicie la descarga del archivo.
(Tarea de baja prioridad si el tiempo apremia) Backend - Endpoint de Guardado:
Crear el endpoint y el servicio para persistir el objeto de planificación en la base de datos NoSQL.
Semana 15 de 15: Pruebas End-to-End, Refinamiento y Preparación para Entrega
Horas de la Semana: 44
Objetivo de la Semana: Realizar pruebas completas del flujo de usuario, corregir bugs, refinar la interfaz y preparar la documentación para la entrega.
Tareas de Desarrollo Detalladas:
Pruebas de Flujo Completo (6h):
Realizar pruebas manuales de todo el proceso: cargar archivos -> configurar -> generar -> analizar -> exportar. Probar con diferentes conjuntos de datos.
Corrección de Bugs y Refinamiento de UI (32h):
Solucionar los problemas encontrados durante las pruebas.
Ajustar estilos, espaciados y mensajes para mejorar la experiencia de usuario.
Documentación de Entrega (8h):
Finalizar el documento de "Guía de Despliegue", asegurando que los pasos en el docker-compose.yml son correctos y están bien explicados.
Estado al Final de la Fase 3 y del Proyecto:
El MVP del SIPO está completamente funcional y cumple con todos los requisitos definidos.
La aplicación ha sido probada de principio a fin.
El proyecto está listo para ser presentado al equipo de WFM para las Pruebas de Aceptación de Usuario (UAT).

Especificación de Requisitos de Software (SRS): Sistema Integral de Planificación y Optimización (SIPO)
Versión: 1.0
Fecha: 09 de septiembre de 2025
Proyecto: Desarrollo de una solución a medida para la planificación de horarios y gestión de la capacidad.

1. Introducción
1.1. Propósito
Este documento proporciona una especificación detallada de los requisitos funcionales y no funcionales para el Sistema Integral de Planificación y Optimización (SIPO), Versión 1.0 (MVP). Está destinado a ser utilizado por el equipo de desarrollo como la guía definitiva para la implementación del sistema y por el equipo de WFM para la validación y las pruebas de aceptación del usuario (UAT). Describe el qué (qué hará el sistema) y no el cómo (cómo se implementará).
1.2. Alcance del Producto
El SIPO es una aplicación web interna, diseñada para automatizar y optimizar el proceso de creación de horarios y gestión de capacidad para los asesores de contact center de Emergia en Colombia y España. El sistema reemplazará el actual proceso manual basado en Microsoft Excel, proporcionando una solución centralizada, flexible y basada en reglas para gestionar las complejidades de la planificación multi-país y multi-cliente. El alcance detallado, incluyendo las funcionalidades explícitamente excluidas, se define en el "Documento de Visión y Alcance: SIPO, V1.0".
1.3. Definiciones, Acrónimos y Abreviaturas
AHT (Average Handle Time): Tiempo Medio de Operación. Tiempo promedio que un asesor dedica a una llamada, incluyendo conversación y trabajo post-llamada.
Asesores Dimensionados: Número de asesores con un horario asignado y disponibles para atender llamadas en un intervalo de tiempo específico.
Asesores Efectivos Requeridos: Número teórico de asesores necesarios para cumplir un nivel de servicio, calculado mediante un modelo Erlang.
Call Capacity: Cantidad máxima de llamadas que los asesores dimensionados pueden atender en un intervalo de tiempo.
Erlang (B, C, A): Familia de modelos matemáticos utilizados en la ingeniería de tráfico para calcular el número de recursos (líneas/agentes) necesarios para manejar un volumen de tráfico determinado.
MVP (Minimum Viable Product): Producto Mínimo Viable. La versión del SIPO con el conjunto de características suficientes para ser funcional y aportar valor al usuario final.
PVD (Pausa Voluntaria de Desconexión): Actividad auxiliar no remunerada, específica de la operación en España, distribuida a lo largo del turno.
SIPO: Sistema Integral de Planificación y Optimización. El nombre de este proyecto de software.
SLA (Service Level Agreement): Acuerdo de Nivel de Servicio. Contrato que define el nivel de calidad que Emergia se compromete a ofrecer a sus clientes.
sobre_sub: Métrica que representa la diferencia numérica entre los Asesores Dimensionados y los Asesores Efectivos Requeridos. Un valor positivo indica sobrecobertura y un valor negativo, infracobertura.
WFM (Workforce Management): Gestión de la Fuerza de Trabajo. La disciplina de planificar y gestionar el personal para asegurar que el número correcto de personas con las habilidades adecuadas esté en el lugar correcto en el momento correcto.
1.4. Referencias
Caso de Negocio: SIPO, V2.0
Acta de Constitución del Proyecto: SIPO
Documento de Visión y Alcance: SIPO, V1.0
1.5. Vista General del Documento
Este documento está organizado de la siguiente manera: la Sección 1 proporciona una introducción general. La Sección 2 describe la perspectiva general del producto, sus funciones, usuarios y restricciones. La Sección 3 contiene los requisitos específicos y detallados, incluyendo los requisitos funcionales, los requisitos de la interfaz externa y los requisitos no funcionales, que son la parte central de este SRS.
2. Descripción General
2.1. Perspectiva del Producto
El SIPO será una aplicación web completamente nueva y autocontenida. Se desarrollará desde cero y no es una extensión de ningún sistema existente. Su función principal es reemplazar por completo el proceso de planificación basado en Excel. Interactuará con los usuarios a través de un navegador web estándar y sus únicas interfaces externas serán para la importación y exportación de archivos en formato .xlsx.
2.2. Funciones del Producto
Las principales funciones que el SIPO proporcionará al usuario son:
Importación de Datos: Carga de datos de demanda y horarios base desde archivos Excel.
Configuración de la Planificación: Parametrización de las variables clave para una sesión de planificación (intervalos, modelo Erlang, SLAs).
Generación de Horarios: Creación automática de horarios detallados, aplicando reglas de negocio para descansos (Breaks) y PVDs.
Análisis de Capacidad: Cálculo y visualización de todas las métricas de WFM relevantes para evaluar la calidad de la planificación.
Persistencia y Exportación: Guardado de los resultados en una base de datos y exportación de los horarios finales a un archivo Excel.
2.3. Características del Usuario
El usuario principal es el Planificador de WFM. Se asume que este usuario tiene un profundo conocimiento de los conceptos de WFM (Erlang, SLAs, AHT, etc.) pero no necesariamente posee habilidades técnicas avanzadas en software. Por lo tanto, la interfaz del sistema debe ser altamente intuitiva y orientada a los procesos de negocio que ya conoce.
2.4. Restricciones Generales
Constraint-TEC-01: El sistema debe desarrollarse utilizando el stack tecnológico definido: Frontend en Angular con TypeScript, Backend en Spring Boot (Java), y empaquetado en contenedores Docker.
Constraint-TEC-02: La base de datos para la persistencia de datos debe ser de tipo NoSQL (ej. MongoDB o similar).
Constraint-DATA-01: El sistema debe ser capaz de leer y escribir archivos en formato Microsoft Excel (.xlsx) como principal medio de intercambio de datos.
Constraint-DEV-01: El desarrollo será ejecutado por un único practicante universitario supervisado, lo que implica que la complejidad de la arquitectura y las funcionalidades debe ser manejable dentro de este marco.
Constraint-TIME-01: Un Producto Mínimo Viable (MVP) que cumpla con todos los requisitos de este documento debe ser entregado en un plazo de 4 meses.
2.5. Supuestos y Dependencias
ASSUMP-01: Se asume que los datos en los archivos Excel de entrada (demanda y horarios) son precisos, completos y están en el formato correcto. La validación de la lógica de negocio de los datos (ej. si un AHT es realista) está fuera del alcance del sistema.
DEP-01: El proyecto depende de la disponibilidad del personal de WFM para participar en las sesiones de refinamiento de requisitos y para ejecutar las Pruebas de Aceptación del Usuario (UAT) de manera oportuna.
Entendido. Esa es una excelente observación de diseño. Trasladar la selección del país a la interfaz, en lugar de inferirla de los datos, hace que el proceso sea más explícito, menos propenso a errores por datos sucios y más flexible para futuras expansiones.
Procedo a reescribir la sección del primer módulo incorporando este cambio fundamental. La lógica del archivo de horarios se simplifica, y la configuración de la planificación se vuelve más central.
3.1. Requisitos Funcionales
3.1.1. Módulo 1: Configuración e Importación de Datos
RF-001: Carga de Archivo de Demanda
Descripción: El sistema debe proporcionar una interfaz que permita al usuario seleccionar y cargar un archivo en formato .xlsx desde su equipo local. Este archivo contendrá la previsión de la demanda.
Entrada: Un archivo .xlsx.
Proceso: El sistema deberá leer los datos del archivo cargado.
Salida: Los datos de demanda (fecha, intervalo, llamadas, AHT) deben quedar almacenados en la memoria temporal de la sesión de planificación.
Requerimientos Específicos:
RF-001.1: El sistema debe validar que el archivo cargado tenga la extensión .xlsx. Si no es así, debe mostrar el mensaje de error: "Error: El archivo debe tener formato .xlsx".
RF-001.2: El sistema debe validar que la hoja de cálculo contenga las columnas obligatorias con los siguientes encabezados exactos: Fecha, Intervalo_de_Tiempo, Llamadas_Esperadas, AHT_Promedio. Si falta alguna columna o el nombre no coincide, debe mostrar un mensaje de error listando las columnas faltantes/incorrectas.
RF-001.3: El sistema debe mostrar un indicador de progreso durante la carga y procesamiento del archivo.
RF-001.4: Al finalizar la carga exitosamente, el sistema debe mostrar un mensaje de confirmación: "Archivo de demanda cargado correctamente. Se han procesado X registros."
RF-002: Carga de Archivo de Horarios Base
Descripción: El sistema debe proporcionar una interfaz que permita al usuario seleccionar y cargar un archivo en formato .xlsx. Este archivo contendrá los turnos base de los asesores. Nota: Este archivo ya no necesita la columna Pais.
Entrada: Un archivo .xlsx.
Proceso: El sistema deberá leer los datos del archivo cargado.
Salida: Los datos de los turnos (ID asesor, nombre, fecha, inicio, fin) deben quedar almacenados en la memoria temporal de la sesión de planificación.
Requerimientos Específicos:
RF-002.1: El sistema debe validar la extensión .xlsx del archivo, mostrando un error si no coincide.
RF-002.2: El sistema debe validar que la hoja de cálculo contenga las columnas obligatorias: ID_Asesor, Nombre_Asesor, Fecha, Hora_Inicio_Turno, Hora_Fin_Turno. Si hay errores, debe notificar al usuario de forma específica.
RF-002.3: Tras una carga exitosa, debe mostrar el mensaje: "Archivo de horarios cargado correctamente. Se han procesado X asesores."
RF-003: Configuración de Parámetros de Planificación
Descripción: Antes de ejecutar la generación de horarios, el sistema debe presentar al usuario un formulario para configurar los parámetros de la simulación.
Entrada: Valores seleccionados/introducidos por el usuario.
Proceso: El sistema guardará estos parámetros para utilizarlos en los cálculos posteriores y para determinar qué conjunto de reglas de negocio aplicar.
Salida: Los parámetros de la planificación quedan definidos para la sesión.
Requerimientos Específicos:
RF-003.1: El formulario debe contener un campo desplegable llamado "País de la Planificación" con las opciones: "Colombia", "España". Esta selección determinará qué reglas de negocio se aplicarán a TODOS los horarios cargados en la sesión actual. El valor por defecto será "Colombia".
RF-003.2: El formulario debe contener un campo desplegable llamado "Granularidad de Intervalo (minutos)" con las opciones: "15", "30", "60". El valor por defecto será "30".
RF-003.3: El formulario debe contener un campo desplegable llamado "Modelo de Cálculo" con las opciones: "Erlang B", "Erlang C", "Erlang A". El valor por defecto será "Erlang C".
RF-003.4: Debe haber un campo numérico para "Nivel de Servicio Objetivo (%)" que sólo acepte valores entre 1 y 100. Valor por defecto: 80.
RF-003.5: Debe haber un campo numérico para "Tiempo de Atención Objetivo (segundos)" que solo acepte valores enteros positivos. Valor por defecto: 20.
RF-003.6: Debe haber un campo numérico para "Tiempo Medio de Paciencia (segundos)". Este campo solo será visible y obligatorio si el "Modelo de Cálculo" seleccionado es "Erlang A".
RF-003.7: El sistema debe tener un botón "Generar Planificación" que solo se activará una vez que se hayan cargado ambos archivos (Demanda y Horarios) y todos los campos de configuración estén completos y validados.
3.1.2. Módulo 2: Motor de Reglas y Generación de Horarios
Este módulo se activa cuando el usuario hace clic en "Generar Planificación". Su comportamiento se bifurcará dependiendo de si los horarios de los asesores son fijos o flexibles.
RF-009: Carga de Archivo de Concesiones (Opcional)
Descripción: El sistema debe proporcionar una interfaz que permita al usuario, de forma opcional, cargar un archivo adicional en formato .xlsx. Este archivo identificará a los asesores con horarios fijos (concesiones) que no deben ser modificados por el sistema.
Entrada: Un archivo .xlsx.
Proceso: El sistema leerá los IDs de los asesores de este archivo y los marcará internamente como "fijos".
Salida: Un listado interno de ID_Asesor que serán excluidos de la generación automática de descansos.
Requerimientos Específicos:
RF-009.1: La carga de este archivo es opcional. Si no se carga, el sistema asumirá que todos los horarios del archivo base (RF-002) son "flexibles".
RF-009.2: El archivo de concesiones debe contener, como mínimo, una columna con el encabezado ID_Asesor.
RF-009.3: Para los asesores listados en este archivo, el sistema debe tomar los horarios (incluyendo descansos y PVDs si ya están especificados en el archivo de horarios base) exactamente como se proporcionan, sin aplicar ninguna de las reglas de generación automática (RF-011, RF-012). El sistema sí los incluirá en los cálculos de capacidad (Módulo 3).
RF-010: Cálculo de Duración de Turno
Descripción: Como paso previo, el sistema debe calcular la duración total en horas de cada turno de trabajo importado, tanto para asesores con horario fijo como flexible.
Entrada: Hora_Inicio_Turno, Hora_Fin_Turno de cada asesor. Si un asesor tiene dos entradas en el mismo día (turno segmentado), la duración total es la suma de ambos segmentos.
Proceso: El sistema calculará la duración de cada segmento y los sumará si corresponde. El cálculo debe manejar correctamente los turnos que cruzan la medianoche.
Salida: Un valor numérico interno (ej. 8.0, 6.5) asociado a cada asesor.
RF-011: Asignación de Descansos (Breaks) para Horarios Flexibles
Descripción: Para todos los asesores no listados en el archivo de concesiones (RF-009), el sistema debe asignar automáticamente un período de descanso (Break). El cálculo de la duración y la estrategia de asignación dependerán del país seleccionado en la configuración.
Entrada: La duración del turno calculada en RF-010, la selección de país (RF-003.1), y el tipo de turno (continuo o segmentado).
Proceso: Aplicará reglas condicionales por país para determinar la duración del break. Luego, utilizará una estrategia de asignación inteligente, especialmente para turnos segmentados, para colocar el descanso de la manera más conveniente para la operación.
Salida: Un horario detallado para cada asesor "flexible" que incluye uno o dos períodos de tiempo etiquetados como "Break".
Requerimientos Específicos:
RF-011.1: La duración total del break se determinará aplicando la tabla correspondiente al país seleccionado en la configuración (RF-003.1).
A. Si el país es "España":
Si Duración < 4 horas: 0 minutos de break.
Si 4 <= Duración < 6 horas: 10 minutos de break.
Si 6 <= Duración < 8 horas: 20 minutos de break.
Si Duración >= 8 horas: 30 minutos de break.
B. Si el país es "Colombia": La duración se basará en la parte entera de la duración total del turno (ej. un turno de 7.5 horas se considera como 7 horas para este cálculo).
Si Duración >= 10 horas: 40 minutos de break.
Si Duración >= 9 horas y < 10 horas: 35 minutos de break.
Si Duración >= 8 horas y < 9 horas: 30 minutos de break.
Si Duración >= 7 horas y < 8 horas: 25 minutos de break.
Si Duración >= 6 horas y < 7 horas: 20 minutos de break.
Si Duración >= 5 horas y < 6 horas: 15 minutos de break.
Si Duración >= 4 horas y < 5 horas: 10 minutos de break.
Si Duración < 4 horas: 0 minutos de break.
RF-011.2: El algoritmo de asignación para turnos continuos debe buscar una franja para el break que cumpla, en orden de prioridad:
Debe estar ubicado lo más cerca posible de la mitad del turno.
Debe comenzar al menos 2 horas después de Hora_Inicio_Turno.
Debe finalizar al menos 1 hora y 30 minutos antes de Hora_Fin_Turno.
RF-011.3: El algoritmo de asignación para turnos segmentados debe ser inteligente y evaluar múltiples escenarios para determinar la colocación más conveniente. La "conveniencia" se define como la opción que menos impacta negativamente la métrica sobre_sub. El algoritmo debe tener la capacidad de:
Opción A: Asignar la duración total del break como un único bloque en el segmento de mayor duración del turno.
Opción B: Dividir la duración total del break en dos partes (ej. un break de 30 minutos se puede dividir en dos de 15) y asignar una parte a cada segmento del turno.
El sistema debe evaluar estas opciones y elegir la que resulte en una mejor cobertura general (un sobre_sub menos negativo o más cercano a cero) durante los intervalos afectados por el descanso.
RF-011.4: El break, ya sea en un solo bloque o dividido, no puede solaparse con un PVD.
RF-012: Asignación de PVDs para Horarios Flexibles (España)
Descripción: Si el país seleccionado es "España", el sistema debe calcular y asignar PVDs a cada asesor con horario flexible.
Entrada: Duración del turno (RF-010), la selección de país "España" (RF-003.1), y el listado de asesores flexibles.
Proceso: Calculará el número de PVDs correspondientes y los distribuirá a lo largo del turno.
Salida: El horario detallado del asesor flexible con períodos de tiempo etiquetados como "PVD".
Requerimientos Específicos:
RF-012.1: Si el país seleccionado NO es "España", este requisito debe ser omitido.
RF-012.2: Se asignará un (1) PVD por cada hora completa de trabajo (ej. 8h -> 8 PVDs; 7.5h -> 7 PVDs).
RF-012.3: Cada PVD tendrá una duración fija de 5 minutos.
RF-012.4: El algoritmo de distribución de PVDs debe cumplir las siguientes reglas:
No pueden solaparse entre sí ni con el Break asignado.
El tiempo entre PVDs debe estar, idealmente, entre 45 y 75 minutos.
La distribución debe ser lo más uniforme posible a lo largo del turno (incluyendo ambos segmentos si es un turno partido).
RF-012.5: El algoritmo debe analizar permutaciones para evitar la sobrecarga de PVDs en una misma franja horaria a nivel de equipo, seleccionando la distribución que mejor contribuya a la homogeneidad de la cobertura.
RF-013: Validación de Límites de Horas por País
Descripción: El sistema debe validar que la duración total de cada turno (tanto fijos como flexibles) cumpla con los límites del país seleccionado.
Entrada: Duración del turno (RF-010) y selección de país (RF-003.1).
Proceso: Comparará la duración del turno con los límites.
Salida: Una advertencia al usuario si se detecta un turno no conforme.
Requerimientos Específicos:
RF-013.1: Si el país es "Colombia", los turnos deben tener una duración mínima de 4 horas y máxima de 10 horas.
RF-013.2: Si el país es "España", la validación del límite máximo de horas es condicional:
A. El sistema DEBE verificar si el ID_Asesor del turno evaluado existe en la lista de asesores cargada desde el archivo de concesiones (RF-009).
B. Si el ID_Asesor SÍ está en la lista de concesiones, el límite máximo de duración del turno permitido es de 10 horas.
C. Si el ID_Asesor NO está en la lista de concesiones, se aplica el límite máximo estándar de 8 horas.
RF-013.3: Si un turno no cumple con las reglas aplicables (ya sean las estándar o las de concesión), el sistema continuará pero mostrará una advertencia al final: "Advertencia: El asesor [ID_Asesor] tiene un turno de [X] horas, fuera de los límites para [País]".
3.1.3. Módulo 3: Análisis de Capacidad
Este módulo realiza los cálculos analíticos que permiten al planificador evaluar la calidad y eficiencia de la planificación generada. Todos los cálculos se realizan para cada intervalo de tiempo definido por la "Granularidad de Intervalo" (RF-003.2).
RF-014: Cálculo de Asesores Efectivos Requeridos
Descripción: El sistema debe calcular el número teórico de asesores necesarios para manejar la demanda de llamadas en cada intervalo, según el modelo Erlang seleccionado.
Entrada: Los datos de Llamadas_Esperadas y AHT_Promedio del archivo de demanda (RF-001), y los parámetros de planificación (Modelo Erlang, SLA) de la configuración (RF-003).
Proceso: Para cada intervalo, el sistema aplicará la fórmula Erlang B, C o A según la selección del usuario.
Salida: Una serie de valores numéricos, uno por cada intervalo, representando los "Asesores Efectivos Requeridos".
RF-015: Cálculo de Asesores Dimensionados
Descripción: El sistema debe determinar el número real de asesores que están disponibles para atender llamadas en cada intervalo, basándose en los horarios generados.
Entrada: La lista completa de horarios detallados (tanto fijos como los generados por el motor de reglas), que incluyen la ubicación de los Breaks y PVDs.
Proceso: Para cada intervalo de tiempo, el sistema contará cuántos asesores están en su turno pero NO están en un Break o en un PVD.
Salida: Una serie de valores numéricos, uno por cada intervalo, representando los "Asesores Dimensionados".
RF-016: Cálculo de Capacidad de Llamada (Call Capacity)
Descripción: El sistema debe calcular el número máximo de llamadas que los asesores dimensionados pueden gestionar en cada intervalo.
Entrada: El número de Asesores Dimensionados (calculado en RF-015) para cada intervalo y el AHT promedio para ese mismo intervalo.
Proceso: Utilizará la fórmula: Call Capacity = Asesores Dimensionados * (Duración del Intervalo en segundos / AHT_Promedio).
Salida: Una serie de valores numéricos, uno por cada intervalo, representando la Call Capacity.
RF-017: Cálculo de Métricas de Cobertura y Rendimiento
Descripción: El sistema debe calcular un conjunto de métricas clave que permitan al usuario final evaluar el rendimiento de la planificación de un solo vistazo.
Entrada: Los resultados de los cálculos anteriores (RF-014, RF-015, RF-016) y los datos de demanda.
Proceso: Aplicará fórmulas aritméticas simples para cada intervalo.
Salida: Múltiples series de datos para cada intervalo, incluyendo sobre_sub, Llamadas atendidas alcanzables y Porcentaje de atención.
Requerimientos Específicos:
RF-017.1: El sobre_sub se calculará como: Asesores Dimensionados - Asesores Efectivos Requeridos.
RF-017.2: Las Llamadas atendidas alcanzables se calcularán con la siguiente lógica: Si Call Capacity < Llamadas esperadas, entonces es igual a Call Capacity. Si no, es igual a Llamadas esperadas.
RF-017.3: El Porcentaje de atención se calculará como: (Llamadas atendidas alcanzables / Llamadas esperadas) * 100.
3.1.4. Módulo 4: Visualización de Resultados
RF-018: Presentación de Resultados en Dashboard
Descripción: El sistema debe presentar todos los datos calculados en una interfaz de usuario clara y consolidada (dashboard) después de que la generación de la planificación haya finalizado.
Entrada: Todas las series de datos generadas en el Módulo 3.
Proceso: El sistema renderizará los componentes gráficos y tabulares.
Salida: Una vista interactiva para el usuario.
Requerimientos Específicos:
RF-018.1: El dashboard debe incluir un gráfico de líneas o barras que muestre, como mínimo, la comparación a lo largo del día entre Asesores Dimensionados y Asesores Efectivos Requeridos.
RF-018.2: El dashboard debe incluir una tabla detallada. Cada fila representará un intervalo de tiempo y cada columna representará una métrica (ej. Intervalo, Llamadas_Esperadas, Asesores_Requeridos, Asesores_Dimensionados, sobre_sub, Call_Capacity, Porcentaje_Atencion).
RF-018.3: En la tabla, los valores de la columna sobre_sub deben tener un formato condicional: valores negativos (< 0) en color rojo, valores positivos (> 0) en color azul o verde.
3.1.5. Módulo 5: Persistencia y Exportación
RF-019: Guardado de la Sesión de Planificación
Descripción: El sistema debe ofrecer al usuario un botón para "Guardar Planificación".
Entrada: La acción del usuario de hacer clic en el botón.
Proceso: El sistema tomará todos los datos de la sesión actual (horarios generados, métricas calculadas, parámetros de configuración) y los guardará en la base de datos NoSQL.
Salida: Un registro persistente en la base de datos. Un mensaje de confirmación para el usuario: "Planificación guardada correctamente".
RF-020: Exportación Personalizada de Horarios a Excel
Descripción: El sistema debe ofrecer al usuario una opción para exportar los horarios detallados a un archivo .xlsx, permitiéndole aplicar filtros personalizados antes de generar el documento.
Entrada: La acción del usuario de iniciar la exportación y los criterios de filtrado seleccionados.
Proceso: El sistema presentará una interfaz de filtrado, procesará los datos según los criterios seleccionados y generará el archivo .xlsx correspondiente.
Salida: La descarga de un archivo .xlsx filtrado en el navegador del usuario.
Requerimientos Específicos:
RF-020.1: Al hacer clic en "Exportar", el sistema debe mostrar una ventana modal o una sección de "Opciones de Exportación".
RF-020.2: Esta interfaz debe incluir un filtro de fechas, permitiendo al usuario seleccionar una fecha de inicio y una fecha de fin. Por defecto, se seleccionará el rango de fechas completo de la planificación actual.
RF-020.3: Esta interfaz debe incluir un filtro de asesores. Este control debe permitir la selección de uno o múltiples asesores de una lista. Debe incluir una opción para "Seleccionar Todos" (comportamiento por defecto) y una función de búsqueda para encontrar asesores específicos fácilmente.
RF-020.4: Un botón de "Generar Exportación" dentro de la interfaz de opciones aplicará los filtros y comenzará la descarga del archivo.
RF-020.5: El archivo Excel exportado debe contener una hoja de cálculo donde cada fila represente a un asesor y las columnas representen los intervalos de tiempo del día, mostrando la actividad correspondiente, únicamente para los asesores y las fechas que cumplan con los criterios de filtrado seleccionados. 
3.2. Requisitos de la Interfaz Externa
Esta sección detalla las interfaces del SIPO con otros componentes, que en el caso del MVP se limitan a las interacciones con el usuario y los formatos de archivo.
R-INT-01: Interfaz de Usuario (UI)
Descripción: El sistema debe proporcionar una interfaz de usuario gráfica (GUI) basada en la web, accesible a través de un navegador moderno (Chrome, Firefox, Edge en sus versiones más recientes).
Requerimientos Específicos:
R-INT-01.1: La interfaz debe ser responsiva y funcional en resoluciones de pantalla de escritorio estándar (desde 1366x768 hasta 1920x1080).
R-INT-01.2: El diseño debe ser limpio y profesional, siguiendo una paleta de colores y un estilo consistentes en toda la aplicación.
R-INT-01.3: La navegación entre las diferentes secciones (carga de datos, configuración, visualización de resultados) debe ser clara e intuitiva.
R-INT-01.4: El sistema debe proporcionar retroalimentación visual para las acciones del usuario, como indicadores de carga (spinners) durante el procesamiento de archivos y mensajes de confirmación o error.
R-INT-02: Interfaz de Archivos
Descripción: El sistema utilizará archivos de Microsoft Excel (.xlsx) como principal medio para la importación y exportación de datos.
Requerimientos Específicos:
R-INT-02.1: Importación: El sistema debe ser capaz de analizar el contenido de archivos .xlsx generados por versiones estándar de Microsoft Excel. No se garantiza la compatibilidad con formatos de hoja de cálculo alternativos (ej. .ods, Numbers) aunque puedan exportar a .xlsx.
R-INT-02.2: Exportación: El archivo .xlsx generado por el SIPO (RF-020) debe ser compatible y poder abrirse correctamente en versiones de Microsoft Excel 2007 y posteriores, así como en Google Sheets. La librería de generación de archivos seleccionada para el desarrollo debe garantizar esta compatibilidad..
3.3. Requisitos No Funcionales (RNF)
Estos requisitos definen los atributos de calidad del sistema. Son tan importantes como los requisitos funcionales para el éxito del proyecto.
RNF-01: Rendimiento
Descripción: El sistema debe ser capaz de procesar la carga de trabajo esperada en un tiempo razonable para no interrumpir el flujo de trabajo del planificador.
Requerimientos Específicos:
RNF-01.1: Para una carga de trabajo estándar (2 archivos Excel, uno con 1000 filas de demanda y otro con 200 asesores para una jornada de 24 horas), el tiempo total desde que el usuario presiona "Generar Planificación" hasta que se muestra el dashboard de resultados no debe exceder los 90 segundos.
RNF-01.2: La respuesta de la interfaz de usuario a las acciones del usuario (clics en botones, selecciones en menús desplegables) debe ser inferior a 500 milisegundos.
RNF-02: Fiabilidad
Descripción: El sistema debe ser robusto y estar disponible cuando se necesite.
Requerimientos Específicos:
RNF-02.1: Los cálculos matemáticos (Erlang, métricas de WFM) deben tener una precisión del 100% de acuerdo a las fórmulas especificadas.
RNF-02.2: El sistema debe gestionar adecuadamente los errores. Una entrada de datos incorrecta (ej. un formato de fecha inválido en el Excel) no debe causar que la aplicación se bloquee. Debe capturar el error y presentar un mensaje claro al usuario.
RNF-03: Usabilidad
Descripción: El sistema debe ser fácil de aprender y utilizar para el perfil de usuario definido (Planificador de WFM).
Requerimientos Específicos:
RNF-03.1: Un nuevo planificador con experiencia en conceptos de WFM debe ser capaz de realizar una planificación completa (cargar archivos, configurar, generar y analizar) con menos de 1 hora de capacitación.
RNF-03.2: La terminología utilizada en la interfaz (etiquetas, botones, mensajes) debe ser consistente con la jerga estándar de la industria de WFM y la definida en la sección 1.3 de este documento.
RNF-04: Mantenibilidad
Descripción: La arquitectura y el código del sistema deben facilitar futuras modificaciones, correcciones y evoluciones. Este es un requisito clave dada la naturaleza del equipo de desarrollo.
Requerimientos Específicos:
RNF-04.1: El código fuente del backend (Spring Boot) y del frontend (Angular) debe estar escrito en inglés.
RNF-04.2: Se deben añadir comentarios en el código para explicar las secciones de lógica de negocio más complejas, especialmente en el motor de reglas y los algoritmos de asignación.
RNF-04.3: Se debe entregar un documento simple de "Guía de Despliegue" que explique los pasos para ejecutar la aplicación a partir de su contenedor Docker.
RNF-05: Seguridad
Descripción: Aunque es una aplicación interna, debe cumplir con unos mínimos de seguridad.
Requerimientos Específicos:
RNF-05.1: El sistema no debe tener credenciales de base de datos o claves de API escritas directamente en el código fuente (hard-coded). Deben gestionarse a través de variables de entorno del contenedor Docker.
RNF-05.2: La validación de los archivos cargados debe realizarse en el lado del servidor para prevenir la inyección de código malicioso.
