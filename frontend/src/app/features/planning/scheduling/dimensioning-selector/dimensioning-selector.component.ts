import { Component, OnInit, Output, EventEmitter, signal, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { CalculatorService } from '../../../calculator/calculator.service';
import { CalculationHistoryItem } from '../../../calculator/calculator.interfaces';

@Component({
    selector: 'app-dimensioning-selector',
    standalone: true,
    imports: [CommonModule],
    templateUrl: './dimensioning-selector.component.html',
    styleUrls: ['./dimensioning-selector.component.css']
})
export class DimensioningSelectorComponent implements OnInit {
    @Input() set selectedScenarioId(id: number | null) {
        this.selectedId.set(id);
        // Auto-expand if a scenario is selected (e.g. loaded from history)
        if (id) {
            this.isExpanded.set(true);
        }
    }
    @Output() onSelectDimensioning = new EventEmitter<number>();

    dimensionings = signal<CalculationHistoryItem[]>([]);
    selectedId = signal<number | null>(null);
    loading = signal(false);
    isExpanded = signal(false);
    errorMessage = signal<string | null>(null);

    constructor(private calculatorService: CalculatorService) { }

    ngOnInit(): void {
        this.loadDimensionings();
    }

    loadDimensionings(): void {
        this.loading.set(true);
        this.errorMessage.set(null);

        this.calculatorService.getHistory().subscribe({
            next: (data: CalculationHistoryItem[]) => {
                this.dimensionings.set(data);
                this.loading.set(false);
            },
            error: (err: any) => {
                console.error('Error loading dimensionings', err);
                this.errorMessage.set('Error al cargar los dimensionamientos');
                this.loading.set(false);
            }
        });
    }

    toggleExpand(): void {
        this.isExpanded.set(!this.isExpanded());
    }

    selectDimensioning(item: CalculationHistoryItem): void {
        // Toggle: si ya está seleccionado, deseleccionar
        if (this.selectedId() === item.id) {
            this.selectedId.set(null);
            this.onSelectDimensioning.emit(0); // Emit 0 or null to indicate deselection
        } else {
            this.selectedId.set(item.id);
            this.onSelectDimensioning.emit(item.id);
        }
    }

    isSelected(id: number): boolean {
        return this.selectedId() === id;
    }
}
