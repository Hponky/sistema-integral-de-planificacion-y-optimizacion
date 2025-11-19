import { Component, OnInit } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { AsyncPipe } from '@angular/common';
import { ApiService } from './core/services/api.service';
import { HttpErrorResponse } from '@angular/common/http';
import { AuthService } from './core/services/auth.service';
import { AuthenticationStateService, AuthenticationState } from './core/services/authentication-state.service';
import { Observable, map } from 'rxjs';
import { NavbarComponent } from './shared/components/navbar/navbar.component';
import { ToastComponent } from './shared/components/toast/toast.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, AsyncPipe, NavbarComponent, ToastComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})
export class AppComponent implements OnInit {
  title = 'frontend';
  healthStatus: string = 'Desconocido';
  isAuthenticated$!: Observable<boolean>;

  constructor(
    public authService: AuthService,
    private apiService: ApiService,
    private authenticationStateService: AuthenticationStateService
  ) {}

  ngOnInit(): void {
    this.isAuthenticated$ = this.authenticationStateService.currentState$.pipe(
      map((state: AuthenticationState) => state === AuthenticationState.AUTHENTICATED)
    );

    this.apiService.getHealthCheck().subscribe({
      next: (response: { status: string }) => {
        this.healthStatus = response.status;
      },
      error: (error: HttpErrorResponse) => {
        console.error('Error al obtener el estado de salud:', error);
        this.healthStatus = 'Caído';
      }
    });
  }

  logout(): void {
    this.authService.logout().subscribe({
      next: () => {
        this.authenticationStateService.setState(AuthenticationState.NOT_AUTHENTICATED);
      },
      error: (error) => {
        console.error('Error durante el logout:', error);
      }
    });
  }
}
