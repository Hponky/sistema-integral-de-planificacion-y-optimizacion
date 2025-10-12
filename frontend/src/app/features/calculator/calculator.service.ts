import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Segment, CalculationResult } from './calculator.interfaces';
import { environment } from '../../../environments/environment'; // Importar environment

@Injectable({
  providedIn: 'root'
})
export class CalculatorService {
  private readonly apiUrl = environment.apiUrl; // Usar la URL base de la API desde environment

  constructor(private readonly http: HttpClient) { }

  /**
   * Obtiene la lista de segmentos disponibles desde el backend.
   * @returns Un Observable con un array de objetos Segment.
   */
  getSegments(): Observable<Segment[]> {
    // La ruta en el backend es /calculator/segments
    return this.http.get<Segment[]>(`${this.apiUrl}/calculator/segments`);
  }

  /**
   * Envía los datos del formulario de la calculadora al backend para su procesamiento.
   * @param formData Un objeto FormData que contiene todos los parámetros y el archivo Excel.
   * @returns Un Observable con el resultado del cálculo.
   */
  calculateDimensioning(formData: FormData): Observable<CalculationResult> {
    // La ruta en el backend es /calculator/calculate
    return this.http.post<CalculationResult>(`${this.apiUrl}/calculator/calculate`, formData);
  }
}
