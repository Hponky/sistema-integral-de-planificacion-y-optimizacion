import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-optimization-config-step',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './optimization-config-step.component.html',
  styleUrls: ['./optimization-config-step.component.css']
})
export class OptimizationConfigStepComponent {
  @Input() optimizationStrategy: string = 'balanced';
  @Input() maxIterations: number = 1000;
  @Input() convergenceThreshold: number = 0.001;
  @Input() enableParallelProcessing: boolean = true;
  @Input() enableAdvancedAlgorithms: boolean = false;
  @Input() enableLogging: boolean = true;

  @Output() optimizationStrategyChange = new EventEmitter<string>();
  @Output() maxIterationsChange = new EventEmitter<number>();
  @Output() convergenceThresholdChange = new EventEmitter<number>();
  @Output() enableParallelProcessingChange = new EventEmitter<boolean>();
  @Output() enableAdvancedAlgorithmsChange = new EventEmitter<boolean>();
  @Output() enableLoggingChange = new EventEmitter<boolean>();

  optimizationStrategies = [
    { value: 'speed', label: 'Velocidad (Optimización rápida)' },
    { value: 'balanced', label: 'Equilibrado (Recomendado)' },
    { value: 'quality', label: 'Calidad (Optimización exhaustiva)' }
  ];
}