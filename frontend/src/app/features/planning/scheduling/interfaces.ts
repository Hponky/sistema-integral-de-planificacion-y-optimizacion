export interface Agent {
  id: number;
  nombre: string;
  perfil: string;
  avatar: string;
}

export interface Break {
  start: string; // HH:MM
  duration: number; // minutos
}

export interface Shift {
  agentId: number;
  fecha: string;
  inicio: string;
  fin: string;
  tipo: 'LIBRE' | 'VAC' | 'BMED' | '08:00-17:00' | '16:00-00:00' | '00:00-08:00';
  typeColor: string;
  breaks: Break[];
}

export interface ScheduleDay {
  fecha: string;
  agentShifts: Partial<Record<number, Shift>>;
}

export interface Schedule {
  agents: Agent[];
  days: ScheduleDay[];
  kpis: {
    totalCoverage: number;
    avgHours: number;
  };
}

export interface ShiftTableRow {
  id: number;
  avatar: string;
  nombre: string;
  perfil: string;
  cumplimiento: number;
  shifts: (Shift | null)[];
}

export interface DateRange {
  startDate: Date;
  endDate: Date;
  numAgents: number;
}