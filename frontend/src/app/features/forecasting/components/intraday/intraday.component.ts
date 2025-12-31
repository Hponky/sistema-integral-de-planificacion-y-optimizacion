import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ForecastingService } from '../../forecasting.service';
import { ToastService } from '../../../../shared/services/toast.service';
import { ModalComponent } from '../../../../shared/components/modal/modal.component';
import { Chart, registerables } from 'chart.js';
Chart.register(...registerables);

interface Segment {
    id: number;
    name: string;
    campaign_name?: string;
    campaignName?: string;
}

@Component({
    selector: 'app-forecasting-intraday',
    standalone: true,
    imports: [CommonModule, FormsModule, DecimalPipe, ModalComponent],
    templateUrl: './intraday.component.html',
    styleUrls: ['../../forecasting.css']
})
export class IntradayComponent implements OnInit, OnDestroy {
    loading: boolean = false;
    error: string | null = null;
    successMessage: string | null = null;

    // Chart
    chart: any;
    miniCharts: any[] = [];
    selectedDayIndex: number = 0;

    // Files
    files: any = {
        intraday: null,
        intraday_holidays: null,
        expected_calls: null
    };

    // Selection Control
    viewSelection: 'weekday' | 'holiday' | 'date' = 'weekday';
    selectedHolidayName: string = '';
    selectedSpecificDate: string = '';
    dateResult: any = null;

    // Models
    intradayWeeks: number = 4;
    intradayResult: any = null;
    holidayResult: any = null;
    selectedSegmentId: number | null = null;
    curveName: string = '';
    savedCurves: any[] = [];
    savedDistributions: any[] = [];
    segments: Segment[] = [];
    groupedSegments: { [key: string]: Segment[] } = {};
    selectedService: string = '';

    // Save Selection
    saveService: string = '';
    saveSegmentId: number | null = null;

    expectedCallsVolumes: { [key: string]: number } | null = null;

    // Weight management
    private previousWeights: Map<string, number> = new Map();
    weightError: string | null = null;
    private analysisCount = 0;

    // Delete confirmation modal
    showDeleteModal: boolean = false;
    itemToDelete: { id: number, type: 'curve' | 'distribution', name?: string } | null = null;

    constructor(
        private forecastingService: ForecastingService,
        private toastService: ToastService
    ) { }

    ngOnInit() {
        this.loadSegments();
        this.loadSavedCurves();
    }

    ngOnDestroy() {
        if (this.chart) this.chart.destroy();
        this.miniCharts.forEach(chart => chart?.destroy());
    }

    loadSegments() {
        this.forecastingService.getSegments().subscribe({
            next: (data) => {
                this.segments = data;
                this.groupSegments(data);
            },
            error: (err) => console.error('Error loading segments', err)
        });
    }

    groupSegments(segments: Segment[]) {
        this.groupedSegments = {};
        segments.forEach(segment => {
            const service = segment.campaign_name || segment.campaignName || 'General';
            if (!this.groupedSegments[service]) {
                this.groupedSegments[service] = [];
            }
            this.groupedSegments[service].push(segment);
        });
    }

    onServiceChange() {
        this.selectedSegmentId = null;
        this.savedCurves = [];
        this.savedDistributions = [];
    }

    onSegmentChange() {
        this.loadSavedCurves();
        this.loadSavedDistributions();
    }

    onSaveServiceChange() {
        this.saveSegmentId = null;
    }

    isCurveLinked(curveId: number): boolean {
        return this.savedDistributions.some(d => d.curve_id === curveId);
    }

    hasOrphanCurves(): boolean {
        return this.savedCurves.some(c => !this.isCurveLinked(c.id));
    }

    onFileSelected(event: any, key: string) {
        if (event.target.files && event.target.files.length > 0) {
            this.files[key] = event.target.files[0];
        }
    }

    getDayName(dayIndex: number): string {
        const days = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];
        return days[dayIndex] || '';
    }

    onDayChange() {
        if (this.viewSelection === 'weekday' && this.intradayResult) {
            this.updateChart();
        } else if (this.viewSelection === 'holiday' && this.holidayResult) {
            this.updateChart();
        } else if (this.viewSelection === 'date' && this.dateResult) {
            this.updateChart();
        }
    }

    setViewSelection(view: 'weekday' | 'holiday' | 'date') {
        this.viewSelection = view;
        if (view === 'date' && !this.dateResult && this.selectedSpecificDate) {
            this.analyzeSpecificDateForIntraday();
        } else {
            this.updateChart();
        }
    }

    analyzeIntraday() {
        if (!this.files.intraday) {
            this.error = 'Por favor selecciona un archivo histórico.';
            return;
        }
        this.loading = true;
        this.error = null;

        if (this.files.intraday_holidays) {
            this.forecastingService.analyzeHolidays(this.files.intraday, this.files.intraday_holidays).subscribe({
                next: (res) => {
                    this.holidayResult = res;
                    this.checkAnalysisComplete(true);
                },
                error: (err) => {
                    this.error = 'Error al analizar festivos: ' + (err.error?.error || err.message);
                    this.checkAnalysisComplete(true);
                }
            });
        }

        if (this.files.expected_calls) {
            this.forecastingService.parseExpectedCalls(this.files.expected_calls).subscribe({
                next: (res) => {
                    this.expectedCallsVolumes = res;
                    this.checkAnalysisComplete(true);
                },
                error: (err) => {
                    this.error = 'Error al procesar llamadas esperadas: ' + (err.error?.error || err.message);
                    this.checkAnalysisComplete(true);
                }
            });
        }

        this.forecastingService.analyzeIntraday(this.files.intraday, this.intradayWeeks).subscribe({
            next: (res) => {
                this.intradayResult = res;
                this.checkAnalysisComplete(false);
            },
            error: (err) => {
                this.error = err.error?.error || 'Error al analizar archivo intradía.';
                this.loading = false;
            }
        });
    }

    private checkAnalysisComplete(isExtra: boolean) {
        const expectedCount = 1 + (this.files.intraday_holidays ? 1 : 0) + (this.files.expected_calls ? 1 : 0);

        if (expectedCount === 1) {
            this.loading = false;
            this.selectedDayIndex = 0;
            this.viewSelection = 'weekday';
            setTimeout(() => this.updateChart(), 100);
            return;
        }

        this.analysisCount++;
        if (this.analysisCount >= expectedCount) {
            this.loading = false;
            this.analysisCount = 0;
            this.selectedDayIndex = 0;
            this.viewSelection = 'weekday';
            if (this.holidayResult && Object.keys(this.holidayResult.holiday_data).length > 0) {
                this.selectedHolidayName = Object.keys(this.holidayResult.holiday_data)[0];
            }
            setTimeout(() => this.updateChart(), 100);
        }
    }

    analyzeSpecificDateForIntraday() {
        if (!this.files.intraday || !this.selectedSpecificDate) {
            this.error = 'Selecciona archivo histórico y una fecha.';
            return;
        }
        this.loading = true;
        this.forecastingService.analyzeDate(this.files.intraday, this.selectedSpecificDate).subscribe({
            next: (res) => {
                const weightPerInstance = 100 / res.historical_data.length;
                res.historical_data.forEach((d: any) => d.proposed_weight = Math.round(weightPerInstance));
                this.dateResult = res;
                this.loading = false;
                this.viewSelection = 'date';
                setTimeout(() => this.updateChart(), 100);
            },
            error: (err) => {
                this.error = 'Error al analizar fecha específica: ' + (err.error?.error || err.message);
                this.loading = false;
            }
        });
    }

    updateChart() {
        let weeksData: any[] = [];
        let labels: string[] = [];
        let title = '';

        if (this.viewSelection === 'weekday') {
            if (!this.intradayResult) return;
            weeksData = this.intradayResult.weekly_data[this.selectedDayIndex];
            labels = this.intradayResult.labels;
            title = `Curva Ponderada - ${this.getDayName(this.selectedDayIndex)}`;
        } else if (this.viewSelection === 'holiday') {
            if (!this.holidayResult || !this.selectedHolidayName) return;
            weeksData = this.holidayResult.holiday_data[this.selectedHolidayName];
            labels = this.holidayResult.labels;
            title = `Curva Ponderada - ${this.selectedHolidayName}`;
        } else {
            if (!this.dateResult) return;
            weeksData = this.dateResult.historical_data;
            labels = this.dateResult.labels;
            title = `Curva Ponderada - ${this.dateResult.target_date_display}`;
        }

        if (!weeksData || weeksData.length === 0) return;

        const datasets = [];

        weeksData.forEach((d: any, index: number) => {
            if (d.is_outlier) return;

            const dataPoints = labels.map((l: string) => (d.intraday_dist[l] || 0) * 100);

            datasets.push({
                label: this.viewSelection === 'weekday' ? `Semana ${d.week}` : `${d.date}`,
                data: dataPoints,
                borderColor: 'rgba(200, 200, 200, 0.5)',
                borderWidth: 1,
                pointRadius: 0,
                tension: 0.4,
                fill: false
            });
        });

        const totalWeight = weeksData.reduce((sum: number, d: any) => sum + (d.proposed_weight || 0), 0);

        const avgData = labels.map((l: string) => {
            if (totalWeight === 0) return 0;

            const weightedSum = weeksData.reduce((sum: number, d: any) => {
                const weight = (d.proposed_weight || 0) / 100;
                const value = (d.intraday_dist[l] || 0) * 100;
                return sum + (value * weight);
            }, 0);

            return weightedSum;
        });

        datasets.push({
            label: 'Curva Ponderada',
            data: avgData,
            borderColor: '#6366f1',
            borderWidth: 3,
            pointRadius: 0,
            tension: 0.4,
            fill: true,
            backgroundColor: 'rgba(99, 102, 241, 0.1)'
        });

        const ctx = document.getElementById('intradayChart') as HTMLCanvasElement;
        if (this.chart) this.chart.destroy();

        if (ctx) {
            this.chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: datasets
                },
                options: {
                    responsive: true,
                    interaction: {
                        mode: 'index',
                        intersect: false,
                    },
                    plugins: {
                        title: {
                            display: true,
                            text: title,
                            font: { size: 16, weight: 'bold' }
                        },
                        tooltip: {
                            callbacks: {
                                label: function (context: any) {
                                    return context.dataset.label + ': ' + context.parsed.y.toFixed(2) + '%';
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            title: {
                                display: true,
                                text: 'Distribución (%)'
                            },
                            beginAtZero: true
                        }
                    }
                }
            });
        }

        setTimeout(() => this.renderMiniCharts(weeksData, labels), 100);
    }

    renderMiniCharts(weeksData: any[], labels: string[]) {
        this.miniCharts.forEach(chart => chart?.destroy());
        this.miniCharts = [];

        weeksData.forEach((weekData: any, index: number) => {
            const canvasId = `weekChart_${index}`;
            const ctx = document.getElementById(canvasId) as HTMLCanvasElement;
            if (!ctx) return;

            const dataPoints = labels.map((l: string) => (weekData.intraday_dist[l] || 0) * 100);
            const color = weekData.is_outlier ? 'rgba(239, 68, 68, 0.6)' : 'rgba(99, 102, 241, 0.8)';
            const bgColor = weekData.is_outlier ? 'rgba(239, 68, 68, 0.1)' : 'rgba(99, 102, 241, 0.15)';

            const miniChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels,
                    datasets: [{
                        data: dataPoints,
                        borderColor: color,
                        backgroundColor: bgColor,
                        borderWidth: 2,
                        pointRadius: 0,
                        tension: 0.4,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            enabled: true,
                            callbacks: {
                                label: function (context: any) {
                                    return context.parsed.y.toFixed(2) + '%';
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            display: true,
                            beginAtZero: true,
                            ticks: {
                                font: { size: 9 },
                                callback: function (value: any) {
                                    return value + '%';
                                }
                            },
                            grid: {
                                color: 'rgba(147, 51, 234, 0.1)'
                            }
                        },
                        x: {
                            display: true,
                            ticks: {
                                font: { size: 7 },
                                maxRotation: 90,
                                minRotation: 90
                            },
                            grid: {
                                display: false
                            }
                        }
                    }
                }
            });

            this.miniCharts.push(miniChart);
        });
    }

    onWeightChange(weekData?: any, inputEvent?: Event) {
        let weeksData: any[] = [];
        let labels: string[] = [];

        if (this.viewSelection === 'weekday') {
            if (!this.intradayResult) return;
            weeksData = this.intradayResult.weekly_data[this.selectedDayIndex];
            labels = this.intradayResult.labels;
        } else if (this.viewSelection === 'holiday') {
            if (!this.holidayResult) return;
            weeksData = this.holidayResult.holiday_data[this.selectedHolidayName];
            labels = this.holidayResult.labels;
        } else {
            if (!this.dateResult) return;
            weeksData = this.dateResult.historical_data;
            labels = this.dateResult.labels;
        }

        if (weeksData) {
            const totalWeight = weeksData.reduce((sum: number, d: any) => sum + (d.proposed_weight || 0), 0);

            if (totalWeight !== 100) {
                this.weightError = `El peso total debe ser exactamente 100% (Actual: ${totalWeight}%)`;
            } else {
                this.weightError = null;
            }

            if (weekData) {
                this.previousWeights.set(weekData.week, weekData.proposed_weight || 0);
            }

            const currentTotalWeight = weeksData.reduce((sum: number, d: any) => sum + (d.proposed_weight || 0), 0);
            const avgData = labels.map((l: string) => {
                if (currentTotalWeight === 0) return 0;

                const weightedSum = weeksData.reduce((sum: number, d: any) => {
                    const weight = (d.proposed_weight || 0) / 100;
                    const value = (d.intraday_dist[l] || 0) * 100;
                    return sum + (value * weight);
                }, 0);

                return weightedSum;
            });

            if (this.chart && this.chart.data.datasets) {
                const avgDataset = this.chart.data.datasets.find((ds: any) => ds.label === 'Curva Ponderada');
                if (avgDataset) {
                    avgDataset.data = avgData;
                    this.chart.update();
                }
            }
        }
    }

    getTotalWeight(): number {
        let weeksData: any[] = [];
        if (this.viewSelection === 'weekday' && this.intradayResult) {
            weeksData = this.intradayResult.weekly_data[this.selectedDayIndex] || [];
        } else if (this.viewSelection === 'holiday' && this.holidayResult) {
            weeksData = this.holidayResult.holiday_data[this.selectedHolidayName] || [];
        } else if (this.dateResult) {
            weeksData = this.dateResult.historical_data || [];
        }
        return weeksData.reduce((sum: number, d: any) => sum + (d.proposed_weight || 0), 0);
    }

    getDistributionData() {
        if (this.viewSelection === 'weekday' && !this.intradayResult) return null;
        if (this.viewSelection === 'holiday' && !this.holidayResult) return null;
        if (this.viewSelection === 'date' && !this.dateResult) return null;

        const allRows: any[] = [];
        const labels = this.viewSelection === 'weekday' ? this.intradayResult.labels :
            (this.viewSelection === 'holiday' ? this.holidayResult.labels : this.dateResult.labels);

        const dayMap: { [key: number]: string } = { 0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves', 4: 'Viernes', 5: 'Sábado', 6: 'Domingo' };

        const processGroup = (instances: any[], name: string, type: string) => {
            if (!instances || instances.length === 0) return;

            const totalWeight = instances.reduce((sum: number, d: any) => sum + (d.proposed_weight || 0), 0);
            if (totalWeight === 0) return;

            const curve: any = {};
            labels.forEach((label: string) => {
                let weightedSum = 0;
                instances.forEach((d: any) => {
                    const weight = (d.proposed_weight || 0) / totalWeight;
                    weightedSum += (d.intraday_dist[label] || 0) * weight;
                });
                curve[label] = weightedSum;
            });

            const generateRow = (dateStr: string, volumeToDistribute: number, dayName: string, week: string | number, rowType: string) => {
                const newRow: any = {
                    'Fecha': dateStr,
                    'Dia': dayName,
                    'Semana': week,
                    'Tipo': rowType
                };

                let sumDist = 0;
                let maxT = labels[0];
                let maxV = -1;

                labels.forEach((t: string) => {
                    const pct = curve[t] || 0;
                    if (pct > maxV) { maxV = pct; maxT = t; }

                    const val = Math.round(volumeToDistribute * pct);
                    newRow[t] = val;
                    sumDist += val;
                });

                const diff = Math.round(volumeToDistribute) - sumDist;
                if (diff !== 0) {
                    newRow[maxT] += diff;
                }

                allRows.push(newRow);
            };

            if (this.expectedCallsVolumes) {
                Object.keys(this.expectedCallsVolumes).forEach((dateKey) => {
                    const dateObj = new Date(dateKey + 'T00:00:00');
                    const wDay = (dateObj.getDay() + 6) % 7;
                    const wDayName = dayMap[wDay];

                    let belongs = false;
                    if (this.viewSelection === 'weekday') {
                        belongs = (wDayName === name);
                    } else if (this.viewSelection === 'holiday') {
                        belongs = instances.some(inst => {
                            let instIso = inst.date;
                            if (inst.date.includes('/')) {
                                const [d, m, y] = inst.date.split('/');
                                instIso = `${y}-${m.padStart(2, '0')}-${d.padStart(2, '0')}`;
                            }
                            return instIso === dateKey;
                        });
                    } else if (this.viewSelection === 'date') {
                        let targetIso = this.dateResult?.target_date;
                        belongs = (dateKey === targetIso);
                    }

                    if (belongs) {
                        const [y, m, d] = dateKey.split('-');
                        const dStr = `${d}/${m}/${y}`;
                        generateRow(dStr, this.expectedCallsVolumes![dateKey], wDayName, this.getWeekNumber(dateObj), type);
                    }
                });
            } else {
                instances.forEach((instance: any) => {
                    generateRow(instance.date, instance.total_calls, instance.day_name || name, instance.week || '-', type);
                });
            }
        };

        if (this.viewSelection === 'weekday') {
            for (let i = 0; i < 7; i++) {
                processGroup(this.intradayResult.weekly_data[i], dayMap[i], 'N');
            }
        } else if (this.viewSelection === 'holiday') {
            processGroup(this.holidayResult.holiday_data[this.selectedHolidayName], this.selectedHolidayName, 'F');
        } else if (this.viewSelection === 'date') {
            processGroup(this.dateResult.historical_data, `Especial_${this.dateResult.target_date_display}`, 'E');
        }

        if (allRows.length === 0) return null;

        allRows.sort((a, b) => {
            const parseDate = (d: string) => {
                if (d.includes('/')) {
                    const [day, month, year] = d.split('/');
                    return new Date(+year, +month - 1, +day).getTime();
                }
                return new Date(d).getTime();
            };
            return parseDate(a['Fecha']) - parseDate(b['Fecha']);
        });

        return { rows: allRows, labels };
    }

    exportCurvesToExcel() {
        const data = this.getDistributionData();
        if (!data) {
            this.error = 'No hay datos para exportar con la configuración actual.';
            return;
        }

        this.loading = true;
        this.error = null;

        let filename = 'distribucion_pronostico.xlsx';
        if (this.viewSelection === 'weekday') {
            filename = 'distribucion_semanal.xlsx';
        } else if (this.viewSelection === 'holiday') {
            filename = `distribucion_${this.selectedHolidayName.replace(/\s+/g, '_')}.xlsx`;
        } else if (this.viewSelection === 'date') {
            filename = `distribucion_fecha_${this.dateResult.target_date_display.replace(/\//g, '-')}.xlsx`;
        }

        const payload = {
            rows: data.rows,
            time_labels: data.labels
        };

        this.forecastingService.exportDistribution(payload).subscribe({
            next: (blob) => {
                this.downloadFile(blob, filename);
                this.loading = false;
            },
            error: (err) => {
                this.error = 'Error exportando distribución: ' + err.message;
                this.loading = false;
            }
        });
    }

    saveAllCurvesToDatabase() {
        if (!this.intradayResult || !this.saveSegmentId) {
            this.error = 'Debes analizar los datos y seleccionar un segmento de destino primero.';
            return;
        }

        if (!this.curveName || this.curveName.trim() === '') {
            this.error = 'Por favor ingresa un nombre para las curvas.';
            return;
        }

        this.loading = true;
        this.error = null;

        const curvesByDay: any = {};
        const dateRange = this.intradayResult.weekly_data[0]?.[0]?.date || '';

        for (let dayIndex = 0; dayIndex < 7; dayIndex++) {
            const dayData = this.intradayResult.weekly_data[dayIndex];
            if (!dayData || dayData.length === 0) continue;

            const weights: any = {};
            dayData.forEach((d: any) => {
                weights[d.week] = d.proposed_weight;
            });

            const totalWeight = Object.values(weights).reduce((sum: number, w: any) => sum + (w as number), 0);
            if (totalWeight === 0) continue;

            const labels = this.intradayResult.labels;
            const weightedDist: any = {};

            labels.forEach((label: string) => {
                let weightedSum = 0;
                dayData.forEach((d: any) => {
                    const weight = (weights[d.week] || 0) / 100;
                    const value = (d.intraday_dist[label] || 0);
                    weightedSum += value * weight;
                });
                weightedDist[label] = weightedSum;
            });

            curvesByDay[dayIndex] = weightedDist;
        }

        const payload = {
            segment_id: this.saveSegmentId,
            name: this.curveName,
            curves_by_day: curvesByDay,
            time_labels: this.intradayResult.labels,
            weeks_analyzed: this.intradayWeeks,
            date_range: dateRange
        };

        // First save the curves (percentages)
        this.forecastingService.saveCurves(payload).subscribe({
            next: (res) => {
                // If curves saved successfully, generate and save the distribution volumes
                const distData = this.getDistributionData();
                if (distData) {
                    const distPayload = {
                        segment_id: this.saveSegmentId,
                        rows: distData.rows,
                        time_labels: distData.labels,
                        curve_id: res.curve_id // Pass the linked curve ID
                    };

                    this.forecastingService.saveDistribution(distPayload).subscribe({
                        next: () => {
                            this.loading = false;
                            this.successMessage = `Curvas y distribuciones guardadas exitosamente.`;
                            this.loadSavedCurves();
                            this.loadSavedDistributions();
                        },
                        error: (distErr) => {
                            console.error('Error saving distributions:', distErr);
                            this.loading = false;
                            this.successMessage = `Curvas guardadas, pero hubo un error al guardar las distribuciones.`;
                            this.loadSavedCurves();
                        }
                    });
                } else {
                    this.loading = false;
                    this.successMessage = `Curvas guardadas exitosamente.`;
                    this.loadSavedCurves();
                }
            },
            error: (err) => {
                this.loading = false;
                this.error = err.error?.error || 'Error al guardar las curvas.';
            }
        });
    }

    loadSavedCurves() {
        if (!this.selectedSegmentId) return;

        this.forecastingService.getCurvesBySegment(this.selectedSegmentId).subscribe({
            next: (res) => {
                this.savedCurves = res.curves || [];
            },
            error: (err) => {
                console.error('Error cargando curvas guardadas:', err);
            }
        });
    }

    loadSavedDistributions() {
        if (!this.selectedSegmentId) return;
        this.forecastingService.getDistributions(this.selectedSegmentId).subscribe({
            next: (data) => this.savedDistributions = data || [],
            error: (err) => this.toastService.showError('Error cargando distribuciones', 'Error')
        });
    }

    // Delete confirmation modal methods
    openDeleteModal(id: number, type: 'curve' | 'distribution', name?: string) {
        this.itemToDelete = { id, type, name };
        this.showDeleteModal = true;
    }

    closeDeleteModal() {
        this.showDeleteModal = false;
        this.itemToDelete = null;
    }

    confirmDelete() {
        if (!this.itemToDelete) return;

        const { id, type } = this.itemToDelete;
        this.loading = true;
        this.showDeleteModal = false;

        const obs = type === 'curve'
            ? this.forecastingService.deleteCurve(id)
            : this.forecastingService.deleteDistribution(id);

        obs.subscribe({
            next: () => {
                this.toastService.showSuccess(`${type === 'curve' ? 'Curva' : 'Escenario'} eliminado correctamente.`);
                this.loading = false;

                // Refresh both lists to keep UI in sync (especially for linked items)
                this.loadSavedCurves();
                this.loadSavedDistributions();

                this.itemToDelete = null;
            },
            error: (err) => {
                this.toastService.showError(`Error al eliminar ${type === 'curve' ? 'curva' : 'distribución'}: ` + (err.error?.error || err.message));
                this.loading = false;
                this.itemToDelete = null;
            }
        });
    }

    deleteCurve(id: number, name?: string) {
        this.openDeleteModal(id, 'curve', name);
    }

    deleteDistribution(id: number, name?: string) {
        this.openDeleteModal(id, 'distribution', name);
    }

    selectDistribution(id: number) {
        this.loading = true;
        this.forecastingService.selectDistribution(id).subscribe({
            next: () => {
                this.toastService.showSuccess('Estado del escenario actualizado.');
                this.loading = false;
                this.loadSavedDistributions();
            },
            error: (err) => {
                this.toastService.showError('Error al seleccionar distribución: ' + (err.error?.error || err.message));
                this.loading = false;
            }
        });
    }

    private downloadFile(blob: Blob, filename: string) {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    }

    private getWeekNumber(date: Date): number {
        const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
        const dayNum = d.getUTCDay() || 7;
        d.setUTCDate(d.getUTCDate() + 4 - dayNum);
        const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
        return Math.ceil((((d.getTime() - yearStart.getTime()) / 86400000) + 1) / 7);
    }
}
