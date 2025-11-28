import { Component, inject, computed, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';

import { SchedulingFacadeService } from './scheduling-facade.service';
import { ControlsComponent } from './controls/controls.component';
import { AgentListComponent } from './agent-list/agent-list.component';
import { ShiftTableComponent } from './shift-table/shift-table.component';
import { CalendarViewComponent } from './calendar-view/calendar-view.component';

@Component({
  selector: 'app-scheduling',
  standalone: true,
  imports: [
    CommonModule,
    ControlsComponent,
    AgentListComponent,
    ShiftTableComponent,
    CalendarViewComponent
  ],
  templateUrl: './scheduling.component.html',
  styleUrls: ['./scheduling.component.css']
})
export class SchedulingComponent implements OnInit {
  facade = inject(SchedulingFacadeService);

  ngOnInit() {
    // Auto-generar mock datos al cargar para UX inmediata
    console.log('SchedulingComponent: Auto-generando mock schedule');
    this.facade.generateMockSchedule();
  }

  agents = this.facade.agents;
  loading = this.facade.loading;
  coverageRate = this.facade.coverageRate;
  
  avgHours = computed(() => this.facade.schedule().kpis.avgHours);
}