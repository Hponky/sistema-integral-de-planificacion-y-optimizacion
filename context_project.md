# Documentación Técnica: EM-Sistema Integral Planificación Optimización (SIPO)

## Frontend Angular (SSR Standalone Components, Signals, RxJS)

### Core Services
- **ApiService:** Base HTTP client con endpoints base_url, interceptors auth/error.
- **AuthService/Guard/Interceptor:** JWT handling, guards routes, refresh tokens.

### Features/Planning
- **FileUploadComponent:** Upload Excel staffing/ausencias → backend process.

## Frontend - features/planning/scheduling/

### Propósito
Fachada UI mock generación horarios (inspirado pl/ legacy scheduling_service.py). Datos mock realistas, sin backend.

### Componentes Standalone
- **SchedulingComponent**: Orquesta layout (controls, agent-list, shift-table, calendar-view).
- **AgentListComponent**: Lista agentes mock (avatar emoji, nombre, perfil).
- **ShiftTableComponent**: Tabla moderna con glassmorfismo, header sticky, búsqueda/filtrado en tiempo real, ordenamiento, paginación inteligente, exportación CSV/Excel. **ShiftTableDataService** centraliza lógica (SOLID/DRY). Features: hover effects, scrollbars personalizadas, responsive, OnPush performance, accesibilidad WCAG.
- **CalendarViewComponent**: Chart.js doughnut distribución turnos por tipo.
- **ControlsComponent**: Form (fecha inicio-fin, #agentes 10-50), botón "Generar" → facade.generateMock().

### SchedulingFacadeService (Signals Reactivo)
- **Estado**: agents$ (Agent[]), schedules$ (Schedule[]), loading$, filters$.
- **Métodos**: generateMock() → 30 agentes × 11 días, turnos realistas (mañana/tarde/noche), breaks random.
- **Interfaces**:
  - Agent: {id, name, profile, avatar}
  - Schedule: {agentId, date, start, end, type, typeColor, breaks: Break[], compliance: number}
  - Break: {start, duration}

### UX/UI Moderno (ShiftTable)
- **Diseño**: Glassmorphism (_color-palette.css), badges coloreados, chips breaks visuales, progress bars.
- **Features**: Copy CSV funcional, header sticky, hover shadows, responsive mobile, empty state.
- **Data**: 30 agentes mock, turnos 7-14h, breaks 30-60min.

### Routing (Lazy + Auth)
- app.routes.ts → {path: 'planning', loadChildren: PlanningRoutingModule}
- planning-routing.module.ts → {path: 'scheduling', loadComponent: SchedulingComponent, canActivate: [AuthGuard]}

### Acceso Navbar
`<a routerLink="/planning/scheduling" *ngIf="authenticationStateService.isAuthenticated$ | async" class="nav-link">Generación Horarios</a>`

### Dependencias
AG-Grid (tablas), Chart.js (gráficos), Angular Signals (reactividad), CSS custom glassmorphism.

## Backend (sipo/pl)
- Scheduling APIs: get_schedule (VM tabla/chart), run_schedule (solver OR-Tools → DB Schedule), fill_gaps.

**Estado:** Fachada UI lista para impl. Backend APIs asumidos disponibles.

## Frontend - features/calculator/

### Propósito
Módulo de cálculo de dimensionamiento de personal con KPIs operativos y tablas de resultados optimizadas.

### Componentes Standalone Mejorados
- **CalculatorComponent**: Orquesta formulario de cálculo, KPIs modernos y tablas de resultados.
- **ResultsTableComponent**: Componente reutilizable con sorting, filtrado, paginación y exportación CSV/Excel.
- **KpiCardComponent**: Tarjetas KPI animadas con tendencias, iconos coloreados y microinteracciones.

### Arquitectura y Patrones Aplicados
- **SOLID Principles**:
  - Single Responsibility: Cada componente tiene una única responsabilidad
  - Open/Closed: Componentes extensibles sin modificación
  - Dependency Inversion: Inyección de dependencias con servicios
- **DRY Pattern**: TableDataService centraliza la lógica de manejo de datos
- **Component Composition**: CalculatorComponent compone ResultsTableComponent y KpiCardComponent
- **OnPush Change Detection**: Optimización de rendimiento con detección de cambios por push

### TableDataService (Centralización de Lógica)
- **Responsabilidad**: Manejo centralizado de sorting, filtrado y paginación
- **Métodos**: sortData(), filterData(), paginateData(), exportToCSV(), exportToExcel()
- **Beneficios**: Reutilización, mantenimiento centralizado, testing simplificado

### UX/UI Moderno (Tendencias 2024-2025)
- **Glassmorphism**: Efectos de blur y transparencia en sección de KPIs
- **Microinteracciones**: Hover effects, animaciones suaves, transiciones fluidas
- **Design System**: Paleta de colores consistente con variables CSS
- **Responsive Design**: Adaptación completa a móviles y tablets
- **Accessibility**: ARIA labels, navegación por teclado, contraste WCAG 2.1 AA

### KPIs Mejorados
- **Visualización**: Tarjetas con gradientes, sombras y animaciones
- **Iconos**: Colores dinámicos según estado (success/warning/error/info)
- **Tendencias**: Indicadores de dirección con valores y colores contextuales
- **Insights**: Recomendaciones inteligentes basadas en valores de KPIs
- **Animaciones**: Efectos de entrada, hover y actualización de valores

### Tablas de Resultados Optimizadas
- **Features**: Sorting multi-columna, filtrado en tiempo real, paginación eficiente
- **Exportación**: CSV y Excel con formato profesional
- **Performance**: Headers sticky, lazy loading, virtual scrolling para grandes datasets
- **UX**: Scrollbar personalizada, hover effects, contadores contextuales
- **Responsive**: Adaptación horizontal y vertical con breakpoints optimizados

### Interfaces TypeScript
```typescript
interface KpiData {
  absentismo_pct: number;
  auxiliares_pct: number;
  desconexiones_pct: number;
}

interface TableData {
  columns: string[];
  data: (string | number)[][];
}

interface SortConfig {
  column: string;
  direction: 'asc' | 'desc';
}

interface CalculationResult {
  dimensionados: TableData;
  presentes: TableData;
  logados: TableData;
  efectivos: TableData;
  kpis: KpiData;
}
```

### Mejoras Técnicas Implementadas
- **Error Handling**: Validación robusta de formularios y manejo de errores de autenticación
- **Performance**: OnPush change detection, lazy loading, optimización de bundles
- **Security**: Validación de inputs, sanitización de datos, protección CSRF
- **Testing**: Componentes testables con mocks y spies
- **Code Quality**: TypeScript strict, ESLint configurado, formato consistente

### Integración con Backend
- **Endpoints**: /api/calculator/calculate (POST), /api/calculator/segments (GET)
- **Authentication**: JWT tokens con refresh automático
- **Error Handling**: Manejo centralizado de errores de sesión expirada
- **Data Flow**: FormData → Backend → CalculationResult → UI Components

### Estado Actual
- **Funcionalidad**: Completamente funcional con todos los KPIs y tablas operativas
- **Performance**: Optimizada para datasets grandes con paginación y sorting eficiente
- **UX**: Moderna con tendencias 2024-2025, accesibilidad WCAG 2.1 AA
- **Calidad**: Código limpio, documentado y mantenible siguiendo mejores prácticas

**Estado:** Módulo calculator completamente implementado y optimizado con UX/UI moderna.