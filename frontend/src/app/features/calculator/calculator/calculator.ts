import { Component, OnInit } from '@angular/core';
import { CommonModule, NgIf, NgFor, DecimalPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { Router } from '@angular/router';
import { CalculatorService } from '../calculator.service';
import { AuthService } from '../../../core/services/auth.service';
import { NavbarComponent } from '../../../shared/components/navbar/navbar.component';
import { Segment, CalculationResult, KpiData, TableData } from '../calculator.interfaces';

@Component({
  selector: 'app-calculator',
  standalone: true,
  imports: [CommonModule, FormsModule, HttpClientModule, NgIf, NgFor, DecimalPipe, NavbarComponent],
  templateUrl: './calculator.html',
  styleUrls: ['./calculator.css']
})
export class CalculatorComponent implements OnInit {
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

  constructor(
    private calculatorService: CalculatorService,
    public authService: AuthService,
    private router: Router
  ) { }

  ngOnInit(): void {
    this.loadSegments();
  }

  loadSegments(): void {
    this.calculatorService.getSegments().subscribe({
      next: (data: Segment[]) => {
        this.segments = data;
        if (this.segments.length > 0) {
          this.selectedSegment = this.segments[0].id;
        }
      },
      error: (err) => {
        console.error('Error al cargar segmentos:', err);
        
        if (err && err.name === 'SessionExpiredError') {
          this.error = 'Tu sesión ha expirado. Por favor, inicia sesión nuevamente.';
        } else {
          this.error = 'Error al cargar los servicios disponibles.';
        }
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
        
        if (err && err.name === 'SessionExpiredError') {
          this.error = 'Tu sesión ha expirado. Por favor, inicia sesión nuevamente.';
        } else {
          this.error = err.error?.error || 'Ocurrió un error al realizar el cálculo.';
        }
        this.loading = false;
      }
    });
  }

  setActiveTab(tab: string): void {
    this.activeTab = tab;
  }

  getTableHeaders(data: TableData): string[] {
    return data.columns || [];
  }

  getTableData(data: TableData): (string | number)[][] {
    return data.data || [];
  }

}