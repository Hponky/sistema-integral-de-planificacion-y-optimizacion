/**
 * Interfaces para el módulo de la calculadora.
 */

export interface Segment {
  id: number;
  name: string;
  campaign_id?: number;
  campaign_name?: string; // Nombre de la campaña desde el backend
  campaignName?: string; // Alias para compatibilidad
}

export interface KpiData {
  absentismo_pct: number;
  auxiliares_pct: number;
  desconexiones_pct: number;
  total_volumen?: number;
  aht_promedio?: number;
  total_horas_planificadas?: number;
  fte_promedio?: number;
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
  warning?: string;
}

export interface CalculationHistoryItem {
  id: number;
  created_at: string;
  segment_name: string;
  campaign_name: string;
  start_date: string;
  end_date: string;
  sla_objetivo: number;
  sla_tiempo: number;
  nda?: number; // Nivel de Atención objetivo
}
