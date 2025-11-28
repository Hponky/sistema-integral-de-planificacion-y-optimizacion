import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { SchedulingFacadeService } from '../scheduling-facade.service';
import type { DateRange } from '../interfaces';

@Component({
  selector: 'app-controls',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './controls.component.html',
  styleUrls: ['./controls.component.css']
})
export class ControlsComponent {
  private facade = inject(SchedulingFacadeService);
  public loading = this.facade.loading;

  startDateStr = new Date().toISOString().split('T')[0];
  endDateStr = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
  numAgents = 8;

  generate(): void {
    const range: DateRange = {
      startDate: new Date(this.startDateStr),
      endDate: new Date(this.endDateStr),
      numAgents: this.numAgents
    };
    this.facade.loadMockSchedule(range);
  }
}