import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', redirectTo: '/dashboard', pathMatch: 'full' },
  {
    path: 'dashboard',
    loadComponent: () => import('./features/dashboard/dashboard.component').then(m => m.DashboardComponent)
  },
  {
    path: 'planning',
    loadComponent: () => import('./features/planning/file-upload/file-upload.component').then(m => m.FileUploadComponent)
  }
];
