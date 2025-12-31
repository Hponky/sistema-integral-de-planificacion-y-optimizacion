import { Injectable, PLATFORM_ID, Inject } from '@angular/core';
import { BehaviorSubject, Observable, throwError } from 'rxjs';
import { catchError, tap } from 'rxjs/operators';
import { isPlatformBrowser } from '@angular/common';

export enum AuthenticationState {
  CHECKING = 'checking',
  AUTHENTICATED = 'authenticated',
  NOT_AUTHENTICATED = 'not-authenticated'
}

export interface AuthenticationStateError {
  timestamp: Date;
  message: string;
  previousState: AuthenticationState;
  attemptedState: AuthenticationState;
}

@Injectable({
  providedIn: 'root'
})
export class AuthenticationStateService {
  private currentStateSubject = new BehaviorSubject<AuthenticationState>(AuthenticationState.NOT_AUTHENTICATED);
  public currentState$: Observable<AuthenticationState> = this.currentStateSubject.asObservable();

  private errorSubject = new BehaviorSubject<AuthenticationStateError | null>(null);
  public error$: Observable<AuthenticationStateError | null> = this.errorSubject.asObservable();

  constructor(
    @Inject(PLATFORM_ID) private platformId: Object
  ) {
    this.initializeStateFromStorage();
  }

  setState(state: AuthenticationState): Observable<AuthenticationState> {
    return new Observable<AuthenticationState>(observer => {
      try {
        if (!this.isValidState(state)) {
          const error: AuthenticationStateError = {
            timestamp: new Date(),
            message: `Invalid authentication state: ${state}`,
            previousState: this.getCurrentState(),
            attemptedState: state
          };

          this.errorSubject.next(error);
          observer.error(error);
          return;
        }

        const previousState = this.getCurrentState();
        this.currentStateSubject.next(state);

        this.saveStateToStorage(state);

        observer.next(state);
        observer.complete();
      } catch (error) {
        const stateError: AuthenticationStateError = {
          timestamp: new Date(),
          message: `Error setting authentication state: ${error instanceof Error ? error.message : String(error)}`,
          previousState: this.getCurrentState(),
          attemptedState: state
        };

        this.errorSubject.next(stateError);
        observer.error(stateError);
      }
    }).pipe(
      tap(state => {
        console.log(`Authentication state changed from ${this.getCurrentState()} to ${state}`);
      }),
      catchError(error => {
        console.error('Authentication state error:', error);
        return throwError(() => error);
      })
    );
  }

  getCurrentState(): AuthenticationState {
    return this.currentStateSubject.value;
  }

  getCurrentError(): AuthenticationStateError | null {
    return this.errorSubject.value;
  }

  clearError(): void {
    this.errorSubject.next(null);
  }

  isChecking(): boolean {
    return this.getCurrentState() === AuthenticationState.CHECKING;
  }

  isAuthenticated(): boolean {
    return this.getCurrentState() === AuthenticationState.AUTHENTICATED;
  }

  isNotAuthenticated(): boolean {
    return this.getCurrentState() === AuthenticationState.NOT_AUTHENTICATED;
  }

  checkAuthState(): void {
    if (!isPlatformBrowser(this.platformId)) {
      return;
    }

    // Check token directly from storage to avoid circular dependency with AuthService
    const hasToken = !!localStorage.getItem('token');

    if (hasToken) {
      if (this.getCurrentState() !== AuthenticationState.AUTHENTICATED) {
        this.setState(AuthenticationState.AUTHENTICATED).subscribe();
      }
    } else {
      if (this.getCurrentState() !== AuthenticationState.NOT_AUTHENTICATED) {
        this.setState(AuthenticationState.NOT_AUTHENTICATED).subscribe();
      }
    }
  }

  private isValidState(state: AuthenticationState): boolean {
    return Object.values(AuthenticationState).includes(state);
  }

  private initializeStateFromStorage(): void {
    if (!isPlatformBrowser(this.platformId)) {
      return;
    }

    // Priority: Check actual token existence first
    const hasToken = !!localStorage.getItem('token');

    if (hasToken) {
      this.currentStateSubject.next(AuthenticationState.AUTHENTICATED);
    } else {
      this.currentStateSubject.next(AuthenticationState.NOT_AUTHENTICATED);
    }
  }

  private saveStateToStorage(state: AuthenticationState): void {
    if (!isPlatformBrowser(this.platformId)) {
      return;
    }

    try {
      localStorage.setItem('auth_state', state);
    } catch (error) {
      console.error('Error saving auth state to storage:', error);
    }
  }
}