import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private apiUrl = '/api'; // Ajusta esto a la URL de tu backend

  constructor(private http: HttpClient) { }

  uploadFile(file: File): Observable<string> { // Ajustar el tipo de retorno a string
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post(`${this.apiUrl}/files/uploadDemand`, formData, { responseType: 'text' }); // Usar el endpoint correcto y responseType: 'text'
  }

  getHealthCheck(): Observable<{ status: string }> { // Añadir método getHealthCheck
    return this.http.get<{ status: string }>(`${this.apiUrl}/health`);
  }

  // Puedes agregar más métodos para otras llamadas a la API aquí
}