import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject, PLATFORM_ID } from '@angular/core';
import { AuthService } from '../services/auth.service';
import { catchError, throwError } from 'rxjs';
import { isPlatformBrowser } from '@angular/common';

export const authenticationInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const platformId = inject(PLATFORM_ID);

  // No interceptar solicitudes de autenticación
  if (req.url.includes('/auth/login') || req.url.includes('/auth/logout')) {
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
        // En un sistema con tokens JWT, aquí se haría el refresh del token
        // Como usamos sesiones, simplemente redirigimos al login
        authService.logout().subscribe({
          next: () => {
            // El logout ya limpia el estado local
            if (isPlatformBrowser(platformId)) {
              window.location.href = '/login'; // Redirigir al login
            }
          },
          error: () => {
            // En caso de error en logout, igual redirigir
            if (isPlatformBrowser(platformId)) {
              window.location.href = '/login';
            }
          }
        });
        return throwError(() => new Error('Sesión expirada'));
      }
      return throwError(() => error);
    })
  );
};