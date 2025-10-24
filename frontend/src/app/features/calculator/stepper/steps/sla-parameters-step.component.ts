import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-sla-parameters-step',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './sla-parameters-step.component.html',
  styleUrls: ['./sla-parameters-step.component.css']
})
export class SlaParametersStepComponent {
  @Input() slaObjetivo: number = 0.60;
  @Input() slaTiempo: number = 20;
  @Input() ndaObjetivo: number = 0.90;

  @Output() slaObjetivoChange = new EventEmitter<number>();
  @Output() slaTiempoChange = new EventEmitter<number>();
  @Output() ndaObjetivoChange = new EventEmitter<number>();
}