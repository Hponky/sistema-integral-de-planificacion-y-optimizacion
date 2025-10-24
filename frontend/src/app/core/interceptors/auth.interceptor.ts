import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject, PLATFORM_ID } from '@angular/core';
import { AuthService } from '../services/auth.service';
import { AuthNavigationService } from '../services/auth-navigation.service';
import { catchError, throwError } from 'rxjs';
import { isPlatformBrowser } from '@angular/common';

const API_ROUTES = ['/api/auth/login', '/api/auth/logout'];
const API_PREFIX = '/api';

function isApiRoute(url: string): boolean {
  return url.startsWith(API_PREFIX) || API_ROUTES.some(route => url.includes(route));
}

function isAuthRoute(url: string): boolean {
  return API_ROUTES.some(route => url.includes(route));
}

export const authenticationInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const authNavigationService = inject(AuthNavigationService);
  const platformId = inject(PLATFORM_ID);

  // No interceptar solicitudes de autenticación
  if (isAuthRoute(req.url)) {
    return next(req);
  }

  // Agregar headers de autenticación si el usuario está logueado
  let modifiedReq = req;
  const currentUser = authService.getCurrentUser();
  if (currentUser) {
    modifiedReq = req.clone({
      withCredentials: true // Para enviar cookies de sesión
    });
  }

  return next(modifiedReq).pipe(
    catchError((error) => {
      if (error instanceof HttpErrorResponse && error.status === 401) {
        // Solo manejar errores 401 para rutas de API
        if (isApiRoute(req.url)) {
          // Limpiar el estado local de autenticación
          authService.clearUser();
          
          // Solo redirigir si estamos en el navegador y no estamos ya en la página de login
          if (isPlatformBrowser(platformId) && !window.location.pathname.includes('/login')) {
            // Usar el servicio de navegación en lugar de window.location.href
            authNavigationService.handleAuthenticationError().subscribe({
              error: (navError) => {
                console.error('Error durante la navegación de autenticación:', navError);
                // En caso de error en la navegación, registrar el error pero no bloquear el flujo
              }
            });
          }
        }
        
        return throwError(() => new Error('Sesión expirada'));
      }
      return throwError(() => error);
    })
  );
};