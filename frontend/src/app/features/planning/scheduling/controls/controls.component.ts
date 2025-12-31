
import { Component, inject, signal, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RulesConfigurationComponent } from '../rules-configuration/rules-configuration.component';
import type { SchedulingRules } from '../interfaces';

import { SchedulingFacadeService } from '../scheduling-facade.service';

@Component({
  selector: 'app-controls',
  standalone: true,
  imports: [CommonModule, FormsModule, RulesConfigurationComponent],
  templateUrl: './controls.component.html',
  styleUrls: ['./controls.component.css']
})
export class ControlsComponent {
  private facade = inject(SchedulingFacadeService);
  public loading = this.facade.loading;
  public downloadUrl = this.facade.downloadUrl;

  startDateStr = new Date().toISOString().split('T')[0];
  endDateStr = '';
  selectedFile: File | null = null;
  selectedAbsencesFile: File | null = null;

  showRulesModal = signal(false);

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files?.length) {
      this.selectedFile = input.files[0];
    }
  }

  removeFile(event: Event): void {
    event.stopPropagation();
    this.selectedFile = null;
  }

  // --- Absences File ---
  onAbsencesFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files?.length) {
      this.selectedAbsencesFile = input.files[0];
    }
  }

  removeAbsencesFile(event: Event): void {
    event.stopPropagation();
    this.selectedAbsencesFile = null;
  }

  formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  }

  @Input() selectedScenarioId: number | null = null;

  fictitiousAgents = this.facade.fictitiousAgents;

  generate(): void {
    if (!this.selectedScenarioId) {
      alert('Por favor selecciona un escenario de dimensionamiento antes de generar el horario.');
      return;
    }

    const hasFictitious = this.fictitiousAgents().length > 0;

    if (this.selectedFile || hasFictitious) {
      this.facade.uploadAndGenerate(
        this.selectedFile,
        this.startDateStr,
        this.endDateStr,
        this.selectedAbsencesFile,
        this.selectedScenarioId
      );
    } else {
      alert('Por favor carga el archivo de personal o inyecta agentes ficticios para simulación.');
    }
  }

  openRules() {
    this.showRulesModal.set(true);
  }

  closeRules() {
    this.showRulesModal.set(false);
  }

  onRulesSaved(rules: SchedulingRules) {
    this.facade.rulesConfig.set(rules);
    this.showRulesModal.set(false);
  }

  onDownloadReport(event: Event): void {
    event.preventDefault();
    const url = this.downloadUrl();
    if (url) {
      this.facade.downloadReport(url);
    }
  }
}
