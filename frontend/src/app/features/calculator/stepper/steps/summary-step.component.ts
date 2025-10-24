import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

export interface SummaryData {
  basicData: {
    selectedSegment: number | null;
    startDate: string;
    endDate: string;
    plantillaExcel: File | null;
  };
  slaParameters: {
    slaObjetivo: number;
    slaTiempo: number;
    ndaObjetivo: number;
  };
  optimizationConfig: {
    optimizationStrategy: string;
    maxIterations: number;
    convergenceThreshold: number;
    enableParallelProcessing: boolean;
    enableAdvancedAlgorithms: boolean;
    enableLogging: boolean;
  };
}

@Component({
  selector: 'app-summary-step',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './summary-step.component.html',
  styleUrls: ['./summary-step.component.css']
})
export class SummaryStepComponent {
  @Input() summaryData: SummaryData | null = null;
  @Input() isProcessing: boolean = false;
  @Input() calculationResult: any = null;
  @Input() errorMessage: string | null = null;

  @Output() confirm = new EventEmitter<void>();
  @Output() back = new EventEmitter<void>();
  @Output() editStep = new EventEmitter<number>();

  onConfirm(): void {
    this.confirm.emit();
  }

  onBack(): void {
    this.back.emit();
  }

  onEditStep(stepIndex: number): void {
    this.editStep.emit(stepIndex);
  }

  getSegmentName(segmentId: number | null): string {
    if (segmentId === null) return 'No seleccionado';
    // Esto debería ser implementado con los datos reales de segmentos
    const segments = [
      { id: 1, name: 'Residencial' },
      { id: 2, name: 'Comercial' },
      { id: 3, name: 'Industrial' }
    ];
    const segment = segments.find(s => s.id === segmentId);
    return segment ? segment.name : 'Desconocido';
  }

  getStrategyName(strategy: string): string {
    const strategies: { [key: string]: string } = {
      'speed': 'Velocidad (Optimización rápida)',
      'balanced': 'Equilibrado (Recomendado)',
      'quality': 'Calidad (Optimización exhaustiva)'
    };
    return strategies[strategy] || strategy;
  }
}