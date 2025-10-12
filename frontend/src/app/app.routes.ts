import { Routes } from '@angular/router';
import { CalculatorComponent } from './features/calculator/calculator/calculator';

export const routes: Routes = [
  { path: '', redirectTo: '/calculator', pathMatch: 'full' },
  {
    path: 'dashboard',
    loadComponent: () => import('./features/dashboard/dashboard.component').then(m => m.DashboardComponent)
  },
  {
    path: 'planning',
    loadComponent: () => import('./features/planning/file-upload/file-upload.component').then(m => m.FileUploadComponent)
  },
  {
    path: 'calculator',
    component: CalculatorComponent
  }
];
