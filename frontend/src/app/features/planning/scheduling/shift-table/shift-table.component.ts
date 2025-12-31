import { Component, OnInit, OnDestroy, ChangeDetectionStrategy, DestroyRef, inject, signal, computed, effect } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { SchedulingFacadeService } from '../scheduling-facade.service';
import { ShiftTableDataService, ShiftTableState, ShiftTableConfig } from '../services/shift-table-data.service';
import { ShiftTableRow, Schedule, Shift } from '../interfaces';
import * as XLSX from 'xlsx';
import { registerLocaleData } from '@angular/common';
import localeEs from '@angular/common/locales/es';

registerLocaleData(localeEs, 'es');


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

  readonly editingShift = signal<{ row: ShiftTableRow, date: string, shift: Shift | null | undefined } | null>(null);

  // Signals for Edit Form State
  readonly editTypeSignal = signal('LIBRE');
  readonly editLabelSignal = signal('VAC');
  readonly editStartSignal = signal('08:00');
  readonly editEndSignal = signal('16:00');

  // Toggle para mostrar/ocultar breaks y PVDs
  readonly showActivities = signal(true);

  toggleActivities() {
    this.showActivities.set(!this.showActivities());
  }




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

  onEditShift(row: ShiftTableRow, date: string, shift: Shift | null | undefined): void {
    this.editingShift.set({ row, date, shift });

    // Initialize form signals
    if (!shift) {
      this.editTypeSignal.set('LIBRE');
      this.editLabelSignal.set('VAC');
      this.editStartSignal.set('08:00');
      this.editEndSignal.set('16:00');
      // Initialize empty activity form
      this.activityForm.set({ inicio_descanso: '', fin_descanso: '', pvds: ['', '', '', '', '', '', '', '', '', ''] });
    } else {
      const type = shift.tipo || '';
      const label = shift.label || '';
      const isAbsence = ['BMED', 'VAC', 'AUS', 'ABSENCE'].includes(type) || ['BMED', 'VAC', 'AUS'].includes(label);

      if (isAbsence) {
        this.editTypeSignal.set('ABSENCE');
        this.editLabelSignal.set(['BMED', 'VAC', 'AUS'].includes(label) ? label : 'AUS');
        this.activityForm.set({ inicio_descanso: '', fin_descanso: '', pvds: ['', '', '', '', '', '', '', '', '', ''] });
      } else {
        this.editTypeSignal.set('WORK');
        this.editStartSignal.set(shift.inicio || '08:00');
        this.editEndSignal.set(shift.fin || '16:00');

        // Load existing activities
        const breakAct = this.getBreak(shift);
        const pvds = shift.activities?.filter((a: any) => a.type === 'PVD').map((a: any) => a.startStr) || [];
        const pvdList = [...pvds];
        while (pvdList.length < 10) pvdList.push('');

        this.activityForm.set({
          inicio_descanso: breakAct?.startStr || '',
          fin_descanso: breakAct?.endStr || '',
          pvds: pvdList
        });
      }
    }
  }

  closeEdit(): void {
    this.editingShift.set(null);
  }

  saveEdit(): void {
    const current = this.editingShift();
    if (!current) return;

    const type = this.editTypeSignal();
    const label = this.editLabelSignal();
    const start = this.editStartSignal();
    const end = this.editEndSignal();

    let newShiftPayload: any = null;

    if (type === 'LIBRE') {
      newShiftPayload = {
        type: 'OFF',
        label: 'LIBRE',
        start_time: null,
        end_time: null,
        duration_minutes: 0
      };
    } else if (type === 'ABSENCE') {

      newShiftPayload = {
        type: 'ABSENCE',
        label: label || 'AUS',
        start_time: '00:00',
        end_time: '23:59'
      };
    } else {
      // TURN / WORK
      newShiftPayload = {
        type: 'WORK',
        label: '', // Reset label for WORK shifts to avoid 'VAC' defaults
        start_time: start || '08:00',
        end_time: end || '16:00'
      };

      // Build activities from form
      const actForm = this.activityForm();
      const manualActivities: any[] = [];

      if (actForm.inicio_descanso && actForm.fin_descanso) {
        manualActivities.push({ type: 'BREAK', startStr: actForm.inicio_descanso, endStr: actForm.fin_descanso });
      }

      actForm.pvds.forEach((p: string) => {
        if (p) {
          const [h, m] = p.split(':').map(Number);
          const endMin = m + 5;
          const endH = endMin >= 60 ? h + 1 : h;
          const endM = endMin >= 60 ? endMin - 60 : endMin;
          const endStr = `${endH.toString().padStart(2, '0')}:${endM.toString().padStart(2, '0')}`;
          manualActivities.push({ type: 'PVD', startStr: p, endStr });
        }
      });

      // Add activities to payload if any were defined
      if (manualActivities.length > 0) {
        newShiftPayload.activities = manualActivities;
        newShiftPayload.manual_activities = true;
      }
    }

    // Call Facade
    this.facade.updateSchedule(current.row.id, current.date, newShiftPayload);
    this.closeEdit();
  }

  /**
   * Verifica si una fecha es domingo (ajustado para evitar desfase de zona horaria)
   */
  isSunday(dateStr: string): boolean {
    if (!dateStr) return false;
    const parts = dateStr.split('-');
    const date = new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]));
    return date.getDay() === 0; // 0 = Domingo
  }

  /**
   * Obtiene el nombre abreviado del día en español (ajustado para evitar desfase)
   */
  getDayName(dateStr: string): string {
    if (!dateStr) return '';
    const parts = dateStr.split('-');
    const date = new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]));
    const dayNames = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];
    return dayNames[date.getDay()];
  }

  /**
   * Calcula las horas trabajadas en una semana para un agente
   * weekEndIndex es el índice del domingo que cierra la semana
   */
  getWeeklyHours(row: ShiftTableRow, weekEndIndex: number): number {
    // Calcular inicio de la semana (7 días antes o desde el inicio)
    const weekStartIndex = Math.max(0, weekEndIndex - 6);
    let totalMinutes = 0;

    for (let i = weekStartIndex; i <= weekEndIndex; i++) {
      const shift = row.shifts[i];
      if (shift && shift.durationMinutes) {
        totalMinutes += shift.durationMinutes;
      }
    }

    return Math.round((totalMinutes / 60) * 10) / 10;
  }

  getBreak(shift: any) {
    return shift.activities?.find((a: any) => a.type === 'BREAK');
  }

  getPvdCount(shift: any) {
    return shift.activities?.filter((a: any) => a.type === 'PVD').length || 0;
  }

  getPvds(shift: any) {
    return shift.activities?.filter((a: any) => a.type === 'PVD') || [];
  }

  // --- Manual Activity Editing ---
  readonly editingActivities = signal<{ row: ShiftTableRow, date: string, shift: any } | null>(null);
  readonly activityForm = signal<any>({ inicio_descanso: '', fin_descanso: '', pvds: [] });

  onEditActivities(row: ShiftTableRow, date: string, shift: any) {
    this.editingActivities.set({ row, date, shift });
    const breakAct = this.getBreak(shift);
    const pvds = shift.activities?.filter((a: any) => a.type === 'PVD').map((a: any) => a.startStr) || [];

    // Ensure 10 slots for PVDs
    const pvdList = [...pvds];
    while (pvdList.length < 10) pvdList.push('');

    this.activityForm.set({
      inicio_descanso: breakAct?.startStr || '',
      fin_descanso: breakAct?.endStr || '',
      pvds: pvdList
    });
  }

  async saveActivities() {
    const current = this.editingActivities();
    if (!current) return;

    const form = this.activityForm();
    const manualActivities: any[] = [];
    if (form.inicio_descanso && form.fin_descanso) {
      manualActivities.push({ type: 'BREAK', startStr: form.inicio_descanso, endStr: form.fin_descanso });
    }
    form.pvds.forEach((p: string) => {
      if (p) {
        // Assume 5 min duration
        const [h, m] = p.split(':').map(Number);
        const endStr = `${h.toString().padStart(2, '0')}:${(m + 5).toString().padStart(2, '0')}`; // Simple add
        manualActivities.push({ type: 'PVD', startStr: p, endStr });
      }
    });

    await this.facade.updateActivities(current.row.id, current.date, manualActivities);
    this.editingActivities.set(null);
  }
}
