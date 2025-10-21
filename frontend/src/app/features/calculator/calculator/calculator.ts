import { Component, OnInit, ViewEncapsulation } from '@angular/core';
import { CommonModule, NgIf, NgFor, DecimalPipe } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { CalculatorService } from '../calculator.service';
import { MaterialModule } from '../../../shared/material.module';
import { NavbarComponent } from '../../../shared/components/navbar/navbar.component';
import { Segment, CalculationResult, TableData } from '../calculator.interfaces';
import { MatSnackBar } from '@angular/material/snack-bar';

@Component({
  selector: 'app-calculator',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    HttpClientModule,
    NgIf,
    NgFor,
    DecimalPipe,
    MaterialModule,
    NavbarComponent
  ],
  templateUrl: './calculator.html',
  styleUrls: ['./calculator.css'],
  encapsulation: ViewEncapsulation.None
})
export class CalculatorComponent implements OnInit {
  segments: Segment[] = [];
  selectedSegment: number | null = null;
  plantillaExcel: File | null = null;

  loading: boolean = false;
  error: string | null = null;
  results: CalculationResult | null = null;
  activeTab: string = 'dimensionados';
  flashMessage: string | null = null;

  // Formularios reactivos para cada paso
  parametrosForm: FormGroup;
  fechasForm: FormGroup;
  archivoForm: FormGroup;

  constructor(
    private readonly calculatorService: CalculatorService,
    private readonly fb: FormBuilder,
    private readonly snackBar: MatSnackBar
  ) {
    // Inicializar formularios reactivos
    this.parametrosForm = this.fb.group({
      sla_objetivo: [0.60, [Validators.required, Validators.min(0), Validators.max(1)]],
      sla_tiempo: [20, [Validators.required, Validators.min(1)]],
      nda_objetivo: [0.90, [Validators.required, Validators.min(0), Validators.max(1)]],
      intervalo_seg: [1800, [Validators.required, Validators.min(1)]]
    });

    this.fechasForm = this.fb.group({
      start_date: ['', Validators.required],
      end_date: ['', Validators.required]
    });

    this.archivoForm = this.fb.group({
      plantilla_excel: [null, Validators.required]
    });
  }

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
        this.error = 'Error al cargar los servicios disponibles.';
      }
    });
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      this.plantillaExcel = input.files[0];
      this.archivoForm.patchValue({ plantilla_excel: this.plantillaExcel });
    } else {
      this.plantillaExcel = null;
      this.archivoForm.patchValue({ plantilla_excel: null });
    }
  }

  private validateForm(): { isValid: boolean; error?: string } {
    // Validar que todos los formularios sean válidos
    if (!this.parametrosForm.valid) {
      return { isValid: false, error: 'Por favor, complete correctamente los parámetros de cálculo.' };
    }

    if (!this.fechasForm.valid) {
      return { isValid: false, error: 'Por favor, seleccione las fechas de inicio y fin del cálculo.' };
    }

    if (!this.archivoForm.valid || !this.selectedSegment) {
      return { isValid: false, error: 'Por favor, seleccione un segmento y cargue un archivo Excel.' };
    }

    // Validaciones adicionales
    const fechas = this.fechasForm.value;
    if (new Date(fechas.start_date) > new Date(fechas.end_date)) {
      return { isValid: false, error: 'La fecha de inicio debe ser anterior a la fecha de fin.' };
    }

    if (this.plantillaExcel && !this.plantillaExcel.name.toLowerCase().endsWith('.xlsx')) {
      return { isValid: false, error: 'Por favor, seleccione un archivo Excel válido (.xlsx).' };
    }

    return { isValid: true };
  }

  onSubmit(): void {
    const validation = this.validateForm();
    if (!validation.isValid) {
      this.error = validation.error || null;
      this.snackBar.open(validation.error || 'Error en el formulario', 'Cerrar', {
        duration: 5000,
        panelClass: ['error-snackbar']
      });
      return;
    }

    this.loading = true;
    this.error = null;
    this.results = null;
    this.flashMessage = null;

    // Obtener valores de los formularios
    const parametros = this.parametrosForm.value;
    const fechas = this.fechasForm.value;
    const archivo = this.archivoForm.value;

    const formData = new FormData();
    formData.append('segment_id', this.selectedSegment!.toString());
    formData.append('plantilla_excel', this.plantillaExcel!);
    formData.append('start_date', fechas.start_date);
    formData.append('end_date', fechas.end_date);
    formData.append('sla_objetivo', parametros.sla_objetivo.toString());
    formData.append('sla_tiempo', parametros.sla_tiempo.toString());
    formData.append('nda_objetivo', parametros.nda_objetivo.toString());
    formData.append('intervalo_seg', parametros.intervalo_seg.toString());

    this.calculatorService.calculateDimensioning(formData).subscribe({
      next: (data: CalculationResult) => {
        this.results = data;
        this.loading = false;
        this.flashMessage = 'Resultados calculados y guardados con éxito.';
        this.snackBar.open('Cálculo completado exitosamente', 'Cerrar', {
          duration: 3000,
          panelClass: ['success-snackbar']
        });
      },
      error: (err) => {
        console.error('Error en el cálculo:', err);
        this.error = err.error?.error || 'Ocurrió un error al realizar el cálculo.';
        this.loading = false;
        this.snackBar.open(this.error || 'Ocurrió un error al realizar el cálculo.', 'Cerrar', {
          duration: 5000,
          panelClass: ['error-snackbar']
        });
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