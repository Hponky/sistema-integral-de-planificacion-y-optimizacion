import { inject } from '@angular/core';
import { CanActivateFn, Router, ActivatedRouteSnapshot, RouterStateSnapshot } from '@angular/router';
import { AuthService } from '../services/auth.service';

export const authGuard: CanActivateFn = (route: ActivatedRouteSnapshot, state: RouterStateSnapshot) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (authService.isAuthenticated()) {
    const user = authService.getCurrentUser();
    const requiredRoles: string | string[] = route.data['role'];

    if (requiredRoles) {
      const hasRole = Array.isArray(requiredRoles)
        ? requiredRoles.includes(user?.role || '')
        : user?.role === requiredRoles;

      if (!hasRole) {
        // User is authenticated but doesn't have the required role
        router.navigate(['/landing']);
        return false;
      }
    }

    return true;
  } else {
    // User is not authenticated
    router.navigate(['/login'], { queryParams: { returnUrl: state.url } });
    return false;
  }
};