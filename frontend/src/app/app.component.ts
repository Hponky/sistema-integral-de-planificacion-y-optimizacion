import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { OnInit } from '@angular/core';
import { ApiService } from './core/services/api.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})
export class AppComponent implements OnInit {
  title = 'frontend';
  healthStatus: string = 'Desconocido';

  constructor(private apiService: ApiService) {}

  ngOnInit(): void {
    this.apiService.getHealthCheck().subscribe({
      next: (response) => {
        this.healthStatus = response.status;
      },
      error: (error) => {
        console.error('Error al obtener el estado de salud:', error);
        this.healthStatus = 'Caído';
      }
    });
  }
}
