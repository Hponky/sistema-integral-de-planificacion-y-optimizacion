import { Routes } from '@angular/router';
import { CalculatorComponent } from './features/calculator/calculator/calculator';
import { authGuard } from './core/guards/auth.guard';
import { LoginComponent } from './features/auth/login/login.component';

export const routes: Routes = [
  { path: '', redirectTo: '/landing', pathMatch: 'full' },
  {
    path: 'landing',
    loadComponent: () => import('./features/landing/landing.component').then(m => m.LandingComponent),
    title: 'Landing Page'
  },
  { path: 'login', component: LoginComponent },
  {
    path: 'dashboard',
    loadComponent: () => import('./features/dashboard/dashboard.component').then(m => m.DashboardComponent),
    canActivate: [authGuard]
  },
  {
    path: 'planning',
    loadComponent: () => import('./features/planning/file-upload/file-upload.component').then(m => m.FileUploadComponent),
    canActivate: [authGuard]
  },
  {
    path: 'calculator',
    component: CalculatorComponent,
    canActivate: [authGuard]
  },
  { path: '**', redirectTo: '/landing' }
];
