/**
 * Interfaces para el módulo de la calculadora.
 */

export interface Segment {
  id: number;
  name: string;
  campaignName: string; // Nombre de la campaña para mostrar en el selector
}

export interface KpiData {
  absentismo_pct: number;
  auxiliares_pct: number;
  desconexiones_pct: number;
}

export interface TableData {
  columns: string[];
  data: (string | number)[][];
}

export interface SortConfig {
  column: string;
  direction: 'asc' | 'desc';
}

export interface CalculationResult {
  dimensionados: TableData;
  presentes: TableData;
  logados: TableData;
  efectivos: TableData;
  kpis: KpiData;
}
