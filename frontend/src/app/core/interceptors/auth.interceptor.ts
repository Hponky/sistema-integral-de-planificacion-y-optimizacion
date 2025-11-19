import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject, PLATFORM_ID } from '@angular/core';
import { AuthService } from '../services/auth.service';
import { AuthNavigationService } from '../services/auth-navigation.service';
import { AuthErrorHandlerService } from '../services/auth-error-handler.service';
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
  const authErrorHandlerService = inject(AuthErrorHandlerService);
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
          console.warn('Error 401 detectado en la ruta:', req.url);
          
          // Usar el servicio de manejo de errores para mostrar un toast al usuario
          authErrorHandlerService.handleError(error, req.url).subscribe({
            error: () => {
              // El error ya ha sido manejado por el servicio, no se necesita acción adicional
            }
          });
          
          // Proporcionar más contexto en el error para mejor diagnóstico
          const sessionError = new Error('Sesión expirada');
          sessionError.name = 'SessionExpiredError';
          (sessionError as any).originalError = error;
          (sessionError as any).url = req.url;
          (sessionError as any).timestamp = new Date();
          
          // Registrar el error para diagnóstico pero no propagarlo completamente
          console.warn('Sesión expirada detectada:', {
            url: req.url,
            timestamp: new Date().toISOString(),
            originalError: error.message || 'Error desconocido'
          });
          
          return throwError(() => sessionError);
        }
      }
      return throwError(() => error);
    })
  );
};