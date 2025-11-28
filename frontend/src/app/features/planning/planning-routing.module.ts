import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { authGuard } from '../../core/guards/auth.guard';

const routes: Routes = [
  {
    path: 'file-upload',
    loadComponent: () => import('./file-upload/file-upload.component').then(m => m.FileUploadComponent)
  },
  {
    path: 'scheduling',
    loadComponent: () => import('./scheduling/scheduling.component').then(m => m.SchedulingComponent),
    canActivate: [authGuard]
  },
  {
    path: '',
    redirectTo: 'file-upload',
    pathMatch: 'full'
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class PlanningRoutingModule { }