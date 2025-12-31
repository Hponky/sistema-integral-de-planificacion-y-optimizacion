import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Segment, CalculationResult } from './calculator.interfaces';
import { environment } from '../../../environments/environment';
import { AuthService } from '../../core/services/auth.service';

@Injectable({
  providedIn: 'root'
})
export class CalculatorService {
  private readonly apiUrl = environment.apiUrl;

  constructor(
    private readonly http: HttpClient,
    private readonly authService: AuthService
  ) { }

  getSegments(): Observable<Segment[]> {
    return this.http.get<Segment[]>(`${this.apiUrl}/calculator/`);
  }

  calculateDimensioning(formData: FormData): Observable<CalculationResult> {
    // Append user information from AuthService
    const currentUser = this.authService.getCurrentUser();
    if (currentUser) {
      if (currentUser.idLegal) {
        formData.append('id_legal', currentUser.idLegal);
      }
      if (currentUser.username) {
        formData.append('username', currentUser.username);
      }
    }

    return this.http.post<CalculationResult>(`${this.apiUrl}/calculator/calculate`, formData);
  }

  getHistory(): Observable<any[]> {
    // Get id_legal from current user and pass as query parameter
    const currentUser = this.authService.getCurrentUser();

    // If no user or no idLegal, return empty array instead of error
    // This can happen if the component loads before auth state is fully initialized
    if (!currentUser?.idLegal) {
      console.warn('Usuario no tiene idLegal, retornando historial vacío');
      return new Observable(observer => {
        observer.next([]);
        observer.complete();
      });
    }

    const params = new HttpParams().set('id_legal', currentUser.idLegal);
    return this.http.get<any[]>(`${this.apiUrl}/calculator/history`, { params });
  }

  getScenarioDetails(id: number): Observable<CalculationResult> {
    return this.http.get<CalculationResult>(`${this.apiUrl}/calculator/history/${id}`);
  }

  deleteScenario(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/calculator/history/${id}`);
  }
}
