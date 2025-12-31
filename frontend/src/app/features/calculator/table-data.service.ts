import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';
import { SortConfig } from './calculator.interfaces';
import * as XLSX from 'xlsx';

export interface PaginationConfig {
  pageIndex: number;
  pageSize: number;
  totalItems: number;
}

export interface ExportConfig {
  filename: string;
  format: 'excel';
}

@Injectable({
  providedIn: 'root'
})
export class TableDataService {
  private exportSubject = new BehaviorSubject<ExportConfig | null>(null);
  private paginationSubject = new BehaviorSubject<PaginationConfig>({
    pageIndex: 0,
    pageSize: 10,
    totalItems: 0
  });

  // Observable para exportación
  exportConfig$ = this.exportSubject.asObservable();

  // Observable para paginación
  paginationConfig$ = this.paginationSubject.asObservable();

  /**
   * Aplica sorting a los datos de la tabla
   * @param data Datos originales
   * @param sortConfig Configuración de ordenamiento
   * @returns Datos ordenados
   */
  applySorting(data: (string | number)[][], sortConfig: SortConfig): (string | number)[][] {
    if (!sortConfig.column || !data || data.length === 0) {
      return data;
    }

    const columnIndex = this.getColumnIndex(data[0], sortConfig.column);
    if (columnIndex === -1) {
      return data;
    }

    return [...data].sort((a, b) => {
      const valA = String(a[columnIndex] || '').toLowerCase();
      const valB = String(b[columnIndex] || '').toLowerCase();

      if (valA < valB) {
        return sortConfig.direction === 'asc' ? -1 : 1;
      }
      if (valA > valB) {
        return sortConfig.direction === 'asc' ? 1 : -1;
      }
      return 0;
    });
  }

  /**
   * Filtra datos basados en término de búsqueda
   * @param data Datos originales
   * @param searchTerm Término de búsqueda
   * @returns Datos filtrados
   */
  filterData(data: (string | number)[][], searchTerm: string): (string | number)[][] {
    if (!searchTerm || !data || data.length === 0) {
      return data;
    }

    const term = searchTerm.toLowerCase().trim();
    return data.filter(row =>
      row.some(cell =>
        String(cell || '').toLowerCase().includes(term)
      )
    );
  }

  /**
   * Aplica paginación a los datos
   * @param data Datos completos
   * @param pageIndex Índice de página actual
   * @param pageSize Tamaño de página
   * @returns Datos paginados
   */
  paginateData(data: (string | number)[][], pageIndex: number, pageSize: number): (string | number)[][] {
    if (!data || data.length === 0) {
      return [];
    }

    const startIndex = pageIndex * pageSize;
    const endIndex = startIndex + pageSize;
    return data.slice(startIndex, endIndex);
  }

  /**
   * Actualiza configuración de paginación
   * @param config Nueva configuración de paginación
   */
  updatePagination(config: Partial<PaginationConfig>): void {
    const current = this.paginationSubject.value;
    this.paginationSubject.next({ ...current, ...config });
  }

  /**
   * Exporta datos a formato Excel (usando la librería xlsx)
   * @param data Datos a exportar
   * @param headers Encabezados de columna
   * @param filename Nombre del archivo
   */
  exportToExcel(data: (string | number)[][], headers: string[], filename: string): void {
    const worksheet = XLSX.utils.aoa_to_sheet([headers, ...data]);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Resultados');

    // Generar buffer
    const excelBuffer: any = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });
    this.saveAsExcelFile(excelBuffer, filename);
  }

  /**
   * Guarda el buffer como un archivo Excel en el navegador
   * @param buffer Buffer de datos de Excel
   * @param fileName Nombre del archivo
   */
  private saveAsExcelFile(buffer: any, fileName: string): void {
    const data: Blob = new Blob([buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;charset=UTF-8' });
    const url = window.URL.createObjectURL(data);
    const link = document.createElement('a');
    link.href = url;
    link.download = fileName + '.xlsx';
    document.body.appendChild(link);
    link.click();

    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }


  /**
   * Obtiene índice de columna por nombre
   * @param firstRow Primera fila (headers)
   * @param columnName Nombre de columna
   * @returns Índice de columna o -1 si no existe
   */
  private getColumnIndex(firstRow: (string | number)[], columnName: string): number {
    return firstRow.findIndex(header =>
      String(header).toLowerCase() === columnName.toLowerCase()
    );
  }

  /**
   * Inicia exportación con configuración
   * @param config Configuración de exportación
   */
  triggerExport(config: ExportConfig): void {
    this.exportSubject.next(config);
  }

  /**
   * Limpia configuración de exportación
   */
  clearExportConfig(): void {
    this.exportSubject.next(null);
  }
}