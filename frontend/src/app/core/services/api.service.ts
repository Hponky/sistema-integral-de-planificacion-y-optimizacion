import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private backendUrl = 'http://localhost:8080/api';

  constructor(private http: HttpClient) { }

  getHealthCheck(): Observable<any> {
    return this.http.get(`${this.backendUrl}/health`);
  }
}