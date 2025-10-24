import { Injectable, inject } from '@angular/core';
import { CanActivateFn, ActivatedRouteSnapshot, RouterStateSnapshot, Router } from '@angular/router';
import { Observable, map, take } from 'rxjs';
import { AuthService } from '../services/auth.service';
import { AuthNavigationService } from '../services/auth-navigation.service';
import { AuthErrorHandlerService } from '../services/auth-error-handler.service';
import { AuthenticationStateService, AuthenticationState } from '../services/authentication-state.service';

@Injectable({
  providedIn: 'root'
})
export class AuthGuardService {
  constructor(
    private readonly authService: AuthService,
    private readonly router: Router,
    private readonly authNavigationService: AuthNavigationService,
    private readonly authErrorHandlerService: AuthErrorHandlerService,
    private readonly authenticationStateService: AuthenticationStateService
  ) {}

  canActivate(
    route: ActivatedRouteSnapshot,
    state: RouterStateSnapshot
  ): Observable<boolean> | boolean {
    return this.authService.currentUser$.pipe(
      take(1),
      map(user => {
        if (user) {
          return this.validateUserRole(user, route);
        } else {
          this.checkServerSession(route, state);
          return false;
        }
      })
    );
  }

  private validateUserRole(user: any, route: ActivatedRouteSnapshot): boolean {
    const requiredRole = route.data['role'];
    if (requiredRole && user.role !== requiredRole) {
      this.router.navigate(['/calculator']);
      return false;
    }
    return true;
  }

  private checkServerSession(route: ActivatedRouteSnapshot, state: RouterStateSnapshot): void {
    const context = `AuthGuard.canActivate - Route: ${route.url.join('/')}`;
    
    this.authErrorHandlerService.handleWithRetry(
      this.authService.checkSession(),
      {
        maxRetries: 2,
        backoffDelay: 1000,
        maxBackoffDelay: 5000
      },
      context
    ).subscribe({
      next: (session) => this.handleSessionResponse(session, route, state, context),
      error: (error) => this.handleSessionError(error, context)
    });
  }

  private handleSessionResponse(
    session: any,
    route: ActivatedRouteSnapshot,
    state: RouterStateSnapshot,
    context: string
  ): void {
    if (session.authenticated && session.user) {
      this.updateLocalUserState(session.user, route, state, context);
    } else {
      this.redirectToLogin(context);
    }
  }

  private handleSessionError(error: any, context: string): void {
    this.authErrorHandlerService.handleError(error, context).subscribe({
      error: () => {
        this.redirectToLogin(context);
      }
    });
  }

  private updateLocalUserState(
    sessionUser: any,
    route: ActivatedRouteSnapshot,
    state: RouterStateSnapshot,
    context: string
  ): void {
    const user = {
      id: 0,
      username: sessionUser.username,
      role: sessionUser.role
    };

    this.authService.setUser(user as any);

    this.authNavigationService.handleSuccessfulAuthentication().subscribe({
      next: () => this.handleSuccessfulAuth(user.username),
      error: (error) => this.handlePostAuthNavigationError(error, context)
    });
  }

  private handleSuccessfulAuth(username: string): void {
    console.log(`✅ Authentication successful for user: ${username}`);
  }

  private handlePostAuthNavigationError(error: any, context: string): void {
    console.error(`❌ Error during post-authentication navigation:`, error);
    this.authErrorHandlerService.handleError(error, `${context} - post-auth navigation`).subscribe({
      error: () => {
        this.router.navigate(['/calculator']);
      }
    });
  }

  private redirectToLogin(context: string): void {
    this.authenticationStateService.setState(AuthenticationState.NOT_AUTHENTICATED).subscribe({
      next: () => this.navigateToLogin(),
      error: (stateError) => this.handleAuthenticationStateError(stateError)
    });
  }

  private navigateToLogin(): void {
    this.authNavigationService.navigateToLogin().subscribe({
      error: (navError) => this.handleNavigationError(navError)
    });
  }

  private handleAuthenticationStateError(stateError: any): void {
    console.error(`❌ Error setting authentication state:`, stateError);
    this.router.navigate(['/login']);
  }

  private handleNavigationError(navError: any): void {
    console.error(`❌ Error during navigation to login:`, navError);
    this.router.navigate(['/login']);
  }
}

const validateUserRole = (user: any, route: ActivatedRouteSnapshot, router: Router): boolean => {
  const requiredRole = route.data['role'];
  if (requiredRole && user.role !== requiredRole) {
    router.navigate(['/calculator']);
    return false;
  }
  return true;
};

const handleAuthGuardSessionResponse = (
  session: any,
  authService: AuthService,
  authNavigationService: AuthNavigationService,
  authErrorHandlerService: AuthErrorHandlerService,
  authenticationStateService: AuthenticationStateService,
  router: Router,
  context: string
): void => {
  if (session.authenticated && session.user) {
    const user = {
      id: 0,
      username: session.user.username,
      role: session.user.role
    };
    authService.setUser(user as any);
    
    authNavigationService.handleSuccessfulAuthentication().subscribe({
      next: () => {
        console.log(`✅ Authentication successful for user: ${user.username}`);
      },
      error: (error) => {
        console.error(`❌ Error during post-authentication navigation:`, error);
        authErrorHandlerService.handleError(error, `${context} - post-auth navigation`).subscribe({
          error: () => {
            router.navigate(['/calculator']);
          }
        });
      }
    });
  } else {
    redirectToLogin(authenticationStateService, authNavigationService, router);
  }
};

const handleAuthGuardSessionError = (
  error: any,
  authErrorHandlerService: AuthErrorHandlerService,
  authenticationStateService: AuthenticationStateService,
  authNavigationService: AuthNavigationService,
  router: Router,
  context: string
): void => {
  authErrorHandlerService.handleError(error, context).subscribe({
    error: () => {
      redirectToLogin(authenticationStateService, authNavigationService, router);
    }
  });
};

const redirectToLogin = (
  authenticationStateService: AuthenticationStateService,
  authNavigationService: AuthNavigationService,
  router: Router
): void => {
  authenticationStateService.setState(AuthenticationState.NOT_AUTHENTICATED).subscribe({
    next: () => {
      authNavigationService.navigateToLogin().subscribe({
        error: (navError) => {
          console.error(`❌ Error during navigation to login:`, navError);
          router.navigate(['/login']);
        }
      });
    },
    error: (stateError) => {
      console.error(`❌ Error setting authentication state:`, stateError);
      router.navigate(['/login']);
    }
  });
};

export const authGuard: CanActivateFn = (route: ActivatedRouteSnapshot, state: RouterStateSnapshot) => {
  const authService = inject(AuthService);
  const router = inject(Router);
  const authNavigationService = inject(AuthNavigationService);
  const authErrorHandlerService = inject(AuthErrorHandlerService);
  const authenticationStateService = inject(AuthenticationStateService);
  
  return authService.currentUser$.pipe(
    take(1),
    map(user => {
      if (user) {
        return validateUserRole(user, route, router);
      } else {
        const context = `authGuard - Route: ${route.url.join('/')}`;
        
        authErrorHandlerService.handleWithRetry(
          authService.checkSession(),
          {
            maxRetries: 2,
            backoffDelay: 1000,
            maxBackoffDelay: 5000
          },
          context
        ).subscribe({
          next: (session) => handleAuthGuardSessionResponse(
            session, authService, authNavigationService, authErrorHandlerService, authenticationStateService, router, context
          ),
          error: (error) => handleAuthGuardSessionError(
            error, authErrorHandlerService, authenticationStateService, authNavigationService, router, context
          )
        });
        
        return false;
      }
    })
  );
};