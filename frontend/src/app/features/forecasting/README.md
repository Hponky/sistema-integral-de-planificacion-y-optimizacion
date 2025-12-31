# Forecasting Module - Modular Structure

## 📁 Estructura de Archivos

```
forecasting/
├── forecasting.ts                    # Componente principal (orquestador)
├── forecasting.html                  # Template principal (tabs)
├── forecasting.css                   # Estilos compartidos
├── forecasting.service.ts            # Servicio compartido para API calls
└── components/
    ├── intraday/
    │   ├── intraday.component.ts     # Lógica de distribución intradía
    │   └── intraday.component.html   # UI de distribución intradía
    ├── date-analysis/
    │   ├── date-analysis.component.ts     # Lógica de análisis de fechas
    │   └── date-analysis.component.html   # UI de análisis de fechas
    ├── monthly-forecast/
    │   ├── monthly-forecast.component.ts     # Lógica de forecast mensual
    │   └── monthly-forecast.component.html   # UI de forecast mensual
    └── distribution/
        ├── distribution.component.ts     # Lógica de distribución de volumen
        └── distribution.component.html   # UI de distribución de volumen
```

## 🎯 Componentes

### 1. **ForecastingComponent** (Principal)
- **Responsabilidad**: Orquestación de tabs y navegación
- **Archivo**: `forecasting.ts` / `forecasting.html`
- **Funcionalidad**: 
  - Gestión de tabs activos
  - Renderizado condicional de componentes hijos
  - Sin lógica de negocio

### 2. **IntradayComponent**
- **Responsabilidad**: Análisis de patrones semanales y distribución intradía
- **Archivos**: `components/intraday/intraday.component.{ts,html}`
- **Funcionalidades**:
  - Carga y análisis de archivos históricos
  - Gestión de segmentos y servicios
  - Visualización de curvas con Chart.js
  - Ajuste de pesos por semana
  - Exportación a Excel
  - Guardado de curvas en base de datos
  - Análisis de festivos
  - Análisis de fechas específicas

### 3. **DateAnalysisComponent**
- **Responsabilidad**: Búsqueda de comportamiento histórico por fecha
- **Archivos**: `components/date-analysis/date-analysis.component.{ts,html}`
- **Funcionalidades**:
  - Búsqueda de patrones históricos para una fecha específica
  - Comparación con años anteriores
  - Selección de curvas históricas

### 4. **MonthlyForecastComponent**
- **Responsabilidad**: Proyecciones mensuales (IntraYear)
- **Archivos**: `components/monthly-forecast/monthly-forecast.component.{ts,html}`
- **Funcionalidades**:
  - Carga de archivos históricos
  - Configuración de peso de recencia
  - Generación de proyecciones mensuales
  - Visualización de resultados por mes

### 5. **DistributionComponent**
- **Responsabilidad**: Distribución de volumen (intra-mes e intradía)
- **Archivos**: `components/distribution/distribution.component.{ts,html}`
- **Funcionalidades**:
  - Distribución intra-mes (mensual → diario)
  - Distribución intradía (diario → intervalos)
  - Generación de archivos Excel

## 🔄 Flujo de Datos

```
ForecastingService (Singleton)
        ↓
    ┌───┴───┬───────┬──────────┬──────────┐
    │       │       │          │          │
Intraday  Date   Monthly  Distribution
Component Analysis Forecast  Component
          Component Component
```

## 🛠️ Servicios Compartidos

### **ForecastingService**
- Centraliza todas las llamadas HTTP a la API
- Compartido por todos los componentes hijos
- Métodos principales:
  - `analyzeIntraday()`
  - `analyzeHolidays()`
  - `analyzeDate()`
  - `monthlyForecast()`
  - `distributeIntramonth()`
  - `distributeIntraday()`
  - `saveCurves()`
  - `getCurvesBySegment()`
  - `exportDistribution()`

### **ToastService**
- Notificaciones de éxito/error
- Usado por componentes para feedback al usuario

## 📊 Estilos

Todos los componentes comparten el archivo `forecasting.css` que contiene:
- Estilos de cards
- Estilos de formularios
- Estilos de tablas
- Estilos de gráficos
- Estilos de loaders
- Estilos de alertas

## 🚀 Ventajas de la Modularización

1. **Separación de Responsabilidades**: Cada componente tiene una única responsabilidad clara
2. **Mantenibilidad**: Más fácil encontrar y modificar código específico
3. **Reusabilidad**: Componentes pueden ser reutilizados en otros contextos
4. **Testabilidad**: Cada componente puede ser testeado de forma aislada
5. **Escalabilidad**: Fácil agregar nuevas funcionalidades sin afectar componentes existentes
6. **Legibilidad**: Archivos más pequeños y enfocados
7. **Lazy Loading**: Posibilidad de cargar componentes bajo demanda en el futuro

## 🔧 Cómo Extender

### Agregar un nuevo tab:

1. Crear nuevo componente en `components/`:
```bash
mkdir components/nuevo-tab
touch components/nuevo-tab/nuevo-tab.component.ts
touch components/nuevo-tab/nuevo-tab.component.html
```

2. Implementar el componente con lógica específica

3. Importar en `forecasting.ts`:
```typescript
import { NuevoTabComponent } from './components/nuevo-tab/nuevo-tab.component';

imports: [
  // ... otros imports
  NuevoTabComponent
]
```

4. Agregar tab en `forecasting.html`:
```html
<button class="tab-btn" [class.active]="activeTab === 'nuevo'" (click)="setActiveTab('nuevo')">
    <span class="icon">🆕</span> Nuevo Tab
</button>

<!-- ... -->

<div *ngIf="activeTab === 'nuevo'" class="tab-content">
    <app-nuevo-tab></app-nuevo-tab>
</div>
```

## 📝 Notas de Migración

- **Antes**: 1 archivo de 1055 líneas (forecasting.ts) + 661 líneas (forecasting.html)
- **Después**: 
  - Componente principal: ~30 líneas
  - 4 componentes especializados: ~200-800 líneas cada uno
  - Total: Mejor organización y mantenibilidad

## ⚠️ Consideraciones

- Todos los componentes son **standalone** (Angular 14+)
- Comparten el mismo servicio `ForecastingService` (singleton)
- Los estilos CSS son compartidos para mantener consistencia visual
- Chart.js se registra en cada componente que lo necesita
