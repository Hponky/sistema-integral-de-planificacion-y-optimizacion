import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';

import { SchedulingFacadeService } from '../scheduling-facade.service';
import type { Agent } from '../interfaces';

@Component({
  selector: 'app-agent-list',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './agent-list.component.html',
  styleUrls: ['./agent-list.component.css']
})
export class AgentListComponent {
  protected facade = inject(SchedulingFacadeService);
  protected agents = this.facade.agents;
}