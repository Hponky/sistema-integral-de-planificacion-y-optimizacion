import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule, NgIf, NgFor, DecimalPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { Router } from '@angular/router';
import { Subject, takeUntil } from 'rxjs';
import { CalculatorService } from '../calculator.service';
import { AuthService } from '../../../core/services/auth.service';
import { AuthenticationStateService, AuthenticationState } from '../../../core/services/authentication-state.service';
import { NavbarComponent } from '../../../shared/components/navbar/navbar.component';
import { ResultsTableComponent } from '../results-table/results-table.component';
import { KpiCardComponent } from '../kpi-card/kpi-card.component';
import { SortConfig } from '../calculator.interfaces';
import { Segment, CalculationResult, KpiData, TableData } from '../calculator.interfaces';

@Component({
  selector: 'app-calculator',
  standalone: true,
  imports: [CommonModule, FormsModule, HttpClientModule, NgIf, NgFor, DecimalPipe, NavbarComponent, ResultsTableComponent, KpiCardComponent],
  templateUrl: './calculator.html',
  styleUrls: ['./calculator.css']
})
export class CalculatorComponent implements OnInit, OnDestroy {
  segments: Segment[] = [];
  selectedSegment: number | null = null;
  config = {
    sla_objetivo: 0.60,
    sla_tiempo: 20,
    nda_objetivo: 0.90,
    intervalo_seg: 1800,
    start_date: '',
    end_date: ''
  };
  plantillaExcel: File | null = null;

  loading: boolean = false;
  error: string | null = null;
  results: CalculationResult | null = null;
  activeTab: string = 'dimensionados';
  flashMessage: string | null = null;
  
  private destroy$ = new Subject<void>();

  constructor(
    private calculatorService: CalculatorService,
    public authService: AuthService,
    private authenticationStateService: AuthenticationStateService,
    private router: Router
  ) { }

  ngOnInit(): void {
    // Verificar estado de autenticación antes de cargar segmentos
    this.authenticationStateService.currentState$.pipe(
      takeUntil(this.destroy$)
    ).subscribe((state: AuthenticationState) => {
      if (state === AuthenticationState.AUTHENTICATED) {
        this.loadSegments();
      }
    });

    // Cargar segmentos si ya está autenticado
    if (this.authService.isAuthenticated()) {
      this.loadSegments();
    }
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadSegments(): void {
    // No cargar segmentos si no está autenticado
    if (!this.authService.isAuthenticated()) {
      return;
    }

    this.calculatorService.getSegments().subscribe({
      next: (data: Segment[]) => {
        this.segments = data;
        if (this.segments.length > 0) {
          this.selectedSegment = this.segments[0].id;
        }
      },
      error: (err) => {
        console.error('Error al cargar segmentos:', err);
        
        // Si es un error de autenticación, no mostrar error local ya que el sistema maneja el redireccionamiento
        if (err && err.name === 'SessionExpiredError') {
          // El AuthErrorHandlerService ya maneja el toast y redirección
          return;
        }
        
        this.error = 'Error al cargar los servicios disponibles.';
      }
    });
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      this.plantillaExcel = input.files[0];
    } else {
      this.plantillaExcel = null;
    }
  }

  private validateForm(): { isValid: boolean; error?: string } {
    const validations = [
      { condition: !this.selectedSegment || !this.plantillaExcel, message: 'Por favor, seleccione un segmento y cargue un archivo Excel.' },
      { condition: this.plantillaExcel && !this.plantillaExcel.name.toLowerCase().endsWith('.xlsx'), message: 'Por favor, seleccione un archivo Excel válido (.xlsx).' },
      { condition: !this.config.start_date || !this.config.end_date, message: 'Por favor, seleccione las fechas de inicio y fin del cálculo.' },
      { condition: new Date(this.config.start_date) > new Date(this.config.end_date), message: 'La fecha de inicio debe ser anterior a la fecha de fin.' },
      { condition: this.config.sla_objetivo <= 0 || this.config.sla_objetivo > 1, message: 'El SLA objetivo debe estar entre 0 y 1.' },
      { condition: this.config.sla_tiempo <= 0, message: 'El tiempo de SLA debe ser mayor a 0.' },
      { condition: this.config.nda_objetivo <= 0 || this.config.nda_objetivo > 1, message: 'El NDA objetivo debe estar entre 0 y 1.' },
      { condition: this.config.intervalo_seg <= 0, message: 'La duración del intervalo debe ser mayor a 0.' }
    ];

    const failedValidation = validations.find(v => v.condition);
    return failedValidation ? { isValid: false, error: failedValidation.message } : { isValid: true };
  }

  onSubmit(): void {
    // Verificar autenticación antes de procesar
    if (!this.authService.isAuthenticated()) {
      this.error = 'Debes estar autenticado para realizar cálculos.';
      return;
    }

    const validation = this.validateForm();
    if (!validation.isValid) {
      this.error = validation.error || null;
      return;
    }

    this.loading = true;
    this.error = null;
    this.results = null;
    this.flashMessage = null;

    const formData = new FormData();
    formData.append('segment_id', this.selectedSegment!.toString());
    formData.append('plantilla_excel', this.plantillaExcel!);
    formData.append('start_date', this.config.start_date);
    formData.append('end_date', this.config.end_date);
    formData.append('sla_objetivo', this.config.sla_objetivo.toString());
    formData.append('sla_tiempo', this.config.sla_tiempo.toString());
    formData.append('nda_objetivo', this.config.nda_objetivo.toString());
    formData.append('intervalo_seg', this.config.intervalo_seg.toString());

    this.calculatorService.calculateDimensioning(formData).subscribe({
      next: (data: CalculationResult) => {
        this.results = data;
        this.loading = false;
        this.flashMessage = 'Resultados calculados y guardados con éxito.';
      },
      error: (err) => {
        console.error('Error en el cálculo:', err);
        
        // Si es un error de autenticación, no mostrar error local ya que el sistema maneja el redireccionamiento
        if (err && err.name === 'SessionExpiredError') {
          // El AuthErrorHandlerService ya maneja el toast y redirección
          this.loading = false;
          return;
        }
        
        this.error = err.error?.error || 'Ocurrió un error al realizar el cálculo.';
        this.loading = false;
      }
    });
  }

  setActiveTab(tab: string): void {
    this.activeTab = tab;
  }

  onTableSort(sortConfig: SortConfig): void {
    // Manejar eventos de sorting desde las tablas hijas
    console.log('Sorting event received:', sortConfig);
  }

  getTableHeaders(data: TableData): string[] {
    return data.columns || [];
  }

  getTableData(data: TableData): (string | number)[][] {
    return data.data || [];
  }

  // Métodos para determinar tendencias y colores de KPIs
  getAbsentismoTrend(value: number | undefined): { value: number; direction: 'up' | 'down' | 'neutral' } | undefined {
    if (value === undefined) return undefined;
    
    // Umbral para absentismo (generalmente < 5% es bueno)
    if (value < 3) {
      return { value: 5 - value, direction: 'down' }; // Bueno, tendencia a bajar
    } else if (value > 7) {
      return { value: value - 7, direction: 'up' }; // Alto, tendencia a subir
    } else {
      return { value: 0, direction: 'neutral' }; // Normal
    }
  }

  getAbsentismoColor(value: number | undefined): string {
    if (value === undefined) return 'info';
    
    if (value < 3) return 'success';
    if (value < 5) return 'warning';
    return 'error';
  }

  getAuxiliaresTrend(value: number | undefined): { value: number; direction: 'up' | 'down' | 'neutral' } | undefined {
    if (value === undefined) return undefined;
    
    // Umbral para auxiliares (generalmente < 15% es bueno)
    if (value < 10) {
      return { value: 10 - value, direction: 'down' }; // Bueno, tendencia a bajar
    } else if (value > 20) {
      return { value: value - 20, direction: 'up' }; // Alto, tendencia a subir
    } else {
      return { value: 0, direction: 'neutral' }; // Normal
    }
  }

  getAuxiliaresColor(value: number | undefined): string {
    if (value === undefined) return 'info';
    
    if (value < 10) return 'success';
    if (value < 15) return 'warning';
    return 'error';
  }

  getDesconexionesTrend(value: number | undefined): { value: number; direction: 'up' | 'down' | 'neutral' } | undefined {
    if (value === undefined) return undefined;
    
    // Umbral para desconexiones (generalmente < 3% es bueno)
    if (value < 2) {
      return { value: 2 - value, direction: 'down' }; // Bueno, tendencia a bajar
    } else if (value > 5) {
      return { value: value - 5, direction: 'up' }; // Alto, tendencia a subir
    } else {
      return { value: 0, direction: 'neutral' }; // Normal
    }
  }

  getDesconexionesColor(value: number | undefined): string {
    if (value === undefined) return 'info';
    
    if (value < 2) return 'success';
    if (value < 3) return 'warning';
    return 'error';
  }

  getInsightMessage(kpis: KpiData | undefined): string {
    if (!kpis) return 'Calcula los indicadores para recibir recomendaciones personalizadas.';
    
    const absentismo = kpis.absentismo_pct || 0;
    const auxiliares = kpis.auxiliares_pct || 0;
    const desconexiones = kpis.desconexiones_pct || 0;
    
    if (absentismo > 7) {
      return 'El absentismo es elevado. Considera implementar programas de bienestar y flexibilidad laboral.';
    } else if (auxiliares > 20) {
      return 'El porcentaje de auxiliares es alto. Revisa la distribución de cargas y considera reentrenamiento.';
    } else if (desconexiones > 5) {
      return 'Las desconexiones son frecuentes. Optimiza los procesos técnicos y mejora la infraestructura.';
    } else if (absentismo < 3 && auxiliares < 10 && desconexiones < 2) {
      return 'Excelentes indicadores. Mantén las prácticas actuales y considera compartir mejores prácticas.';
    } else {
      return 'Los indicadores están en rangos aceptables. Continúa con el monitoreo regular.';
    }
  }

}