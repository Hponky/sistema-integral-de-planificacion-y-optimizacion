import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private apiUrl = ''; // Usar rutas relativas para que el proxy funcione correctamente

  constructor(private http: HttpClient) { }

  uploadFile(file: File): Observable<string> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post(`${this.apiUrl}/api/files/uploadDemand`, formData, { responseType: 'text' });
  }

  getHealthCheck(): Observable<{ status: string }> {
    return this.http.get<{ status: string }>(`${this.apiUrl}/api/health`);
  }

  // Puedes agregar más métodos para otras llamadas a la API aquí
}