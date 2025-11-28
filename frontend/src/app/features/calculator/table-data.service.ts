import { Injectable } from '@angular/core';
import { Observable, BehaviorSubject, of } from 'rxjs';
import { map, tap } from 'rxjs/operators';
import { TableData, SortConfig } from './calculator.interfaces';

export interface PaginationConfig {
  pageIndex: number;
  pageSize: number;
  totalItems: number;
}

export interface ExportConfig {
  filename: string;
  format: 'csv' | 'excel';
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
   * Exporta datos a formato CSV
   * @param data Datos a exportar
   * @param headers Encabezados de columna
   * @param filename Nombre del archivo
   */
  exportToCSV(data: (string | number)[][], headers: string[], filename: string): void {
    const csvContent = this.generateCSVContent(data, headers);
    this.downloadFile(csvContent, `${filename}.csv`, 'text/csv');
  }

  /**
   * Exporta datos a formato Excel (simplificado)
   * @param data Datos a exportar
   * @param headers Encabezados de columna
   * @param filename Nombre del archivo
   */
  exportToExcel(data: (string | number)[][], headers: string[], filename: string): void {
    // Para Excel completo, se necesitaría una librería como xlsx
    // Por ahora, exportamos como CSV que Excel puede abrir
    this.exportToCSV(data, headers, filename);
  }

  /**
   * Genera contenido CSV
   * @param data Datos
   * @param headers Encabezados
   * @returns Contenido CSV
   */
  private generateCSVContent(data: (string | number)[][], headers: string[]): string {
    const csvRows = [];
    
    // Agregar headers
    csvRows.push(headers.join(','));
    
    // Agregar datos
    data.forEach(row => {
      const csvRow = row.map(cell => {
        const cellValue = String(cell || '');
        // Escapar comillas y agregar si contiene comas o comillas
        return cellValue.includes(',') || cellValue.includes('"') 
          ? `"${cellValue.replace(/"/g, '""')}"` 
          : cellValue;
      });
      csvRows.push(csvRow.join(','));
    });
    
    return csvRows.join('\n');
  }

  /**
   * Descarga archivo en el navegador
   * @param content Contenido del archivo
   * @param filename Nombre del archivo
   * @param mimeType Tipo MIME
   */
  private downloadFile(content: string, filename: string, mimeType: string): void {
    const blob = new Blob([content], { type: mimeType });
    const url = window.URL.createObjectURL(blob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
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