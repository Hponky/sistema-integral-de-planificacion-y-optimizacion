
import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ForecastingService } from '../../forecasting.service';

@Component({
    selector: 'app-forecasting-distribution',
    standalone: true,
    imports: [CommonModule, FormsModule],
    templateUrl: './distribution.component.html',
    styleUrls: ['../../forecasting.css']
})
export class DistributionComponent {
    loading: boolean = false;
    error: string | null = null;
    successMessage: string | null = null;

    monthlyVolumeJson: string = '';
    curvesJson: string = '';

    files: any = {
        dist_hist: null,
        dist_holidays: null,
        daily_vol: null
    };

    constructor(private forecastingService: ForecastingService) { }

    onFileSelected(event: any, key: string) {
        if (event.target.files && event.target.files.length > 0) {
            this.files[key] = event.target.files[0];
        }
    }

    distributeIntramonth() {
        if (!this.files.dist_hist || !this.monthlyVolumeJson) {
            this.error = 'Faltan datos para distribución intra-mes.';
            return;
        }
        this.loading = true;
        this.error = null;
        this.successMessage = null;

        const formData = new FormData();
        formData.append('historical_file', this.files.dist_hist);
        if (this.files.dist_holidays) formData.append('holidays_file', this.files.dist_holidays);
        formData.append('monthly_volume', this.monthlyVolumeJson);

        this.forecastingService.distributeIntramonth(formData).subscribe({
            next: (blob) => {
                this.downloadFile(blob, 'distribucion_diaria.xlsx');
                this.loading = false;
                this.successMessage = 'Archivo generado correctamente.';
            },
            error: (err) => {
                this.error = 'Error en distribución intra-mes.';
                this.loading = false;
            }
        });
    }

    distributeIntraday() {
        if (!this.files.daily_vol || !this.curvesJson) {
            this.error = 'Faltan datos para distribución intradía.';
            return;
        }
        this.loading = true;
        this.error = null;
        this.successMessage = null;

        const formData = new FormData();
        formData.append('forecast_file', this.files.daily_vol);
        formData.append('curves_data', this.curvesJson);

        this.forecastingService.distributeIntraday(formData).subscribe({
            next: (blob) => {
                this.downloadFile(blob, 'proyeccion_final.xlsx');
                this.loading = false;
                this.successMessage = 'Archivo final generado.';
            },
            error: (err) => {
                this.error = 'Error en distribución intradía.';
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
}
