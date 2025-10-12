import { ApplicationConfig } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';

import { routes } from './app.routes';
import { provideClientHydration } from '@angular/platform-browser';
import { ApiService } from './core/services/api.service'; // Importar ApiService
import { CalculatorService } from './features/calculator/calculator.service'; // Importar CalculatorService

export const appConfig: ApplicationConfig = {
  providers: [provideRouter(routes), provideClientHydration(), provideHttpClient(), ApiService, CalculatorService] // Proporcionar servicios
};
