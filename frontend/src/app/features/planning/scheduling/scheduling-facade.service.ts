import { Injectable, signal, computed } from '@angular/core';

import type { Agent, Schedule, DateRange, Shift, Break } from './interfaces';

const MOCK_AGENTS: Agent[] = [
  { id: 1, nombre: 'Juan Pérez', perfil: 'Senior', avatar: '👨‍💼' },
  { id: 2, nombre: 'María López', perfil: 'Junior', avatar: '👩‍💼' },
  { id: 3, nombre: 'Carlos García', perfil: 'Senior', avatar: '👨‍💼' },
  { id: 4, nombre: 'Ana Martínez', perfil: 'Junior', avatar: '👩‍💼' },
  { id: 5, nombre: 'Luis Rodríguez', perfil: 'Senior', avatar: '👨‍💼' },
  { id: 6, nombre: 'Sofía Hernández', perfil: 'Junior', avatar: '👩‍💼' },
  { id: 7, nombre: 'Pedro Sánchez', perfil: 'Senior', avatar: '👨‍💼' },
  { id: 8, nombre: 'Laura Torres', perfil: 'Junior', avatar: '👩‍💼' },
  { id: 9, nombre: 'Miguel Ángel', perfil: 'Senior', avatar: '👨‍💼' },
  { id: 10, nombre: 'Elena Ruiz', perfil: 'Junior', avatar: '👩‍💼' },
  { id: 11, nombre: 'David Morales', perfil: 'Senior', avatar: '👨‍💼' },
  { id: 12, nombre: 'Carmen Díaz', perfil: 'Junior', avatar: '👩‍💼' },
  { id: 13, nombre: 'José Navarro', perfil: 'Senior', avatar: '👨‍💼' },
  { id: 14, nombre: 'Paula Gómez', perfil: 'Junior', avatar: '👩‍💼' },
  { id: 15, nombre: 'Antonio Silva', perfil: 'Senior', avatar: '👨‍💼' },
  { id: 16, nombre: 'Lucía Vega', perfil: 'Junior', avatar: '👩‍💼' },
  { id: 17, nombre: 'Raúl Castro', perfil: 'Senior', avatar: '👨‍💼' },
  { id: 18, nombre: 'Sara Blanco', perfil: 'Junior', avatar: '👩‍💼' },
  { id: 19, nombre: 'Fernando Ortiz', perfil: 'Senior', avatar: '👨‍💼' },
  { id: 20, nombre: 'Nerea Ramos', perfil: 'Junior', avatar: '👩‍💼' },
  { id: 21, nombre: 'Víctor Luna', perfil: 'Senior', avatar: '👨‍💼' },
  { id: 22, nombre: 'Marta Flores', perfil: 'Junior', avatar: '👩‍💼' },
  { id: 23, nombre: 'Diego Molina', perfil: 'Senior', avatar: '👨‍💼' },
  { id: 24, nombre: 'Irene Cano', perfil: 'Junior', avatar: '👩‍💼' },
  { id: 25, nombre: 'Sergio Peña', perfil: 'Senior', avatar: '👨‍💼' },
  { id: 26, nombre: 'Alba Rico', perfil: 'Junior', avatar: '👩‍💼' },
  { id: 27, nombre: 'Javier Soto', perfil: 'Senior', avatar: '👨‍💼' },
  { id: 28, nombre: 'Clara Méndez', perfil: 'Junior', avatar: '👩‍💼' },
  { id: 29, nombre: 'Óscar Nieves', perfil: 'Senior', avatar: '👨‍💼' },
  { id: 30, nombre: 'Rebeca Lago', perfil: 'Junior', avatar: '👩‍💼' }
];

@Injectable({
  providedIn: 'root'
})
export class SchedulingFacadeService {
  readonly agents = signal(MOCK_AGENTS);
  readonly schedule = signal<Schedule>({ agents: [], days: [], kpis: { totalCoverage: 0, avgHours: 0 } });
  readonly loading = signal(false);

  readonly coverageRate = computed(() => this.schedule().kpis.totalCoverage);

  loadMockSchedule(range: DateRange): void {
    this.loading.set(true);
    setTimeout(() => {
      const days = this.generateDays(range);
      this.schedule.set({
        agents: MOCK_AGENTS,
        days,
        kpis: { totalCoverage: 92 + Math.random() * 8, avgHours: 7.5 + Math.random() * 1 }
      });
      this.loading.set(false);
    }, 1500);
  }

  generateMockSchedule(): void {
    const today = new Date();
    const endDate = new Date(today.getTime() + 10 * 24 * 60 * 60 * 1000); // 10 días
    const range: DateRange = { startDate: today, endDate, numAgents: MOCK_AGENTS.length };
    this.loadMockSchedule(range);
  }

  private generateDays(range: DateRange): Schedule['days'] {
    const days: Schedule['days'] = [];
    let current = new Date(range.startDate);
    const end = new Date(range.endDate);
    const shiftTipos: Shift['tipo'][] = ['LIBRE', 'VAC', 'BMED', '08:00-17:00', '16:00-00:00', '00:00-08:00'];
    const typeColors: Record<Shift['tipo'], string> = {
      'LIBRE': '#6c757d',
      'VAC': '#ffc107',
      'BMED': '#17a2b8',
      '08:00-17:00': '#28a745',
      '16:00-00:00': '#fd7e14',
      '00:00-08:00': '#dc3545'
    };

    while (current <= end) {
      const fecha = current.toISOString().split('T')[0];
      const agentShifts: Record<number, Shift> = {};
      MOCK_AGENTS.forEach((agent) => {
        const tipo = shiftTipos[Math.floor(Math.random() * shiftTipos.length)];
        const breaks: Break[] = tipo === 'LIBRE' || tipo === 'VAC' ? [] : [
          { start: '12:00', duration: 30 + Math.floor(Math.random() * 30) }
        ];
        agentShifts[agent.id] = {
          agentId: agent.id,
          fecha,
          tipo,
          typeColor: typeColors[tipo],
          breaks,
          inicio: tipo === 'LIBRE' ? '' : tipo.split('-')[0],
          fin: tipo === 'LIBRE' ? '' : tipo.split('-')[1]
        };
      });
      days.push({ fecha, agentShifts });
      current.setDate(current.getDate() + 1);
    }
    return days;
  }
}