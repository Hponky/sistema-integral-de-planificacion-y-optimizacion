# Plan de Rediseño UX/UI: Módulo de Calculadora de Agentes

**Autor:** Kilo Code (Experto Senior UX/UI)
**Fecha:** 2025-10-18
**Versión:** 1.0

## 1. Resumen Ejecutivo

Este documento detalla el plan de acción para el rediseño completo del módulo de la calculadora de dimensionamiento de agentes. El objetivo es transformar la herramienta actual en una experiencia de usuario moderna, intuitiva, accesible y estéticamente agradable, alineada con los estándares de diseño de 2025. La propuesta se basa en una auditoría exhaustiva de la interfaz existente y una investigación de las mejores prácticas dictadas por Material Design 3.0 y los Human Interface Guidelines de Apple.

## 2. Auditoría UX/UI del Sistema Actual

| Área de Análisis | Problema Detectado | Impacto en el Usuario | Severidad |
| :--- | :--- | :--- | :--- |
| **Diseño Visual** | Paleta de colores monotona, falta de jerarquía visual, tipografía plana. | Dificultad para escanear información, interfaz poco atractiva y confusa. | Alta |
| **Layout y Espaciado** | Inconsistencia en márgenes y `padding`, elementos de formulario muy juntos. | Sobrecarga cognitiva, dificultad para agrupar información relacionada. | Media |
| **Interacción** | Ausencia de feedback visual en botones y campos (estados `hover`, `active`, `disabled`). | Incertidumbre sobre la interactividad de los elementos, experiencia de usuario pobre. | Alta |
| **Componentes UI** | Uso de componentes nativos (dropdowns) que rompen la consistencia del diseño. | Experiencia visual inconsistente y poco profesional. | Media |
| **Carga de Archivos** | Funcionalidad básica sin "drag-and-drop", feedback de carga limitado. | Proceso de carga de archivos menos eficiente y moderno. | Baja |
| **Visualización de Datos** | Tablas de datos densas, difíciles de leer y sin ayudas visuales. | Dificultad para analizar y extraer insights de los resultados. | Alta |
| **Accesibilidad** | Ausencia de etiquetas `<label>` en formularios, posible bajo contraste, falta de foco visible. | Exclusión de usuarios con discapacidades (lectores de pantalla), usabilidad reducida. | Crítica |
| **Navegación** | Navbar y menú lateral desconectados, falta de agrupación lógica. | Flujo de navegación ineficiente y confuso. | Media |

## 3. Principios y Guías de Diseño a Adoptar

El rediseño se fundamentará en los siguientes principios y sistemas de diseño:

*   **Material Design 3.0 (Google):** Se adoptará como base para el sistema de componentes, la paleta de colores dinámica, la tipografía y los principios de elevación y movimiento. Aporta un lenguaje visual coherente y moderno.
*   **Human Interface Guidelines (Apple):** Se tomarán sus principios de claridad, deferencia y profundidad para asegurar una experiencia intuitiva, simple y centrada en el contenido.
*   **WCAG 2.2 (Nivel AA):** Todas las decisiones de diseño y desarrollo deberán cumplir con este estándar para garantizar la accesibilidad universal.

## 4. Tareas de Rediseño Priorizadas

### P1: Sistema de Diseño y Paleta Cromática (Prioridad Alta)

*   **Tarea 1.1:** Implementar una paleta de colores semántica basada en los tonos morados definidos:
    *   **Primario:** `#7C3AED` (para acciones principales, botones CTA, encabezados importantes).
    *   **Secundario:** `#A78BFA` (para elementos de soporte, fondos de sección, estados activos).
    *   **Acentos/Terciario:** `#DDD6FE` (para bordes, divisores, fondos sutiles).
    *   **Superficies:** Colores neutros (blancos, grises claros) para los fondos principales y contenedores de datos.
    *   **Colores de Estado:** Definir colores específicos para éxito (verde), error (rojo) y advertencia (amarillo).
*   **Tarea 1.2:** Establecer una escala tipográfica clara utilizando una fuente moderna (ej. Roboto, Inter). Definir tamaños y pesos para títulos (h1, h2, h3), cuerpo de texto, etiquetas y captions.
*   **Tarea 1.3:** Definir un sistema de espaciado y grilla (grid system) basado en una unidad base (ej. 8px) para garantizar consistencia en todos los márgenes y paddings.

### P2: Rediseño de Componentes y Formularios (Prioridad Alta)

*   **Tarea 2.1:** Rediseñar todos los campos de formulario (`input`, `select`, `datepicker`) como componentes de Angular Material, asegurando que cada campo tenga una etiqueta `<label>` persistente y visible.
*   **Tarea 2.2:** Reemplazar el componente de carga de archivos por un componente de "File Upload" de Material que incluya una zona de "drag-and-drop", validación de tipo de archivo y una barra de progreso visual.
*   **Tarea 2.3:** Rediseñar los botones con estilos claros para acciones primarias, secundarias y de texto. Implementar estados `hover`, `focus`, `active` y `disabled` para todos los elementos interactivos.
*   **Tarea 2.4:** Introducir un componente "Stepper" o una guía visual para indicar los pasos del proceso de cálculo (1. Parámetros, 2. Carga de datos, 3. Resultados).

### P3: Visualización de Datos y Resultados (Prioridad Alta)

*   **Tarea 3.1:** Rediseñar las tablas de resultados utilizando el componente `mat-table` de Angular Material.
    *   Implementar filas con colores alternos (`striped rows`) para mejorar la legibilidad.
    *   Asegurar que las cabeceras de las tablas sean fijas (`sticky`) al hacer scroll vertical.
    *   Añadir tooltips informativos en las cabeceras para explicar cada métrica.
*   **Tarea 3.2:** Reemplazar los iconos genéricos de resultados por iconos de Material Symbols más descriptivos y visualmente integrados.
*   **Tarea 3.3:** Añadir una opción para exportar los datos de las tablas a formatos como CSV y XLSX.

### P4: Accesibilidad y Diseño Responsive (Prioridad Media)

*   **Tarea 4.1:** Realizar una auditoría de accesibilidad completa utilizando herramientas como Lighthouse y Axe. Asegurar que todo el contenido cumpla con el nivel AA de WCAG 2.2 (contraste de color, etiquetas ARIA, navegación por teclado).
*   **Tarea 4.2:** Implementar un diseño "mobile-first". Definir breakpoints específicos para adaptar la interfaz a tablets y desktops, asegurando que la experiencia sea óptima en cualquier dispositivo.
    *   **Móvil (< 600px):** Layout de una sola columna, formularios y tablas adaptadas.
    *   **Tablet (600px - 960px):** Layout de dos columnas si el espacio lo permite.
    *   **Desktop (> 960px):** Layout completo de dos o tres columnas.

### P5: Microinteracciones y Feedback (Prioridad Media)

*   **Tarea 5.1:** Añadir animaciones sutiles a la carga de elementos y transiciones de estado para proporcionar feedback visual sin ser intrusivo.
*   **Tarea 5.2:** Implementar "toasts" o "snackbars" para notificaciones importantes (ej. "Cálculo completado con éxito", "Error en el formato del archivo").
*   **Tarea 5.3:** Añadir "skeleton loaders" mientras se cargan los datos de las tablas para mejorar la percepción de rendimiento.

## 5. Propuestas de Innovación y Funcionalidades Adicionales

*   **Función 5.1: Comparador de Escenarios:** Permitir al usuario guardar un cálculo como un "escenario" y luego compararlo lado a lado con otro cálculo para analizar variaciones.
*   **Función 5.2: Visualizaciones Gráficas:** Añadir gráficos interactivos (ej. gráficos de líneas para mostrar la demanda de agentes a lo largo del día) utilizando una librería como `ngx-charts` para complementar los datos tabulares.
*   **Función 5.3: Tema Oscuro (Dark Mode):** Implementar un selector de tema para que los usuarios puedan cambiar entre un tema claro y uno oscuro, mejorando la comodidad visual en diferentes entornos de iluminación.

## 6. Rediseño de la Barra de Navegación (Navbar)

*   **Tarea 6.1:** Unificar la navegación principal en una única barra superior.
*   **Tarea 6.2:** Reemplazar el texto "Bienvenido, admin" por un menú de avatar que, al hacer clic, muestre opciones como "Perfil" y "Cerrar Sesión".
*   **Tarea 6.3:** Integrar un logo de la aplicación y reorganizar los elementos para un look más limpio y profesional.

Este plan servirá como la guía central para el proyecto de rediseño. Cada sección define tareas claras que pueden ser asignadas, desarrolladas y validadas de manera incremental.