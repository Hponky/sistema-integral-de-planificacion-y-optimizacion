import { Component, OnInit, Inject, PLATFORM_ID } from '@angular/core';
import { RouterOutlet, Router } from '@angular/router';
import { AsyncPipe, isPlatformBrowser } from '@angular/common';
import { ApiService } from './core/services/api.service';
import { HttpErrorResponse } from '@angular/common/http';
import { AuthService } from './core/services/auth.service';
import { AuthenticationStateService, AuthenticationState } from './core/services/authentication-state.service';
import { Observable, map } from 'rxjs';
import { NavbarComponent } from './shared/components/navbar/navbar.component';
import { ToastComponent } from './shared/components/toast/toast.component';
import { SessionInactivityService } from './core/services/session-inactivity.service';

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
    private authenticationStateService: AuthenticationStateService,
    private router: Router,
    private inactivityService: SessionInactivityService,
    @Inject(PLATFORM_ID) private platformId: Object
  ) { }

  ngOnInit(): void {
    this.isAuthenticated$ = this.authenticationStateService.currentState$.pipe(
      map((state: AuthenticationState) => state === AuthenticationState.AUTHENTICATED)
    );

    if (isPlatformBrowser(this.platformId)) {
      this.apiService.getHealthCheck().subscribe({
        next: (response: { status: string }) => {
          this.healthStatus = response.status;
        },
        error: (error: HttpErrorResponse) => {
          console.error('Error al obtener el estado de salud:', error);
          this.healthStatus = 'Caído';
        }
      });
      this.inactivityService.startTracking();
    }
  }

  logout(): void {
    const currentUrl = this.router.url;
    this.authService.logout();
    this.authenticationStateService.setState(AuthenticationState.NOT_AUTHENTICATED);
    this.router.navigate(['/login'], { queryParams: { returnUrl: currentUrl } });
  }

  isLoginPage(): boolean {
    return this.router.url.startsWith('/login');
  }
}
