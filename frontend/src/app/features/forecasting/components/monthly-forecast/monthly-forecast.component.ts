
import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ForecastingService } from '../../forecasting.service';

@Component({
    selector: 'app-forecasting-monthly-forecast',
    standalone: true,
    imports: [CommonModule, FormsModule],
    templateUrl: './monthly-forecast.component.html',
    styleUrls: ['../../forecasting.css']
})
export class MonthlyForecastComponent {
    loading: boolean = false;
    error: string | null = null;

    recencyWeight: number = 0.5;
    monthlyResult: any = null;

    files: any = {
        monthly_hist: null,
        holidays: null
    };

    constructor(private forecastingService: ForecastingService) { }

    onFileSelected(event: any, key: string) {
        if (event.target.files && event.target.files.length > 0) {
            this.files[key] = event.target.files[0];
        }
    }

    calculateMonthlyForecast() {
        if (!this.files.monthly_hist) {
            this.error = 'Falta archivo histórico.';
            return;
        }
        this.loading = true;
        this.error = null;

        const formData = new FormData();
        formData.append('historical_file', this.files.monthly_hist);
        if (this.files.holidays) formData.append('holidays_file', this.files.holidays);
        formData.append('recency_weight', this.recencyWeight.toString());

        this.forecastingService.monthlyForecast(formData).subscribe({
            next: (res) => {
                this.monthlyResult = res;
                this.loading = false;
            },
            error: (err) => {
                this.error = err.error?.error || 'Error generating forecast.';
                this.loading = false;
            }
        });
    }

    getMonthName(monthIndexStr: string): string {
        const idx = parseInt(monthIndexStr) - 1;
        const months = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'];
        return months[idx] || monthIndexStr;
    }
}
