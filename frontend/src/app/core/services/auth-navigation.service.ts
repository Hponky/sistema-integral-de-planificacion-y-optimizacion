import { Injectable } from '@angular/core';
import { Router } from '@angular/router';
import { Observable, throwError, from, BehaviorSubject, timer } from 'rxjs';
import { catchError, map, timeout, repeat, delay, takeWhile } from 'rxjs/operators';
import { AuthenticationStateService, AuthenticationState } from './authentication-state.service';

export interface NavigationError {
  timestamp: Date;
  message: string;
  targetRoute: string[];
  originalError?: any;
}

@Injectable({
  providedIn: 'root'
})
export class AuthNavigationService {
  private readonly NAVIGATION_TIMEOUT = 5000; // 5 segundos
  private errorSubject = new BehaviorSubject<NavigationError | null>(null);
  public error$ = this.errorSubject.asObservable();

  constructor(
    private router: Router,
    private authenticationStateService: AuthenticationStateService
  ) {}

  navigateToLogin(): Observable<boolean> {
    return this.navigateWithErrorHandling(['/login'], 'login');
  }

  navigateToDashboard(): Observable<boolean> {
    return this.navigateWithErrorHandling(['/calculator'], 'dashboard');
  }

  navigateToHome(): Observable<boolean> {
    return this.navigateWithErrorHandling(['/'], 'home');
  }

  handleAuthenticationError(): Observable<boolean> {
    return this.authenticationStateService.setState(AuthenticationState.NOT_AUTHENTICATED).pipe(
      map(() => true),
      catchError(() => throwError(() => new Error('Failed to set authentication state'))),
      timeout(this.NAVIGATION_TIMEOUT),
      catchError(error => {
        this.logNavigationError('authentication-error', ['/login'], error);
        return this.navigateToLogin();
      })
    );
  }

  handleSuccessfulAuthentication(): Observable<boolean> {
    return this.authenticationStateService.setState(AuthenticationState.AUTHENTICATED).pipe(
      map(() => true),
      catchError(() => throwError(() => new Error('Failed to set authentication state'))),
      timeout(this.NAVIGATION_TIMEOUT),
      catchError(error => {
        this.logNavigationError('successful-authentication', ['/calculator'], error);
        return this.navigateToDashboard();
      })
    );
  }

  handleUnauthorizedAccess(): Observable<boolean> {
    return this.authenticationStateService.setState(AuthenticationState.NOT_AUTHENTICATED).pipe(
      map(() => true),
      catchError(() => throwError(() => new Error('Failed to set authentication state'))),
      timeout(this.NAVIGATION_TIMEOUT),
      catchError(error => {
        this.logNavigationError('unauthorized-access', ['/login'], error);
        return this.navigateToLogin();
      })
    );
  }

  handleSessionExpiry(): Observable<boolean> {
    return this.authenticationStateService.setState(AuthenticationState.NOT_AUTHENTICATED).pipe(
      map(() => true),
      catchError(() => throwError(() => new Error('Failed to set authentication state'))),
      timeout(this.NAVIGATION_TIMEOUT),
      catchError(error => {
        this.logNavigationError('session-expiry', ['/login'], error);
        return this.navigateToLogin();
      })
    );
  }

  getCurrentError(): NavigationError | null {
    return this.errorSubject.value;
  }

  clearError(): void {
    this.errorSubject.next(null);
  }

  private navigateWithErrorHandling(route: string[], routeName: string): Observable<boolean> {
    let retryCount = 0;
    const maxRetries = 2;
    
    return from(this.router.navigate(route)).pipe(
      timeout(this.NAVIGATION_TIMEOUT),
      repeat({
        count: maxRetries,
        delay: (error) => {
          retryCount++;
          if (retryCount <= maxRetries) {
            return timer(retryCount * 1000);
          }
          throw error;
        }
      }),
      catchError(error => {
        this.logNavigationError(routeName, route, error);
        return throwError(() => error);
      })
    );
  }

  private logNavigationError(routeName: string, targetRoute: string[], error: any): void {
    const navigationError: NavigationError = {
      timestamp: new Date(),
      message: `Navigation error for ${routeName}: ${error instanceof Error ? error.message : String(error)}`,
      targetRoute,
      originalError: error
    };
    
    this.errorSubject.next(navigationError);
    console.error('Navigation error:', navigationError);
  }
}