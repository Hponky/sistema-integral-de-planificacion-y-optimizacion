import { ApplicationConfig, LOCALE_ID } from '@angular/core';
import { provideRouter } from '@angular/router';
import { registerLocaleData } from '@angular/common';
import localeEs from '@angular/common/locales/es';

registerLocaleData(localeEs);
import { provideHttpClient, withInterceptors, withFetch } from '@angular/common/http';

import { routes } from './app.routes';
import { provideClientHydration } from '@angular/platform-browser';
import { ApiService } from './core/services/api.service'; // Importar ApiService
import { CalculatorService } from './features/calculator/calculator.service'; // Importar CalculatorService
import { AuthService } from './core/services/auth.service'; // Importar AuthService
import { authenticationInterceptor } from './core/interceptors/auth.interceptor'; // Importar interceptor
import { AuthErrorHandlerService } from './core/services/auth-error-handler.service'; // Importar AuthErrorHandlerService
import { ToastService } from './shared/services/toast.service'; // Importar ToastService
import { MatIconRegistry } from '@angular/material/icon';
import { provideAnimations } from '@angular/platform-browser/animations';

export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(routes),
    provideClientHydration(),
    provideHttpClient(withInterceptors([authenticationInterceptor]), withFetch()),
    provideAnimations(),
    ApiService,
    CalculatorService,
    AuthService,
    AuthErrorHandlerService,
    ToastService,
    MatIconRegistry,
    { provide: LOCALE_ID, useValue: 'es' }
  ] // Proporcionar servicios
};
