
export interface Agent {
  id: number;
  nombre: string;
  identificacion?: string; // New field
  centro?: string; // New field
  contrato?: number; // New field
  perfil: string;
  avatar: string;
  isFictitious?: boolean;
}

export interface Activity {
  type: string; // 'BREAK', 'PVD'
  start: number; // minutes from midnight
  end: number;
  duration: number;
  label?: string;
  startStr?: string; // HH:MM
  endStr?: string;
}

export interface Shift {
  agentId: number;
  fecha: string;
  inicio: string;
  fin: string;
  tipo: string; // e.g., 'WORK', 'OFF' or specific labels
  label: string; // "09:00-18:00"
  typeColor: string;
  activities: Activity[];
  durationMinutes: number; // New field
  isModified?: boolean; // Indicates if visually modified by user
  modificationTimestamp?: string; // e.g. "17/12/2025, 10:36 a.m."
  formatted_activities?: string; // e.g. "BREAK (14:30-14:50); PVD (10:15-10:20)"
}

export interface ScheduleDay {
  fecha: string;
  agentShifts: Record<number, Shift>;
}

export interface Schedule {
  agents: Agent[];
  days: ScheduleDay[];
  kpis: {
    totalCoverage: number;
    avgHours: number;
    activeAgents?: number;
    avgBmed?: number;
    avgVac?: number;
    serviceLevel?: number;
    nda?: number;
    avgAht?: number;
  };
}

export interface ShiftTableRow {
  id: number;
  avatar: string;
  identificacion: string; // New
  nombre: string;
  centro: string; // New
  contrato: number; // New
  perfil: string;
  cumplimiento: number;
  horasTotales: number; // New field
  contratoPeriodo: number;
  shifts: (Shift | null)[];
}

export interface DateRange {
  startDate: Date;
  endDate: Date;
  numAgents: number;
}

export interface SchedulingRules {
  // Constraints
  weeklyDayOff: boolean; // At least 1 day off (Sat or Sun)
  maxSundays: number; // Max 2 sundays/month
  minRestHours: number; // 12h between shifts
  nightDayAlternation: boolean; // Prevent Night -> Day transition

  // Shift Limits
  minShiftDuration: number; // 4h
  maxShiftDuration: number; // 9h (default base)

  // Activities
  enableBreaks: boolean;
  enablePVDs: boolean;
}

export interface FictitiousAgentConfig {
  count: number;
  center: string;
  contract: number;
  segment: string;
  suggestedShift: string;
  windowMonday: string;
  windowTuesday: string;
  windowWednesday: string;
  windowThursday: string;
  windowFriday: string;
  windowSaturday: string;
  windowSunday: string;
  modalidadFinde: string;
  rotacionDominical: string;
}