import { Component, OnInit } from '@angular/core';
import { CommonModule, NgIf, NgFor, DecimalPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { CalculatorService } from '../calculator.service';
import { Segment, CalculationResult, KpiData, TableData } from '../calculator.interfaces';

@Component({
  selector: 'app-calculator',
  standalone: true,
  imports: [CommonModule, FormsModule, HttpClientModule, NgIf, NgFor, DecimalPipe],
  templateUrl: './calculator.html',
  styleUrls: ['./calculator.css']
})
export class CalculatorComponent implements OnInit {
  segments: Segment[] = [];
  segmentId: number | null = null;
  startDate: string = '';
  endDate: string = '';
  plantillaExcel: File | null = null;
  slaObjetivo: number = 0.60;
  slaTiempo: number = 20;
  ndaObjetivo: number = 0.90;
  intervaloSeg: number = 1800;

  isLoading: boolean = false;
  errorMessage: string | null = null;
  results: CalculationResult | null = null;
  kpis: KpiData | null = null;

  constructor(private calculatorService: CalculatorService) { }

  ngOnInit(): void {
    this.loadSegments();
    this.setInitialDates();
  }

  setInitialDates(): void {
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(today.getDate() + 1);

    this.startDate = this.formatDate(today);
    this.endDate = this.formatDate(tomorrow);
  }

  formatDate(date: Date): string {
    const year = date.getFullYear();
    const month = ('0' + (date.getMonth() + 1)).slice(-2);
    const day = ('0' + date.getDate()).slice(-2);
    return `${year}-${month}-${day}`;
  }

  loadSegments(): void {
    this.calculatorService.getSegments().subscribe({
      next: (data: Segment[]) => {
        this.segments = data;
        if (this.segments.length > 0) {
          this.segmentId = this.segments[0].id;
        }
      },
      error: (err) => {
        console.error('Error al cargar segmentos:', err);
        this.errorMessage = 'Error al cargar los servicios disponibles.';
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

  onSubmit(): void {
    if (!this.segmentId || !this.startDate || !this.endDate || !this.plantillaExcel) {
      this.errorMessage = 'Por favor, complete todos los campos requeridos.';
      return;
    }

    this.isLoading = true;
    this.errorMessage = null;
    this.results = null;
    this.kpis = null;

    const formData = new FormData();
    formData.append('segment_id', this.segmentId.toString());
    formData.append('start_date', this.startDate);
    formData.append('end_date', this.endDate);
    formData.append('plantilla_excel', this.plantillaExcel);
    formData.append('sla_objetivo', this.slaObjetivo.toString());
    formData.append('sla_tiempo', this.slaTiempo.toString());
    formData.append('nda_objetivo', this.ndaObjetivo.toString());
    formData.append('intervalo_seg', this.intervaloSeg.toString());

    this.calculatorService.calculateDimensioning(formData).subscribe({
      next: (data: CalculationResult) => {
        this.results = data;
        this.kpis = data.kpis;
        this.isLoading = false;
        // Aquí podrías añadir una notificación de éxito si fuera necesario
      },
      error: (err) => {
        console.error('Error en el cálculo:', err);
        this.errorMessage = err.error?.error || 'Ocurrió un error al realizar el cálculo.';
        this.isLoading = false;
      }
    });
  }
}