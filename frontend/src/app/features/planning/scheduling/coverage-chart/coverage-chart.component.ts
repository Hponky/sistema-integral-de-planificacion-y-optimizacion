
import { Component, Input, OnChanges, SimpleChanges, ElementRef, ViewChild, OnDestroy, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Chart, registerables } from 'chart.js';
Chart.register(...registerables);

@Component({
    selector: 'app-coverage-chart',
    standalone: true,
    imports: [CommonModule, FormsModule],
    templateUrl: './coverage-chart.component.html',
    styleUrls: ['./coverage-chart.component.css']
})
export class CoverageChartComponent implements OnChanges, OnDestroy {
    @Input() metrics: any = null;
    @Input() days: any[] = [];
    @Input() chartType: 'coverage' | 'breaks' = 'coverage';

    @ViewChild('chartCanvas') chartCanvas!: ElementRef<HTMLCanvasElement>;

    private chart: Chart | null = null;

    constructor(private el: ElementRef) { }

    selectedDate = signal<string>('');

    dayOptions = computed(() => {
        return this.days.map(d => d.fecha);
    });

    ngOnChanges(changes: SimpleChanges) {
        if (changes['days'] && this.days.length > 0 && !this.selectedDate()) {
            this.selectedDate.set(this.days[0].fecha);
        }

        if (changes['metrics'] || changes['days'] || changes['chartType'] || this.selectedDate()) {
            this.updateChart();
        }
    }

    ngOnDestroy() {
        if (this.chart) {
            this.chart.destroy();
        }
    }

    onDateChange(newDate: string) {
        this.selectedDate.set(newDate);
        this.updateChart();
    }

    /**
     * Recupera una variable CSS definida en el archivo .css
     */
    private getStyleVar(name: string): string {
        return getComputedStyle(this.el.nativeElement).getPropertyValue(name).trim();
    }

    private updateChart() {
        if (!this.metrics || !this.metrics.daily_metrics || !this.selectedDate()) return;

        const dayData = this.metrics.daily_metrics[this.selectedDate()];
        if (!dayData || !dayData.slots) return;

        // Detectar el intervalo nativo de los datos (48 = 30min, 288 = 5min)
        const totalSlotsCount = dayData.slots.length;
        const nativeInterval = totalSlotsCount > 0 ? Math.round(1440 / totalSlotsCount) : 30;

        let processedSlots = [...dayData.slots];

        // 1. Si es gráfica de cubrimiento y los datos vienen detallados (ej. 5 min),
        // redimensionamos a 30 min (tomando 1 de cada 6 slots)
        if (this.chartType === 'coverage' && nativeInterval < 30) {
            const step = Math.round(30 / nativeInterval);
            processedSlots = processedSlots.filter((_, idx) => idx % step === 0);
        }

        // --- FILTRADO DE SLOTS ACTIVOS ---
        // Buscamos el primer y último slot que tenga actividad en la data procesada
        let filteredSlots = processedSlots;
        let firstActiveIdx = -1;
        let lastActiveIdx = -1;

        // Helper para encontrar el último índice (polyfill manual para evitar error de versión TS)
        const findLastIndexCompat = (arr: any[], predicate: (item: any) => boolean) => {
            for (let i = arr.length - 1; i >= 0; i--) {
                if (predicate(arr[i])) return i;
            }
            return -1;
        };

        if (this.chartType === 'coverage') {
            const predicate = (s: any) => (s.required || 0) > 0 || (s.agents || 0) > 0;
            firstActiveIdx = processedSlots.findIndex(predicate);
            lastActiveIdx = findLastIndexCompat(processedSlots, predicate);
        } else {
            const predicate = (s: any) => (s.breaks || 0) > 0 || (s.pvds || 0) > 0;
            firstActiveIdx = processedSlots.findIndex(predicate);
            lastActiveIdx = findLastIndexCompat(processedSlots, predicate);
        }

        // Si hay actividad, recortamos estrictamente. Si no, mostramos todo el día vacío.
        if (firstActiveIdx !== -1 && lastActiveIdx !== -1) {
            // Recorte estricto sin márgenes (padding)
            const start = firstActiveIdx;
            const end = lastActiveIdx + 1; // slice es exclusivo en el final
            filteredSlots = processedSlots.slice(start, end);
        }

        // El intervalo final depende de si decimamos o no
        // IMPORTANTE: Para calcular la hora correcta (labels), SIEMPRE usamos el intervalo NATIVO,
        // ya que s.slot es el índice original del array de alta resolución.
        const labels = filteredSlots.map((s: any) => this.slotToTime(s.slot, nativeInterval));

        // Recuperar tokens de diseño desde CSS para mantener separación de responsabilidades total
        const tokens = {
            general: {
                lineWidth: parseInt(this.getStyleVar('--chart-line-width')),
                tension: parseFloat(this.getStyleVar('--chart-line-tension')),
                tensionSteps: parseFloat(this.getStyleVar('--chart-line-tension-steps')),
                pointRadius: parseInt(this.getStyleVar('--chart-point-radius')),
                grid: this.getStyleVar('--chart-grid-color'),
                label: this.getStyleVar('--chart-label-color')
            },
            needed: {
                border: this.getStyleVar('--chart-needed-border'),
                fill: this.getStyleVar('--chart-needed-fill'),
                fillState: this.getStyleVar('--chart-needed-fill-state') === 'true'
            },
            real: {
                border: this.getStyleVar('--chart-real-border'),
                fill: this.getStyleVar('--chart-real-fill'),
                fillState: this.getStyleVar('--chart-real-fill-state') === 'true'
            },
            breaks: {
                border: this.getStyleVar('--chart-breaks-border'),
                fill: this.getStyleVar('--chart-breaks-fill'),
                fillState: this.getStyleVar('--chart-breaks-fill-state') === 'true'
            },
            pvds: {
                border: this.getStyleVar('--chart-pvds-border'),
                fill: this.getStyleVar('--chart-pvds-fill'),
                fillState: this.getStyleVar('--chart-pvds-fill-state') === 'true'
            },
            tooltip: {
                bg: this.getStyleVar('--chart-tooltip-bg'),
                border: this.getStyleVar('--chart-tooltip-border'),
                borderWidth: parseInt(this.getStyleVar('--chart-tooltip-border-width')),
                padding: parseInt(this.getStyleVar('--chart-tooltip-padding')),
                text: this.getStyleVar('--chart-tooltip-text')
            }
        };

        let datasets: any[] = [];

        if (this.chartType === 'coverage') {
            datasets = [
                {
                    label: 'Necesitados (Plan)',
                    data: filteredSlots.map((s: any) => s.required || 0),
                    borderColor: tokens.needed.border,
                    backgroundColor: tokens.needed.fill,
                    borderWidth: tokens.general.lineWidth,
                    tension: tokens.general.tension,
                    fill: tokens.needed.fillState,
                    pointRadius: tokens.general.pointRadius,
                },
                {
                    label: 'Disponibles (Reales)',
                    data: filteredSlots.map((s: any) => s.agents),
                    borderColor: tokens.real.border,
                    backgroundColor: tokens.real.fill,
                    borderWidth: tokens.general.lineWidth,
                    tension: tokens.general.tensionSteps,
                    fill: tokens.real.fillState,
                    pointRadius: tokens.general.pointRadius,
                }
            ];
        } else {
            datasets = [
                {
                    label: 'En Descanso',
                    data: filteredSlots.map((s: any) => s.breaks || 0),
                    borderColor: tokens.breaks.border,
                    backgroundColor: tokens.breaks.fill,
                    borderWidth: tokens.general.lineWidth,
                    tension: tokens.general.tension,
                    fill: tokens.breaks.fillState,
                    pointRadius: tokens.general.pointRadius,
                },
                {
                    label: 'En PVD',
                    data: filteredSlots.map((s: any) => s.pvds || 0),
                    borderColor: tokens.pvds.border,
                    backgroundColor: tokens.pvds.fill,
                    borderWidth: tokens.general.lineWidth,
                    tension: tokens.general.tension,
                    fill: tokens.pvds.fillState,
                    pointRadius: tokens.general.pointRadius,
                }
            ];
        }

        if (!this.chartCanvas) {
            setTimeout(() => this.updateChart(), 100);
            return;
        }

        const ctx = this.chartCanvas.nativeElement.getContext('2d');
        if (!ctx) return;

        if (this.chart) {
            this.chart.destroy();
        }

        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            color: tokens.general.label,
                            usePointStyle: true,
                            padding: 20
                        }
                    },
                    tooltip: {
                        backgroundColor: tokens.tooltip.bg,
                        titleColor: tokens.tooltip.text,
                        bodyColor: tokens.tooltip.text,
                        padding: tokens.tooltip.padding,
                        borderColor: tokens.tooltip.border,
                        borderWidth: tokens.tooltip.borderWidth
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: tokens.general.label,
                            autoSkip: true,
                            maxTicksLimit: 48
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: tokens.general.grid
                        },
                        ticks: {
                            color: tokens.general.label
                        },
                        title: {
                            display: true,
                            text: 'Asesores',
                            color: tokens.general.label
                        }
                    }
                }
            }
        });
    }

    private slotToTime(slot: number, intervalMinutes: number): string {
        const totalMinutes = slot * intervalMinutes;
        const h = Math.floor(totalMinutes / 60);
        const m = totalMinutes % 60;
        return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`;
    }

}
