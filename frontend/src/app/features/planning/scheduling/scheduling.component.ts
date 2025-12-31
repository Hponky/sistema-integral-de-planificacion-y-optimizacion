import { Component, inject, computed, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

import { SchedulingFacadeService } from './scheduling-facade.service';
import { ControlsComponent } from './controls/controls.component';
import { AgentListComponent } from './agent-list/agent-list.component';
import { ShiftTableComponent } from './shift-table/shift-table.component';
import { CalendarViewComponent } from './calendar-view/calendar-view.component';
import { CalculationHistoryComponent } from '../../calculator/calculation-history/calculation-history.component';
import { DimensioningSelectorComponent } from './dimensioning-selector/dimensioning-selector.component';
import { ModalComponent } from '../../../shared/components/modal/modal.component';
import { ToastService } from '../../../shared/services/toast.service';
import { CoverageChartComponent } from './coverage-chart/coverage-chart.component';
import { BreakPvdTableComponent } from './break-pvd-table/break-pvd-table.component';

@Component({
  selector: 'app-scheduling',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ControlsComponent,
    AgentListComponent,
    ShiftTableComponent,
    CalendarViewComponent,
    CalculationHistoryComponent,
    DimensioningSelectorComponent,
    ModalComponent,
    CoverageChartComponent,
    BreakPvdTableComponent
  ],
  templateUrl: './scheduling.component.html',
  styleUrls: ['./scheduling.component.css']
})
export class SchedulingComponent implements OnInit {
  facade = inject(SchedulingFacadeService);
  private router = inject(Router);
  private toastService = inject(ToastService);

  selectedDimensioningId: number | null = null;

  ngOnInit() {
    // Auto-generar mock datos al cargar para UX inmediata
    console.log('SchedulingComponent: Auto-generando mock schedule');
    this.facade.generateMockSchedule();
  }

  agents = this.facade.agents;
  loading = this.facade.loading;
  coverageRate = this.facade.coverageRate;
  metrics = this.facade.metrics;
  scheduleDays = computed(() => this.facade.schedule().days);

  avgHours = computed(() => this.facade.schedule().kpis.avgHours);

  // New KPIs
  kpis = computed(() => this.facade.schedule().kpis); // Access all kpis easily
  activeAgents = computed(() => this.facade.schedule().kpis.activeAgents || 0);
  avgBmed = computed(() => this.facade.schedule().kpis.avgBmed || 0);
  avgVac = computed(() => this.facade.schedule().kpis.avgVac || 0);
  serviceLevel = computed(() => this.facade.schedule().kpis.serviceLevel || 0);
  nda = computed(() => this.facade.schedule().kpis.nda || 0);
  avgAht = computed(() => this.facade.schedule().kpis.avgAht || 0);

  onViewHistoryDetails(id: number): void {
    this.router.navigate(['/calculator'], { queryParams: { scenarioId: id } });
  }

  onSelectDimensioning(id: number): void {
    // Si id es 0 o falsy, significa deselección
    this.selectedDimensioningId = id || null;
    this.facade.setDimensioningScenario(id || null);

    if (id) {
      console.log('Selected dimensioning:', id);
    } else {
      console.log('Dimensioning deselected');
    }
  }

  // Fictitious Agents Simulation
  showFictitiousModal = false;
  fictitiousAgentsCount = computed(() => this.facade.fictitiousAgents().length);
  fictitiousAgents = this.facade.fictitiousAgents;

  fictitiousConfig: any = {
    count: 5,
    center: 'BR',
    contract: 30,
    segment: 'Inbound',
    suggestedShift: '08:00-15:00',
    windowMonday: '08:00-15:00',
    windowTuesday: '08:00-15:00',
    windowWednesday: '08:00-15:00',
    windowThursday: '08:00-15:00',
    windowFriday: '08:00-15:00',
    windowSaturday: '-',
    windowSunday: '-',
    modalidadFinde: 'UNICO',
    rotacionDominical: 'NORMAL'
  };

  openFictitiousModal() {
    this.showFictitiousModal = true;
  }

  closeFictitiousModal() {
    this.showFictitiousModal = false;
  }

  addFictitiousAgents() {
    this.facade.generateFictitiousAgents(this.fictitiousConfig);
    this.closeFictitiousModal();
    this.toastService.showSuccess(`Se han inyectado ${this.fictitiousConfig.count} agentes ficticios`, 'Simulación');
  }

  removeFictitiousAgent(id: string) {
    this.facade.removeFictitiousAgent(id);
  }

  clearFictitiousAgents() {
    this.facade.clearFictitiousAgents();
    this.toastService.showInfo('Inyectados eliminados');
  }

  // --- History Feature ---
  showHistory = false;
  showSaveModal = false;
  scenarioName = '';
  history: any[] = [];

  openSaveModal() {
    this.scenarioName = '';
    this.showSaveModal = true;
  }

  closeSaveModal() {
    this.showSaveModal = false;
    this.scenarioName = '';
  }

  async confirmSave(isTemporary: boolean = false) {
    if (!this.scenarioName.trim()) return;

    try {
      await this.facade.saveScenario(this.scenarioName.trim(), isTemporary, this.selectedDimensioningId);
      this.closeSaveModal();

      const msg = isTemporary
        ? 'El escenario de simulación se ha guardado (temporal 7 días)'
        : 'El escenario se ha guardado correctamente';

      this.toastService.showSuccess(msg, 'Guardado exitoso');

      // Refresh history list to show new item with correct status
      this.history = await this.facade.getHistory();
    } catch (e) {
      console.error(e);
      this.toastService.showError('No se pudo guardar el escenario', 'Error al guardar');
    }
  }

  async toggleHistory() {
    this.showHistory = !this.showHistory;
    if (this.showHistory) {
      try {
        this.history = await this.facade.getHistory();
      } catch (e) {
        console.error(e);
        this.toastService.showError('No se pudo cargar el historial', 'Error');
      }
    }
  }

  async loadScenario(id: number) {
    try {
      await this.facade.loadScenario(id);
      this.selectedDimensioningId = this.facade.currentDimensioningId();
      this.showHistory = false;
      this.toastService.showSuccess('El escenario se ha cargado correctamente', 'Escenario cargado');
    } catch (e) {
      console.error(e);
      this.toastService.showError('No se pudo cargar el escenario', 'Error al cargar');
    }
  }

  // --- Delete Scenario Logic ---
  showDeleteConfirmModal = false;
  scenarioToDeleteId: number | null = null;

  openDeleteModal(id: number, event: Event) {
    event.stopPropagation(); // Evitar que se cargue el escenario al hacer click en borrar
    this.scenarioToDeleteId = id;
    this.showDeleteConfirmModal = true;
  }

  closeDeleteModal() {
    this.showDeleteConfirmModal = false;
    this.scenarioToDeleteId = null;
  }

  async confirmDelete() {
    if (!this.scenarioToDeleteId) return;

    try {
      await this.facade.deleteScenario(this.scenarioToDeleteId);
      this.closeDeleteModal();
      this.toastService.showSuccess('El escenario ha sido eliminado', 'Eliminado');

      // Recargar historial
      this.history = await this.facade.getHistory();
    } catch (e) {
      console.error(e);
      this.toastService.showError('No se pudo eliminar el escenario', 'Error al eliminar');
    }
  }


}