
import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ForecastingService } from '../../forecasting.service';

@Component({
    selector: 'app-forecasting-date-analysis',
    standalone: true,
    imports: [CommonModule, FormsModule],
    templateUrl: './date-analysis.component.html',
    styleUrls: ['../../forecasting.css']
})
export class DateAnalysisComponent {
    loading: boolean = false;
    error: string | null = null;
    successMessage: string | null = null; // Added mostly for useCurve feedback

    analysisDate: string = '';
    analysisResult: any = null;

    files: any = {
        analysis: null
    };

    constructor(private forecastingService: ForecastingService) { }

    onFileSelected(event: any, key: string) {
        if (event.target.files && event.target.files.length > 0) {
            this.files[key] = event.target.files[0];
        }
    }

    analyzeDate() {
        if (!this.files.analysis || !this.analysisDate) {
            this.error = 'Selecciona archivo y fecha.';
            return;
        }
        this.loading = true;
        this.error = null;

        this.forecastingService.analyzeDate(this.files.analysis, this.analysisDate).subscribe({
            next: (res) => {
                this.analysisResult = res;
                this.loading = false;
            },
            error: (err) => {
                this.error = err.error?.error || 'Error en análisis de fecha.';
                this.loading = false;
            }
        });
    }

    useCurve(item: any) {
        // Select this curve for distribution
        this.successMessage = `Curva del año ${item.year} seleccionada.`;
        // In a real app, this would add to a "basket" of curves.
        setTimeout(() => this.successMessage = null, 3000);
    }
}
