import { Component, EventEmitter, Input, Output, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { ProgressComponent } from '../../../shared/stepper/components/progress.component';
import { ProgressStepComponent } from '../../../shared/stepper/components/progress-step.component';
import { ProgressStepDirective } from '../../../shared/stepper/directives/progress-step.directive';
import { ProgressHelperService } from '../../../shared/stepper/services/progress-helper.service';
import { UiHelper } from '../../../shared/stepper/utils/ui-helper';

import { BasicDataStepComponent } from './steps/basic-data-step.component';
import { SlaParametersStepComponent } from './steps/sla-parameters-step.component';
import { OptimizationConfigStepComponent } from './steps/optimization-config-step.component';
import { SummaryStepComponent, SummaryData } from './steps/summary-step.component';

export interface StepData {
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
  selector: 'app-calculator-stepper',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ProgressComponent,
    ProgressStepComponent,
    ProgressStepDirective,
    BasicDataStepComponent,
    SlaParametersStepComponent,
    OptimizationConfigStepComponent,
    SummaryStepComponent
  ],
  templateUrl: './calculator-stepper.component.html',
  styleUrls: ['./calculator-stepper.component.css']
})
export class CalculatorStepperComponent implements OnInit {
  @Input() segments: any[] = [];
  @Output() calculationComplete = new EventEmitter<any>();

  currentStepIndex: number = 0;
  isProcessing: boolean = false;
  calculationResult: any = null;
  errorMessage: string | null = null;
  uiHelper: UiHelper | null = null;

  stepData: StepData = {
    basicData: {
      selectedSegment: null,
      startDate: '',
      endDate: '',
      plantillaExcel: null
    },
    slaParameters: {
      slaObjetivo: 0.60,
      slaTiempo: 20,
      ndaObjetivo: 0.90
    },
    optimizationConfig: {
      optimizationStrategy: 'balanced',
      maxIterations: 1000,
      convergenceThreshold: 0.001,
      enableParallelProcessing: true,
      enableAdvancedAlgorithms: false,
      enableLogging: true
    }
  };

  steps = [
    { title: 'Datos Básicos', description: 'Información general del proyecto' },
    { title: 'Parámetros Técnicos', description: 'Configuración de SLA y NDA' },
    { title: 'Optimización', description: 'Ajustes del algoritmo de optimización' },
    { title: 'Resumen', description: 'Revisión y confirmación' }
  ];

  constructor(private progressHelper: ProgressHelperService) {}

  ngOnInit(): void {
    this.initializeUiState();
  }

  private initializeUiState(): void {
    this.uiHelper = new UiHelper(this.progressHelper);
    this.uiHelper.initializeSteps(this.steps.length);
  }

  nextStep(): void {
    if (this.currentStepIndex < this.steps.length - 1) {
      this.currentStepIndex++;
      if (this.uiHelper) {
        // Usar métodos públicos de UiHelper
        this.uiHelper.itemProgressList[this.currentStepIndex - 1].status = 'completed';
        this.uiHelper.itemProgressList[this.currentStepIndex].status = 'in_progress';
        this.uiHelper.activeIndex = this.currentStepIndex;
      }
    }
  }

  previousStep(): void {
    if (this.currentStepIndex > 0) {
      this.currentStepIndex--;
      if (this.uiHelper) {
        // Usar métodos públicos de UiHelper
        const nextIndex = this.currentStepIndex + 1;
        if (nextIndex < this.uiHelper.itemProgressList.length) {
          this.uiHelper.itemProgressList[nextIndex].status = 'pending';
        }
        this.uiHelper.itemProgressList[this.currentStepIndex].status = 'in_progress';
        this.uiHelper.activeIndex = this.currentStepIndex;
      }
    }
  }

  goToStep(stepIndex: number): void {
    if (stepIndex >= 0 && stepIndex < this.steps.length) {
      this.currentStepIndex = stepIndex;
      if (this.uiHelper) {
        this.uiHelper.activeIndex = stepIndex;
      }
    }
  }

  onBasicDataChange(field: string, value: any): void {
    if (field in this.stepData.basicData) {
      (this.stepData.basicData as any)[field] = value;
    }
  }

  onSlaParametersChange(field: string, value: any): void {
    if (field in this.stepData.slaParameters) {
      (this.stepData.slaParameters as any)[field] = value;
    }
  }

  onOptimizationConfigChange(field: string, value: any): void {
    if (field in this.stepData.optimizationConfig) {
      (this.stepData.optimizationConfig as any)[field] = value;
    }
  }

  async onConfirmCalculation(): Promise<void> {
    this.isProcessing = true;
    this.errorMessage = null;
    
    try {
      await this.performCalculation();
    } catch (error) {
      this.errorMessage = 'Error al realizar el cálculo. Por favor, inténtalo de nuevo.';
      console.error('Calculation error:', error);
    } finally {
      this.isProcessing = false;
    }
  }

  private async performCalculation(): Promise<void> {
    return new Promise((resolve) => {
      setTimeout(() => {
        this.calculationResult = {
          processingTime: '2 minutos 34 segundos',
          iterations: 856,
          slaAchieved: 0.62,
          ndaAchieved: 0.91,
          optimizationScore: 87.5
        };
        
        this.calculationComplete.emit(this.calculationResult);
        resolve();
      }, 2000);
    });
  }

  onEditStep(stepIndex: number): void {
    this.goToStep(stepIndex);
  }

  onRetryCalculation(): void {
    this.calculationResult = null;
    this.errorMessage = null;
    this.goToStep(this.steps.length - 1);
  }

  onNewCalculation(): void {
    this.resetForm();
    this.goToStep(0);
  }

  private resetForm(): void {
    this.stepData = {
      basicData: {
        selectedSegment: null,
        startDate: '',
        endDate: '',
        plantillaExcel: null
      },
      slaParameters: {
        slaObjetivo: 0.60,
        slaTiempo: 20,
        ndaObjetivo: 0.90
      },
      optimizationConfig: {
        optimizationStrategy: 'balanced',
        maxIterations: 1000,
        convergenceThreshold: 0.001,
        enableParallelProcessing: true,
        enableAdvancedAlgorithms: false,
        enableLogging: true
      }
    };
    
    this.calculationResult = null;
    this.errorMessage = null;
    this.isProcessing = false;
  }

  getSummaryData(): SummaryData {
    return {
      basicData: this.stepData.basicData,
      slaParameters: this.stepData.slaParameters,
      optimizationConfig: this.stepData.optimizationConfig
    };
  }
}