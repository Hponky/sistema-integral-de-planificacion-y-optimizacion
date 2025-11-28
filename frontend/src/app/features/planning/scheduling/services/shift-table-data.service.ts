import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, combineLatest } from 'rxjs';
import { map, take } from 'rxjs/operators';
import type { Schedule, Agent, Shift, ShiftTableRow } from '../interfaces';

export interface ShiftTableConfig {
  pageSize: number;
  currentPage: number;
  searchTerm: string;
  sortBy: string;
  sortDirection: 'asc' | 'desc';
}

export interface ShiftTableState {
  rows: ShiftTableRow[];
  filteredRows: ShiftTableRow[];
  paginatedRows: ShiftTableRow[];
  totalRecords: number;
  totalPages: number;
  config: ShiftTableConfig;
}

@Injectable({
  providedIn: 'root'
})
export class ShiftTableDataService {
  private readonly defaultConfig: ShiftTableConfig = {
    pageSize: 20,
    currentPage: 1,
    searchTerm: '',
    sortBy: 'nombre',
    sortDirection: 'asc'
  };

  private configSubject = new BehaviorSubject<ShiftTableConfig>(this.defaultConfig);
  private originalRowsSubject = new BehaviorSubject<ShiftTableRow[]>([]);

  readonly config$ = this.configSubject.asObservable();
  readonly state$: Observable<ShiftTableState> = combineLatest([
    this.originalRowsSubject,
    this.configSubject
  ]).pipe(
    map(([rows, config]) => this.computeState(rows, config))
  );

  /**
   * Establece los datos originales de la tabla
   * @param schedule Datos del horario
   */
  setOriginalData(schedule: Schedule): void {
    const rows = this.buildRows(schedule);
    this.originalRowsSubject.next(rows);
  }

  /**
   * Actualiza la configuración de la tabla
   * @param updates Parcial de la configuración a actualizar
   */
  updateConfig(updates: Partial<ShiftTableConfig>): void {
    const currentConfig = this.configSubject.value;
    this.configSubject.next({ ...currentConfig, ...updates });
  }

  /**
   * Reinicia la configuración a valores por defecto
   */
  resetConfig(): void {
    this.configSubject.next({ ...this.defaultConfig });
  }

  /**
   * Construye las filas de la tabla a partir del schedule
   * @param schedule Datos del horario
   * @returns Filas construidas
   */
  private buildRows(schedule: Schedule): ShiftTableRow[] {
    if (!schedule?.agents || !schedule?.days) {
      return [];
    }

    return schedule.agents.slice(0, 50).map(agent => {
      const shifts = schedule.days.slice(0, 31).map(day => day.agentShifts[agent.id]);
      
      return {
        id: agent.id,
        avatar: agent.avatar,
        nombre: agent.nombre,
        perfil: agent.perfil,
        cumplimiento: this.calculateCompliance(agent, schedule.days),
        shifts: shifts as (Shift | null)[]
      };
    });
  }

  /**
   * Calcula el cumplimiento de un agente
   * @param agent Datos del agente
   * @param days Días del schedule
   * @returns Porcentaje de cumplimiento
   */
  private calculateCompliance(agent: Agent, days: any[]): number {
    // Lógica de cumplimiento basada en turnos asignados
    const assignedDays = days.filter(day => 
      day.agentShifts[agent.id] && day.agentShifts[agent.id].tipo !== 'LIBRE'
    ).length;
    
    const totalDays = days.length;
    const baseCompliance = Math.min(95, Math.floor((assignedDays / totalDays) * 100));
    
    // Añadir variación aleatoria para simular datos reales
    return baseCompliance + Math.floor(Math.random() * 10) - 5;
  }

  /**
   * Computa el estado completo de la tabla
   * @param rows Filas originales
   * @param config Configuración actual
   * @returns Estado completo de la tabla
   */
  private computeState(rows: ShiftTableRow[], config: ShiftTableConfig): ShiftTableState {
    // Aplicar filtrado
    const filteredRows = this.filterRows(rows, config.searchTerm);
    
    // Aplicar ordenamiento
    const sortedRows = this.sortRows(filteredRows, config.sortBy, config.sortDirection);
    
    // Aplicar paginación
    const paginatedRows = this.paginateRows(sortedRows, config.currentPage, config.pageSize);
    
    return {
      rows,
      filteredRows: sortedRows,
      paginatedRows,
      totalRecords: filteredRows.length,
      totalPages: Math.ceil(filteredRows.length / config.pageSize),
      config
    };
  }

  /**
   * Filtra las filas según término de búsqueda
   * @param rows Filas a filtrar
   * @param searchTerm Término de búsqueda
   * @returns Filas filtradas
   */
  private filterRows(rows: ShiftTableRow[], searchTerm: string): ShiftTableRow[] {
    if (!searchTerm.trim()) {
      return rows;
    }

    const term = searchTerm.toLowerCase();
    return rows.filter(row => 
      row.nombre.toLowerCase().includes(term) ||
      row.perfil.toLowerCase().includes(term) ||
      row.shifts.some((shift: Shift | null) => 
        shift && shift.tipo.toLowerCase().includes(term)
      )
    );
  }

  /**
   * Ordena las filas según campo y dirección
   * @param rows Filas a ordenar
   * @param sortBy Campo de ordenamiento
   * @param sortDirection Dirección de ordenamiento
   * @returns Filas ordenadas
   */
  private sortRows(rows: ShiftTableRow[], sortBy: string, sortDirection: 'asc' | 'desc'): ShiftTableRow[] {
    return [...rows].sort((a, b) => {
      let aVal: any = a[sortBy as keyof ShiftTableRow];
      let bVal: any = b[sortBy as keyof ShiftTableRow];

      // Manejo especial para campos anidados
      if (sortBy === 'nombre') {
        aVal = a.nombre;
        bVal = b.nombre;
      }

      let comparison = 0;
      if (aVal < bVal) comparison = -1;
      if (aVal > bVal) comparison = 1;

      return sortDirection === 'desc' ? -comparison : comparison;
    });
  }

  /**
   * Aplica paginación a las filas
   * @param rows Filas a paginar
   * @param currentPage Página actual
   * @param pageSize Tamaño de página
   * @returns Filas paginadas
   */
  private paginateRows(rows: ShiftTableRow[], currentPage: number, pageSize: number): ShiftTableRow[] {
    const startIndex = (currentPage - 1) * pageSize;
    return rows.slice(startIndex, startIndex + pageSize);
  }

  /**
   * Genera datos CSV para exportación
   * @param rows Filas a exportar
   * @param days Días del schedule
   * @returns String CSV
   */
  generateCSV(rows: ShiftTableRow[], days: any[]): string {
    const headers = [
      'Agente', 
      'Perfil', 
      'Cumplimiento', 
      ...days.slice(0, 31).map((d: any, i: number) => `Día ${i + 1}`)
    ];

    const csvRows = rows.map(row => [
      row.nombre,
      row.perfil,
      `${row.cumplimiento}%`,
      ...row.shifts.map((shift: Shift | null) => shift?.tipo || 'LIBRE')
    ]);

    return [headers, ...csvRows]
      .map(row => row.join(','))
      .join('\n');
  }

  /**
   * Genera datos Excel para exportación
   * @param rows Filas a exportar
   * @param days Días del schedule
   * @returns Datos formateados para Excel
   */
  generateExcelData(rows: ShiftTableRow[], days: any[]): any[] {
    return rows.map(row => ({
      'Agente': row.nombre,
      'Perfil': row.perfil,
      'Cumplimiento': `${row.cumplimiento}%`,
      ...days.slice(0, 31).reduce((acc: any, day: any, i: number) => {
        acc[`Día ${i + 1}`] = row.shifts[i]?.tipo || 'LIBRE';
        return acc;
      }, {})
    }));
  }
}