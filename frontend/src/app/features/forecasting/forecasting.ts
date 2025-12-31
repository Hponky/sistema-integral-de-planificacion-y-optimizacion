import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';

// Import modular components
import { IntradayComponent } from './components/intraday/intraday.component';
import { DateAnalysisComponent } from './components/date-analysis/date-analysis.component';
import { MonthlyForecastComponent } from './components/monthly-forecast/monthly-forecast.component';
import { DistributionComponent } from './components/distribution/distribution.component';

@Component({
    selector: 'app-forecasting',
    standalone: true,
    imports: [
        CommonModule,
        FormsModule,
        HttpClientModule,
        IntradayComponent,
        DateAnalysisComponent,
        MonthlyForecastComponent,
        DistributionComponent
    ],
    templateUrl: './forecasting.html',
    styleUrls: ['./forecasting.css']
})
export class ForecastingComponent {
    activeTab: string = 'intraday';

    setActiveTab(tab: string) {
        this.activeTab = tab;
    }
}
