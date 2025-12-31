import { Component, OnInit, Output, EventEmitter } from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { CalculatorService } from '../calculator.service';
import { CalculationHistoryItem, CalculationResult, KpiData, TableData, SortConfig } from '../calculator.interfaces';
import { ResultsTableComponent } from '../results-table/results-table.component';
import { KpiCardComponent } from '../kpi-card/kpi-card.component';

@Component({
    selector: 'app-calculation-history',
    standalone: true,
    imports: [CommonModule, DatePipe, ResultsTableComponent, KpiCardComponent],
    templateUrl: './calculation-history.component.html',
    styleUrls: ['./calculation-history.component.css']
})
export class CalculationHistoryComponent implements OnInit {
    historyItems: CalculationHistoryItem[] = [];
    loading = false;
    errorMessage: string | null = null;

    showModal = false;
    loadingDetails = false;
    selectedResult: CalculationResult | null = null;

    @Output() onViewDetails = new EventEmitter<number>(); // Mantener por compatibilidad si se usa externamente, aunque ahora abrimos modal

    constructor(private calculatorService: CalculatorService) { }

    ngOnInit(): void {
        this.loadHistory();
    }

    loadHistory(): void {
        this.loading = true;
        this.errorMessage = null;
        this.calculatorService.getHistory().subscribe({
            next: (data) => {
                this.historyItems = data;
                this.loading = false;

                // Si no hay datos y el array está vacío, podría ser por falta de idLegal
                if (data.length === 0) {
                    console.log('No se encontraron registros en el historial');
                }
            },
            error: (err) => {
                console.error('Error loading history', err);
                this.errorMessage = 'Error al cargar el historial. Por favor, intenta nuevamente.';
                this.loading = false;
            }
        });
    }

    openDetailsModal(id: number): void {
        this.showModal = true;
        this.loadingDetails = true;
        this.selectedResult = null;

        // Lock body scroll
        document.body.style.overflow = 'hidden';

        this.calculatorService.getScenarioDetails(id).subscribe({
            next: (data) => {
                this.selectedResult = data;
                this.loadingDetails = false;
            },
            error: (err) => {
                console.error('Error loading details', err);
                this.loadingDetails = false;
                alert('Error al cargar los detalles.');
                this.closeModal();
            }
        });
    }

    closeModal(): void {
        this.showModal = false;
        this.selectedResult = null;

        // Unlock body scroll
        document.body.style.overflow = '';
    }

    deleteItem(id: number): void {
        if (confirm('¿Estás seguro de que deseas eliminar este cálculo?')) {
            this.calculatorService.deleteScenario(id).subscribe({
                next: () => {
                    this.loadHistory();
                },
                error: (err) => {
                    console.error('Error deleting scenario', err);
                    alert('Error al eliminar el cálculo.');
                }
            });
        }
    }

    onTableSort(sortConfig: SortConfig): void {
        console.log('Sorting in modal:', sortConfig);
    }

    // Helpers para KPIs (copiados de CalculatorComponent para consistencia visual)
    getAbsentismoTrend(value: number | undefined): { value: number; direction: 'up' | 'down' | 'neutral' } | undefined {
        if (value === undefined) return undefined;
        if (value < 3) return { value: 5 - value, direction: 'down' };
        else if (value > 7) return { value: value - 7, direction: 'up' };
        else return { value: 0, direction: 'neutral' };
    }

    getAbsentismoColor(value: number | undefined): string {
        if (value === undefined) return 'info';
        if (value < 3) return 'success';
        if (value < 5) return 'warning';
        return 'error';
    }

    getAuxiliaresTrend(value: number | undefined): { value: number; direction: 'up' | 'down' | 'neutral' } | undefined {
        if (value === undefined) return undefined;
        if (value < 10) return { value: 10 - value, direction: 'down' };
        else if (value > 20) return { value: value - 20, direction: 'up' };
        else return { value: 0, direction: 'neutral' };
    }

    getAuxiliaresColor(value: number | undefined): string {
        if (value === undefined) return 'info';
        if (value < 10) return 'success';
        if (value < 15) return 'warning';
        return 'error';
    }

    getDesconexionesTrend(value: number | undefined): { value: number; direction: 'up' | 'down' | 'neutral' } | undefined {
        if (value === undefined) return undefined;
        if (value < 2) return { value: 2 - value, direction: 'down' };
        else if (value > 5) return { value: value - 5, direction: 'up' };
        else return { value: 0, direction: 'neutral' };
    }

    getDesconexionesColor(value: number | undefined): string {
        if (value === undefined) return 'info';
        if (value < 2) return 'success';
        if (value < 3) return 'warning';
        return 'error';
    }

    getInsightMessage(kpis: KpiData | any | undefined): string {
        if (!kpis) return 'Calcula los indicadores para recibir recomendaciones personalizadas.';

        const absentismo = kpis.absentismo_pct || 0;
        const auxiliares = kpis.auxiliares_pct || 0;
        const desconexiones = kpis.desconexiones_pct || 0;

        if (absentismo > 7) {
            return 'El absentismo es elevado. Considera implementar programas de bienestar y flexibilidad laboral.';
        } else if (auxiliares > 20) {
            return 'El porcentaje de auxiliares es alto. Revisa la distribución de cargas y considera reentrenamiento.';
        } else if (desconexiones > 5) {
            return 'Las desconexiones son frecuentes. Optimiza los procesos técnicos y mejora la infraestructura.';
        } else if (absentismo < 3 && auxiliares < 10 && desconexiones < 2) {
            return 'Excelentes indicadores. Mantén las prácticas actuales y considera compartir mejores prácticas.';
        } else {
            return 'Los indicadores están en rangos aceptables. Continúa con el monitoreo regular.';
        }
    }
}
