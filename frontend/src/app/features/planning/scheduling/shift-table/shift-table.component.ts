import { Component, OnInit, OnDestroy, ChangeDetectionStrategy, DestroyRef, inject, signal, computed, effect } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { SchedulingFacadeService } from '../scheduling-facade.service';
import { ShiftTableDataService, ShiftTableState, ShiftTableConfig } from '../services/shift-table-data.service';
import { ShiftTableRow, Schedule, Shift } from '../interfaces';
import * as XLSX from 'xlsx';

@Component({
  selector: 'app-shift-table',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './shift-table.component.html',
  styleUrls: ['./shift-table.component.css'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class ShiftTableComponent implements OnInit, OnDestroy {
  private readonly facade = inject(SchedulingFacadeService);
  private readonly shiftTableDataService = inject(ShiftTableDataService);
  private readonly destroyRef = inject(DestroyRef);

  // Signals para manejar el estado reactivo
  readonly state = signal<ShiftTableState | null>(null);
  readonly searchTerm = signal('');
  readonly currentPage = signal(1);
  readonly pageSize = signal(20);
  readonly sortBy = signal('nombre');
  readonly sortDirection = signal<'asc' | 'desc'>('asc');
  

  // Computeds para valores derivados
  readonly paginatedRows = computed(() => this.state()?.paginatedRows || []);
  readonly totalRecords = computed(() => this.state()?.totalRecords || 0);
  readonly totalPages = computed(() => this.state()?.totalPages || 0);
  readonly days = computed(() => this.facade.schedule().days || []);
  
  // Computed para detectar si es móvil
  readonly isMobile = computed(() => {
    if (typeof window === 'undefined') return false;
    return window.innerWidth < 768;
  });

  constructor() {
    // Suscribirse a los cambios del estado del servicio
    this.shiftTableDataService.state$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((newState: ShiftTableState) => {
        this.state.set(newState);
      });

    // Efecto para reaccionar a cambios en el schedule del facade
    effect(() => {
      const schedule = this.facade.schedule();
      if (schedule?.agents?.length && schedule?.days?.length) {
        // Usar un timeout para evitar el error de signal writes en effect
        setTimeout(() => {
          this.shiftTableDataService.setOriginalData(schedule);
        }, 0);
      }
    });
  }

  ngOnInit(): void {
    // Inicializar con datos mock si no hay nada
    if (!this.facade.schedule().agents?.length) {
      this.facade.generateMockSchedule();
    }
    
    // Inicializar listeners responsivos
  }

  ngOnDestroy(): void {
  }

  /**
   * Maneja el cambio en el término de búsqueda
   */
  onSearchChange(event: Event): void {
    const target = event.target as HTMLInputElement;
    this.searchTerm.set(target.value);
    this.updateConfig({ searchTerm: target.value, currentPage: 1 });
  }

  /**
   * Maneja la tecla Enter en la búsqueda
   */
  onSearchEnter(event: Event): void {
    event.preventDefault();
    this.updateConfig({ currentPage: 1 });
  }

  /**
   * Limpia el término de búsqueda
   */
  clearSearch(): void {
    this.searchTerm.set('');
    this.updateConfig({ searchTerm: '', currentPage: 1 });
  }

  /**
   * Maneja el cambio de ordenamiento
   */
  onSortChange(field: string): void {
    const currentDirection = this.sortDirection();
    const newDirection = this.sortBy() === field && currentDirection === 'asc' ? 'desc' : 'asc';
    
    this.sortBy.set(field);
    this.sortDirection.set(newDirection);
    this.updateConfig({ sortBy: field, sortDirection: newDirection });
  }

  /**
   * Maneja el cambio de página
   */
  onPageChange(page: number): void {
    this.currentPage.set(page);
    this.updateConfig({ currentPage: page });
  }

  /**
   * Actualiza la configuración del servicio
   */
  private updateConfig(updates: Partial<ShiftTableConfig>): void {
    this.shiftTableDataService.updateConfig(updates);
  }

  /**
   * Genera las páginas para la paginación
   */
  getPaginationPages(): number[] {
    const totalPages = this.totalPages();
    const currentPage = this.currentPage();
    
    if (totalPages <= 7) {
      return Array.from({ length: totalPages }, (_, i) => i + 1);
    }

    const pages: number[] = [];
    
    // Siempre mostrar la primera página
    pages.push(1);
    
    // Mostrar páginas alrededor de la actual
    if (currentPage > 3) {
      pages.push(-1); // Ellipsis
    }
    
    const start = Math.max(2, currentPage - 1);
    const end = Math.min(totalPages - 1, currentPage + 1);
    
    for (let i = start; i <= end; i++) {
      pages.push(i);
    }
    
    if (currentPage < totalPages - 2) {
      pages.push(-1); // Ellipsis
    }
    
    // Siempre mostrar la última página
    if (totalPages > 1) {
      pages.push(totalPages);
    }
    
    return pages.filter(page => page !== -1 || pages.indexOf(page) === pages.lastIndexOf(page));
  }

  /**
   * Obtiene el rango de registros mostrados
   */
  getPaginationRange(): string {
    const currentPage = this.currentPage();
    const pageSize = this.pageSize();
    const totalRecords = this.totalRecords();
    
    if (totalRecords === 0) return '0-0';
    
    const start = (currentPage - 1) * pageSize + 1;
    const end = Math.min(currentPage * pageSize, totalRecords);
    
    return `${start}-${end}`;
  }

  /**
   * Función de tracking para optimizar el rendimiento
   */
  trackByFn(index: number, row: ShiftTableRow): string {
    return row.id.toString();
  }

  /**
   * Determina si una fila debe ser resaltada
   */
  shouldHighlightRow(row: ShiftTableRow): boolean {
    // Lógica para resaltar filas según criterios específicos
    return row.cumplimiento < 80; // Ejemplo: resaltar agentes con bajo cumplimiento
  }

  /**
   * Exporta los datos a CSV
   */
  exportCSV(): void {
    const currentState = this.state();
    const days = this.days();
    
    if (!currentState?.filteredRows?.length) {
      return;
    }

    const csvContent = this.shiftTableDataService.generateCSV(currentState.filteredRows, days);
    this.downloadFile(csvContent, 'horarios.csv', 'text/csv');
  }

  /**
   * Exporta los datos a Excel
   */
  exportExcel(): void {
    const currentState = this.state();
    const days = this.days();
    
    if (!currentState?.filteredRows?.length) {
      return;
    }

    const excelData = this.shiftTableDataService.generateExcelData(currentState.filteredRows, days);
    
    const ws = XLSX.utils.json_to_sheet(excelData);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "Horarios");
    XLSX.writeFile(wb, "horarios.xlsx");
  }

  /**
   * Descarga un archivo con el contenido y tipo especificados
   */
  private downloadFile(content: string, filename: string, type: string): void {
    const blob = new Blob([content], { type });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }

}