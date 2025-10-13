import { ApplicationConfig } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient, withInterceptors, withFetch } from '@angular/common/http';

import { routes } from './app.routes';
import { provideClientHydration } from '@angular/platform-browser';
import { ApiService } from './core/services/api.service'; // Importar ApiService
import { CalculatorService } from './features/calculator/calculator.service'; // Importar CalculatorService
import { AuthService } from './core/services/auth.service'; // Importar AuthService
import { authenticationInterceptor } from './core/interceptors/auth.interceptor'; // Importar interceptor

export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(routes),
    provideClientHydration(),
    provideHttpClient(withInterceptors([authenticationInterceptor]), withFetch()),
    ApiService,
    CalculatorService,
    AuthService
  ] // Proporcionar servicios
};
