
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

@Injectable({
    providedIn: 'root'
})
export class ForecastingService {
    private readonly apiUrl = environment.apiUrl + '/forecasting';

    constructor(private readonly http: HttpClient) { }

    analyzeIntraday(file: File, weeks: number): Observable<any> {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('weeks', weeks.toString());
        return this.http.post(`${this.apiUrl}/analyze-intraday`, formData);
    }

    analyzeHolidays(historicalFile: File, holidaysFile: File): Observable<any> {
        const formData = new FormData();
        formData.append('historical_file', historicalFile);
        formData.append('holidays_file', holidaysFile);
        return this.http.post(`${this.apiUrl}/analyze-holidays`, formData);
    }

    buildCurve(payload: any): Observable<any> {
        return this.http.post(`${this.apiUrl}/build-curve`, payload);
    }

    analyzeDate(file: File, targetDate: string): Observable<any> {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('target_date', targetDate);
        return this.http.post(`${this.apiUrl}/analyze-date`, formData);
    }

    analyzeDateCurve(file: File, specificDate: string): Observable<any> {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('specific_date', specificDate);
        return this.http.post(`${this.apiUrl}/analyze-date-curve`, formData);
    }

    monthlyForecast(formData: FormData): Observable<any> {
        return this.http.post(`${this.apiUrl}/monthly-forecast`, formData);
    }

    distributeIntramonth(formData: FormData): Observable<Blob> {
        return this.http.post(`${this.apiUrl}/distribute-intramonth`, formData, { responseType: 'blob' });
    }

    distributeIntraday(formData: FormData): Observable<Blob> {
        return this.http.post(`${this.apiUrl}/distribute-intraday`, formData, { responseType: 'blob' });
    }

    saveCurves(payload: any): Observable<any> {
        return this.http.post(`${this.apiUrl}/save-curves`, payload);
    }

    getCurvesBySegment(segmentId: number): Observable<any> {
        return this.http.get(`${this.apiUrl}/curves/${segmentId}`);
    }

    getCurveById(curveId: number): Observable<any> {
        return this.http.get(`${this.apiUrl}/curve/${curveId}`);
    }

    generateExpectedCalls(payload: any): Observable<any> {
        return this.http.post(`${this.apiUrl}/generate-expected-calls`, payload);
    }

    saveDistribution(payload: any): Observable<any> {
        return this.http.post(`${this.apiUrl}/save-distribution`, payload);
    }

    downloadExpectedCalls(payload: any): Observable<Blob> {
        return this.http.post(`${this.apiUrl}/download-expected-calls`, payload, { responseType: 'blob' });
    }

    getSegments(): Observable<any[]> {
        return this.http.get<any[]>(`${environment.apiUrl}/calculator/`);
    }

    exportCurvesToExcel(payload: any): Observable<Blob> {
        return this.http.post(`${this.apiUrl}/export-curves`, payload, { responseType: 'blob' });
    }

    exportDistribution(payload: any): Observable<Blob> {
        return this.http.post(`${this.apiUrl}/export-distribution`, payload, { responseType: 'blob' });
    }
    parseExpectedCalls(file: File): Observable<any> {
        const formData = new FormData();
        formData.append('file', file);
        return this.http.post(`${this.apiUrl}/parse-expected-calls`, formData);
    }

    deleteCurve(curveId: number): Observable<any> {
        return this.http.delete(`${this.apiUrl}/curves/${curveId}`);
    }

    getDistributions(segmentId: number): Observable<any[]> {
        return this.http.get<any[]>(`${this.apiUrl}/distributions/${segmentId}`);
    }

    deleteDistribution(distId: number): Observable<any> {
        return this.http.delete(`${this.apiUrl}/distributions/${distId}`);
    }

    selectDistribution(distId: number): Observable<any> {
        return this.http.post(`${this.apiUrl}/distributions/${distId}/select`, {});
    }
}
