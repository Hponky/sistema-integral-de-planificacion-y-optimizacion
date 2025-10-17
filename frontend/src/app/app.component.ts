import { Component, OnInit, Inject } from '@angular/core';
import { RouterOutlet, Router } from '@angular/router';
import { ApiService } from './core/services/api.service';
import { AuthService } from './core/services/auth.service';
import { HttpErrorResponse } from '@angular/common/http';
import { isPlatformBrowser } from '@angular/common';
import { PLATFORM_ID } from '@angular/core';

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
  isBrowser: boolean;

  constructor(
    private apiService: ApiService,
    private authService: AuthService,
    private router: Router,
    @Inject(PLATFORM_ID) platformId: Object
  ) {
    this.isBrowser = isPlatformBrowser(platformId);
  }

  ngOnInit(): void {
    // Verificar estado de salud del API
    this.apiService.getHealthCheck().subscribe({
      next: (response: { status: string }) => {
        this.healthStatus = response.status;
      },
      error: (error: HttpErrorResponse) => {
        console.error('Error al obtener el estado de salud:', error);
        this.healthStatus = 'Caído';
      }
    });

    // Solo verificar autenticación si estamos en el navegador
    if (this.isBrowser) {
      // Verificar si hay un usuario guardado y validar la sesión
      const currentUser = this.authService.getCurrentUser();
      const currentPath = window.location.pathname;
      
      if (currentUser && currentPath === '/login') {
        // Si hay un usuario guardado y estamos en la página de login, redirigir a calculator
        this.router.navigate(['/calculator']);
      } else if (!currentUser && currentPath !== '/login' && currentPath !== '/') {
        // Si no hay usuario y no estamos en login, verificar sesión en el servidor
        this.authService.checkSession().subscribe({
          next: (session) => {
            if (!session.authenticated) {
              // Si no hay sesión activa, redirigir al login
              this.router.navigate(['/login']);
            }
          },
          error: () => {
            // En caso de error, redirigir al login
            this.router.navigate(['/login']);
          }
        });
      }
    }
  }
}
