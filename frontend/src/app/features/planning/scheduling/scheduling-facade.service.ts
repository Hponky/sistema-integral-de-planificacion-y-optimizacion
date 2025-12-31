
import { Injectable, signal, computed, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import type { Agent, Schedule, Shift, Activity, SchedulingRules } from './interfaces';
import { environment } from '../../../../environments/environment';
import { AuthService } from '../../../core/services/auth.service';

@Injectable({
  providedIn: 'root'
})
export class SchedulingFacadeService {
  private http = inject(HttpClient);
  private authService = inject(AuthService); // Inject Auth Service

  readonly agents = signal<Agent[]>([]);
  readonly schedule = signal<Schedule>({ agents: [], days: [], kpis: { totalCoverage: 0, avgHours: 0 } });
  readonly loading = signal(false);
  readonly downloadUrl = signal<string | null>(null);
  readonly currentScenarioId = signal<number | null>(null); // To persist context for recalculation
  readonly currentDimensioningId = signal<number | null>(null);

  private rawScheduleData: any[] = [];
  private modifiedCells = new Map<string, string>(); // Tracks "agentId-date" -> "Timestamp String"

  readonly fictitiousAgents = signal<any[]>([]);


  // Rules Configuration
  readonly rulesConfig = signal<SchedulingRules>({
    weeklyDayOff: true,
    maxSundays: 2,
    minRestHours: 12,
    nightDayAlternation: true,
    minShiftDuration: 4,
    maxShiftDuration: 9,
    enableBreaks: true,
    enablePVDs: true
  });

  readonly coverageRate = computed(() => this.schedule().kpis.totalCoverage);

  readonly metrics = signal<any>(null); // Store full metrics blob

  readonly breakPvdData = computed(() => {
    const rawData = this.rawScheduleData;
    const tableData: any[] = [];
    let totalWorkHours = 0;
    let totalBreakMinutes = 0;

    rawData.forEach((item: any, index: number) => {
      const agent = item.agent;
      const shifts = item.shifts || {};

      Object.entries(shifts).forEach(([dateStr, sData]: [string, any]) => {
        if (sData.type !== 'WORK') return;

        totalWorkHours += (sData.duration_minutes || 0) / 60;

        const row: any = {
          agentId: index + 1,
          dni: agent.dni,
          nombre: agent.name,
          fecha: dateStr,
          turno: sData.label || `${this.minToTime(sData.start_min)}-${this.minToTime(sData.end_min)}`,
          horas: ((sData.duration_minutes || 0) / 60).toFixed(2),
          inicio_descanso: '',
          fin_descanso: '',
          unique_id: `${agent.dni}-${dateStr}`
        };

        const activities = sData.activities || [];
        const breaks = activities.filter((a: any) => a.type === 'BREAK');
        const pvds = activities.filter((a: any) => a.type === 'PVD');

        if (breaks.length > 0) {
          row.inicio_descanso = breaks[0].startStr || this.minToTime(breaks[0].start);
          row.fin_descanso = breaks[0].endStr || this.minToTime(breaks[0].end);
          totalBreakMinutes += (breaks[0].duration || 0);
        }

        pvds.forEach((p: any, idx: number) => {
          if (idx < 10) {
            const start = p.startStr || this.minToTime(p.start);
            const end = p.endStr || this.minToTime(p.end || (p.start + 5));
            row[`pvd${idx + 1}`] = `${start} - ${end}`;
            totalBreakMinutes += (p.duration || 5);
          }
        });

        tableData.push(row);
      });
    });

    return {
      tableData,
      kpis: {
        totalWorkHours,
        totalBreakMinutes
      }
    };
  });

  async uploadAndGenerate(file: File | null, startDate: string, endDate?: string, absencesFile?: File | null, scenarioId?: number): Promise<void> {
    this.loading.set(true);
    try {
      const formData = new FormData();
      if (file) {
        formData.append('file', file);
      }
      if (absencesFile) {
        formData.append('absences_file', absencesFile);
      }
      formData.append('start_date', startDate);
      if (endDate) {
        formData.append('end_date', endDate);
      }
      formData.append('rules_config', JSON.stringify(this.rulesConfig()));
      if (scenarioId) {
        formData.append('scenario_id', scenarioId.toString());
        this.currentScenarioId.set(scenarioId); // Save for later recalculations
      }

      if (this.fictitiousAgents().length > 0) {
        formData.append('fictitious_agents', JSON.stringify(this.fictitiousAgents()));
      }

      // Reset modified cells on new generation
      this.modifiedCells.clear();

      const response: any = await firstValueFrom(
        this.http.post(`${environment.apiUrl}/planning/generate-schedule`, formData)
      );

      if (response.status === 'success') {
        this.processResponse(response);

        // Notificar advertencias de validación (contratos vs turnos sugeridos)
        if (response.warnings && response.warnings.length > 0) {
          const maxWarnings = 10;
          let msg = `🔍 Detección de fallas en plantilla:\n`;
          msg += `Pueden haber problemas en la plantilla de agentes adjunta. Por favor, tome precaución y revise los siguientes agentes:\n\n`;

          msg += response.warnings.slice(0, maxWarnings).join('\n');
          if (response.warnings.length > maxWarnings) {
            msg += `\n... y otros ${response.warnings.length - maxWarnings} casos similares.`;
          }

          msg += `\n\nNota: El planificador debe verificar que el turno sugerido y la ventana coincidan con las horas de contrato.`;
          alert(msg);
        }
      }
    } catch (error) {
      console.error('Error generating schedule:', error);
      // Handle error (toast/alert)
    } finally {
      this.loading.set(false);
    }
  }

  // Fallback alias for existing components calling generateMockSchedule (autostart)
  generateMockSchedule(): void {
    // No-op or load empty state. Real app usage requires file upload now.
    console.log("Mock schedule disabled. Upload a file to generate.");
  }

  private processResponse(data: any) {
    console.log('processResponse received data:', data);
    console.log('Received KPIs:', data.kpis);

    const rawSchedule = data.schedule; // List of agent schedules
    this.rawScheduleData = rawSchedule; // Save for updates

    // Store metrics
    if (data.metrics) {
      this.metrics.set(data.metrics);

      // Validation: Check if we have required agents > 0
      let totalRequired = 0;
      if (data.metrics.daily_metrics) {
        Object.values(data.metrics.daily_metrics).forEach((d: any) => {
          if (d.slots) {
            d.slots.forEach((s: any) => totalRequired += (s.required || 0));
          }
        });
      }

      if (totalRequired === 0) {
        alert("ADVERTENCIA: No se encontraron asesores necesitados (valor 0) para el rango de fechas seleccionado.\n\n" +
          "Posibles causas:\n" +
          "1. El Escenario de Dimensionamiento seleccionado no tiene datos para estas fechas.\n" +
          "2. El rango de fechas de la generación no coincide con el del dimensionamiento.\n" +
          "3. El dimensionamiento tiene valores en 0.\n\n" +
          "Por favor verifica las fechas seleccionadas.");
      }
    }

    const agents: Agent[] = [];
    const daysMap: Record<string, Record<number, Shift>> = {};
    // daysMap[date] -> { agentId: shift }

    rawSchedule.forEach((item: any, index: number) => {
      // Map Agent
      // Backend uses temp IDs, we map to int
      const agentId = index + 1;
      const agentName = item.agent.name;
      agents.push({
        id: agentId,
        nombre: agentName,
        identificacion: item.agent.dni,
        centro: item.agent.center,
        contrato: item.agent.contract_hours,
        perfil: item.agent.segment || 'Agente',
        avatar: item.agent.is_fictitious ? '🧪' : '👤',
        isFictitious: !!item.agent.is_fictitious
      });

      // Map Shifts
      const shifts = item.shifts;
      for (const [dateStr, sData] of Object.entries(shifts)) {
        const shiftData = sData as any;

        if (!daysMap[dateStr]) {
          daysMap[dateStr] = {};
        }

        let activities: Activity[] = [];
        if (shiftData.activities) {
          activities = shiftData.activities.map((act: any) => ({
            type: act.type,
            start: act.start,
            end: act.end,
            duration: act.duration,
            startStr: this.minToTime(act.start),
            endStr: this.minToTime(act.end)
          }));
        }

        // Determine shift display properties
        let tipo = 'LIBRE';
        let label = 'LIBRE';
        let typeColor = '#6c757d'; // Gray for LIBRE
        let inicio = '';
        let fin = '';

        if (shiftData.type === 'WORK') {
          tipo = shiftData.label || 'WORK';
          label = shiftData.label || `${this.minToTime(shiftData.start_min)}-${this.minToTime(shiftData.end_min)}`;
          typeColor = '#28a745'; // Green
          inicio = this.minToTime(shiftData.start_min);
          fin = this.minToTime(shiftData.end_min);
        } else if (shiftData.type === 'ABSENCE') {
          const absCode = shiftData.label || 'AUS';
          tipo = absCode;
          label = absCode;
          // Color coding for absences
          if (absCode === 'VAC') {
            typeColor = '#17a2b8'; // Cyan for vacation
          } else if (absCode === 'BMED') {
            typeColor = '#dc3545'; // Red for medical leave
          } else {
            typeColor = '#fd7e14'; // Orange for other absences
          }
        }

        const shift: Shift = {
          agentId: agentId,
          fecha: dateStr,
          inicio: inicio,
          fin: fin,
          tipo: tipo,
          label: label,
          typeColor: typeColor,
          activities: activities,
          durationMinutes: shiftData.duration_minutes || 0,
          isModified: this.modifiedCells.has(`${agentId}-${dateStr}`),
          modificationTimestamp: this.modifiedCells.get(`${agentId}-${dateStr}`),
          formatted_activities: shiftData.formatted_activities || ''
        };

        daysMap[dateStr][agentId] = shift;
      }
    });

    // Convert daysMap to array
    const days = Object.keys(daysMap).sort().map(date => ({
      fecha: date,
      agentShifts: daysMap[date]
    }));

    // Resolve download URL relative to API environment
    let url = data.download_url;
    if (url && !url.startsWith('http')) {
      // Remove leading slash from path
      const cleanPath = url.startsWith('/') ? url.substring(1) : url;

      // Determine base URL from environment.apiUrl
      // Example: '.../api' -> '.../'
      let baseUrl = environment.apiUrl;
      const apiSuffix = '/api';

      if (baseUrl.endsWith(apiSuffix)) {
        baseUrl = baseUrl.substring(0, baseUrl.length - apiSuffix.length);
      } else if (baseUrl.endsWith(apiSuffix + '/')) {
        baseUrl = baseUrl.substring(0, baseUrl.length - (apiSuffix.length + 1));
      }

      // Ensure base ends with slash
      if (!baseUrl.endsWith('/')) {
        baseUrl += '/';
      }

      url = `${baseUrl}${cleanPath}`;
    }
    this.downloadUrl.set(url);
    this.agents.set(agents);
    this.schedule.set({
      agents,
      days,
      kpis: {
        totalCoverage: data.kpis?.totalCoverage || 0,
        avgHours: data.kpis?.avgHours || 0,
        activeAgents: data.kpis?.activeAgents || 0,
        avgBmed: data.kpis?.avgBmed || 0,
        avgVac: data.kpis?.avgVac || 0,
        serviceLevel: data.kpis?.serviceLevel || 0,
        nda: data.kpis?.nda || 0,
        avgAht: data.kpis?.avgAht || 0
      }
    });
  }

  // -- History / Scenarios --

  async saveScenario(name: string, isTemporary: boolean = false, dimensioningId: number | null = null): Promise<void> {
    this.loading.set(true);
    try {
      const user = this.authService.getCurrentUser();

      const payload = {
        name,
        schedule: this.rawScheduleData,
        metrics: this.metrics(),
        dimensioning_scenario_id: dimensioningId,
        kpis: this.schedule().kpis,
        startDate: this.schedule().days.length > 0 ? this.schedule().days[0].fecha : null,
        daysCount: this.schedule().days.length,
        username: user?.username || 'Unknown',
        idLegal: user?.idLegal || null,
        isTemporary
      };

      console.log('Saving scenario payload:', payload);

      const response: any = await firstValueFrom(
        this.http.post(`${environment.apiUrl}/planning/scenarios`, payload)
      );

      // Success - component will show toast
    } catch (e) {
      console.error('Error saving scenario:', e);
      throw e; // Re-throw for component to handle
    } finally {
      this.loading.set(false);
    }
  }

  async getHistory(): Promise<any[]> {
    return await firstValueFrom(
      this.http.get<any[]>(`${environment.apiUrl}/planning/scenarios`)
    );
  }

  async loadScenario(id: number): Promise<void> {
    this.loading.set(true);
    try {
      // Reset modified cells on load
      this.modifiedCells.clear();

      const data: any = await firstValueFrom(
        this.http.get(`${environment.apiUrl}/planning/scenarios/${id}`)
      );

      this.currentDimensioningId.set(data.dimensioningScenarioId || null);
      this.currentScenarioId.set(data.dimensioningScenarioId || null);

      this.processResponse({
        schedule: data.schedule,
        metrics: data.metrics,
        kpis: data.kpis,
        download_url: ''
      });

    } catch (e) {
      console.error("Error loading scenario", e);
    } finally {
      this.loading.set(false);
    }
  }

  async deleteScenario(id: number): Promise<void> {
    await firstValueFrom(
      this.http.delete(`${environment.apiUrl}/planning/scenarios/${id}`)
    );
  }

  private minToTime(minutes: number): string {
    if (minutes === undefined) return '';
    const h = Math.floor(minutes / 60);
    const m = minutes % 60;
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`;
  }

  async downloadReport(url: string): Promise<void> {
    try {
      const data = await firstValueFrom(
        this.http.get(url, { responseType: 'blob' })
      );

      // Verificar si la respuesta es un archivo válido (no JSON error ni HTML de login)
      if (data.type.includes('application/json') || data.type.includes('text/html')) {
        const text = await data.text();
        console.error('Error en la descarga (contenido inválido):', text);

        let errorMsg = 'No se pudo descargar el reporte.';
        try {
          if (data.type.includes('application/json')) {
            const json = JSON.parse(text);
            errorMsg = json.detail || json.message || errorMsg;
          } else {
            errorMsg += ' La sesión puede haber expirado o el archivo no existe.';
          }
        } catch (e) { }

        alert(errorMsg);
        return;
      }

      const downloadUrl = window.URL.createObjectURL(data);
      const link = document.createElement('a');
      link.href = downloadUrl;
      // Intenta obtener el nombre del archivo de la URL o usa uno por defecto
      const filename = url.split('/').pop() || 'reporte_horarios.xlsx';
      link.download = filename.includes('.') ? filename : `${filename}.xlsx`;

      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
    } catch (error) {
      console.error('Error downloading report:', error);
      alert('Ocurrió un error al intentar descargar el reporte.');
    }
  }

  async exportFilteredReport(agentIds: string[]): Promise<void> {
    if (!agentIds || agentIds.length === 0) {
      alert('Por favor selecciona al menos un agente.');
      return;
    }

    this.loading.set(true);
    try {
      const payload = {
        schedule: this.rawScheduleData,
        agentIds: agentIds,
        scenarioId: this.currentScenarioId(),
        metrics: this.metrics(),
        startDate: this.schedule().days.length > 0 ? this.schedule().days[0].fecha : null
      };

      const response: any = await firstValueFrom(
        this.http.post(`${environment.apiUrl}/planning/export-excel`, payload)
      );

      if (response.status === 'success' && response.download_url) {
        // Build full URL if necessary
        let url = response.download_url;
        if (!url.startsWith('http')) {
          const apiBase = environment.apiUrl.replace(/\/api$/, '');
          url = `${apiBase}${url.startsWith('/') ? '' : '/'}${url}`;
        }
        await this.downloadReport(url);
      }
    } catch (error) {
      console.error('Error exporting filtered report:', error);
      alert('No se pudo generar el reporte filtrado.');
    } finally {
      this.loading.set(false);
    }
  }

  async setDimensioningScenario(id: number | null): Promise<void> {
    this.currentScenarioId.set(id);
    this.currentDimensioningId.set(id);

    // If there is a schedule, recalculate with the new scenario context (KPIs will change)
    if (this.rawScheduleData && this.rawScheduleData.length > 0) {
      console.log('Dimensioning changed, triggering recalculate for current schedule...');
      await this.recalculate();
    }
  }

  async recalculate(): Promise<void> {
    this.loading.set(true);
    try {
      const payload = {
        schedule: this.rawScheduleData,
        scenarioId: this.currentScenarioId(),
        startDate: this.schedule().days.length > 0 ? this.schedule().days[0].fecha : null,
        daysCount: this.schedule().days.length || 7
      };

      const response: any = await firstValueFrom(
        this.http.post(`${environment.apiUrl}/planning/recalculate`, payload)
      );

      if (response.status === 'success') {
        this.processResponse(response);
      }
    } catch (error) {
      console.error("Recalculate error:", error);
    } finally {
      this.loading.set(false);
    }
  }

  async updateSchedule(updatedAgentId: number, dateStr: string, newShift: any): Promise<void> {
    this.loading.set(true);
    try {
      // 1. Update local raw schedule
      const agentIndex = this.rawScheduleData.findIndex((a, idx) => (idx + 1) === updatedAgentId);
      if (agentIndex !== -1) {
        // Mark as modified with timestamp
        const now = new Date();
        // Format: "10:36 a.m, 17/12/2025"
        const timeStr = now.toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit', hour12: true });
        const dateStrTs = now.toLocaleDateString('es-CO');
        const timestamp = `${timeStr}, ${dateStrTs}`;

        this.modifiedCells.set(`${updatedAgentId}-${dateStr}`, timestamp);

        if (!this.rawScheduleData[agentIndex].shifts) this.rawScheduleData[agentIndex].shifts = {};

        if (newShift === null || newShift.type === 'OFF') {
          // Delete/Free - set to OFF type
          this.rawScheduleData[agentIndex].shifts[dateStr] = {
            type: 'OFF',
            label: 'LIBRE',
            duration_minutes: 0
          };
        } else if (newShift.type === 'ABSENCE') {
          // Absence - store with proper structure
          this.rawScheduleData[agentIndex].shifts[dateStr] = {
            type: 'ABSENCE',
            label: newShift.label || 'AUS',
            duration_minutes: 0
          };
        } else {
          // Work shift - convert time to minutes
          const startParts = (newShift.start_time || '08:00').split(':');
          const endParts = (newShift.end_time || '16:00').split(':');
          const startMin = parseInt(startParts[0]) * 60 + parseInt(startParts[1] || '0');
          const endMin = parseInt(endParts[0]) * 60 + parseInt(endParts[1] || '0');

          this.rawScheduleData[agentIndex].shifts[dateStr] = {
            type: 'WORK',
            label: newShift.label || `${newShift.start_time}-${newShift.end_time}`,
            start_min: startMin,
            end_min: endMin,
            duration_minutes: endMin - startMin,
            activities: []
          };
        }
      }


      // 2. Call Recalculate
      await this.recalculate();

    } catch (error) {
      console.error("Recalculate error:", error);
    } finally {
      this.loading.set(false);
    }
  }

  async updateActivities(agentId: number, dateStr: string, manualActivities: any): Promise<void> {
    this.loading.set(true);
    try {
      const agentIndex = this.rawScheduleData.findIndex((a, idx) => (idx + 1) === agentId);
      if (agentIndex !== -1) {
        const shift = this.rawScheduleData[agentIndex].shifts[dateStr];
        if (shift && shift.type === 'WORK') {
          // Format times back to minutes for start/end if needed, but the allocator uses start/end fields
          const processedActivities = manualActivities.map((act: any) => {
            const startMin = this.timeToMin(act.startStr);
            const endMin = this.timeToMin(act.endStr);
            return {
              ...act,
              start: startMin,
              end: endMin,
              duration: endMin - startMin
            };
          });

          this.rawScheduleData[agentIndex].shifts[dateStr].activities = processedActivities;
          this.rawScheduleData[agentIndex].shifts[dateStr].manual_activities = true;

          this.modifiedCells.set(`${agentId}-${dateStr}`, `Actividades modificadas: ${new Date().toLocaleTimeString()}`);
        }
      }

      await this.recalculate();
    } catch (e) {
      console.error("Error updating activities", e);
    } finally {
      this.loading.set(false);
    }
  }

  private timeToMin(timeStr: string): number {
    if (!timeStr) return 0;
    const parts = timeStr.split(':');
    return parseInt(parts[0]) * 60 + parseInt(parts[1] || '0');
  }

  generateFictitiousAgents(config: any) {
    const newAgents: any[] = [];
    const currentCount = this.fictitiousAgents().length;
    const existingIds = this.agents().map(a => a.identificacion || '').filter(id => id.startsWith('SIM-'));
    let startIdx = currentCount + 1;

    // Ensure unique IDs
    if (existingIds.length > 0) {
      const maxId = Math.max(...existingIds.map(id => parseInt(id.split('-')[1]) || 0));
      startIdx = maxId + 1;
    }

    for (let i = 0; i < config.count; i++) {
      const id = `SIM-${startIdx + i}`;
      const agent = {
        id: id,
        dni: id,
        name: `Inyectado ${startIdx + i}`,
        center: config.center,
        service: config.segment, // Mapping Segmento field
        contract_hours: config.contract,
        suggested_shift: config.suggestedShift,
        modalidad_finde: config.modalidadFinde || 'UNICO',
        rotacion_mensual_domingo: config.rotacionDominical || 'NORMAL',
        semanas_libres_finde: [],
        country: 'ES',
        max_sundays: config.rotacionDominical === 'PRIORITARIO' ? 10 : 2,
        windows: {
          0: this.parseWindow(config.windowMonday),
          1: this.parseWindow(config.windowTuesday),
          2: this.parseWindow(config.windowWednesday),
          3: this.parseWindow(config.windowThursday),
          4: this.parseWindow(config.windowFriday),
          5: this.parseWindow(config.windowSaturday),
          6: this.parseWindow(config.windowSunday)
        },
        entry_date: '1900-01-01',
        exit_date: null,
        absences: [],
        is_fictitious: true
      };
      newAgents.push(agent);
    }
    this.fictitiousAgents.update(prev => [...prev, ...newAgents]);
  }

  private parseWindow(win: string): any {
    if (!win || win === '-' || !win.includes('-')) return null;
    const parts = win.split('-');
    if (parts.length < 2) return null;
    return [[parts[0].trim(), parts[1].trim()]];
  }

  clearFictitiousAgents() {
    this.fictitiousAgents.set([]);
  }

  removeFictitiousAgent(id: string) {
    this.fictitiousAgents.update(prev => prev.filter(a => a.id !== id));
  }
}
