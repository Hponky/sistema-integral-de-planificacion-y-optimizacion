import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject, PLATFORM_ID } from '@angular/core';
import { AuthService } from '../services/auth.service';
import { AuthNavigationService } from '../services/auth-navigation.service';
import { AuthErrorHandlerService } from '../services/auth-error-handler.service';
import { catchError, throwError } from 'rxjs';
import { isPlatformBrowser } from '@angular/common';
import { Router } from '@angular/router';

const API_PREFIX = '/api';

function isApiRoute(url: string): boolean {
  // Allow relative URLs starting with /api OR absolute URLs containing /api
  return url.startsWith(API_PREFIX) || url.includes('/api/');
}

function isAuthRoute(url: string): boolean {
  // Don't intercept requests to the external auth API
  return url.includes('ApiRestAutenticacion');
}

export const authenticationInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const router = inject(Router);
  const platformId = inject(PLATFORM_ID);

  // No interceptar solicitudes de autenticación
  if (isAuthRoute(req.url)) {
    return next(req);
  }

  // Agregar headers de autenticación si el usuario está logueado
  let modifiedReq = req;
  const token = authService.getToken();

  if (token) {
    modifiedReq = req.clone({
      setHeaders: {
        Authorization: `Bearer ${token}`
      }
    });
  }

  return next(modifiedReq).pipe(
    catchError((error) => {
      if (error instanceof HttpErrorResponse && error.status === 401) {
        // Solo manejar errores 401 para rutas de API
        if (isApiRoute(req.url)) {
          console.warn('Sesión expirada o no autorizada (401). Redirigiendo al login...');

          // Cerrar sesión y redirigir
          authService.logout();

          // Obtener la URL actual para redirigir después del login
          const currentUrl = router.routerState.snapshot.url;
          router.navigate(['/login'], { queryParams: { returnUrl: currentUrl } });

          return throwError(() => new Error('Sesión expirada'));
        }
      }
      return throwError(() => error);
    })
  );
};