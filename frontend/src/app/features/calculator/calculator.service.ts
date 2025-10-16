import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Segment, CalculationResult } from './calculator.interfaces';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class CalculatorService {
  private readonly apiUrl = environment.apiUrl;

  constructor(private readonly http: HttpClient) { }

  getSegments(): Observable<Segment[]> {
    return this.http.get<Segment[]>(`${this.apiUrl}/calculator/`);
  }

  calculateDimensioning(formData: FormData): Observable<CalculationResult> {
    return this.http.post<CalculationResult>(`${this.apiUrl}/calculator/calculate`, formData);
  }
}
