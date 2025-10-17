import { Injectable, inject } from '@angular/core';
import { CanActivateFn, ActivatedRouteSnapshot, RouterStateSnapshot, Router } from '@angular/router';
import { Observable, of, switchMap } from 'rxjs';
import { AuthService } from '../services/auth.service';

@Injectable({
  providedIn: 'root'
})
export class AuthGuardService {
  constructor(private authService: AuthService, private router: Router) {}

  canActivate(
    route: ActivatedRouteSnapshot,
    state: RouterStateSnapshot
  ): Observable<boolean> {
    return this.authService.currentUser$.pipe(
      switchMap(user => {
        if (user) {
          // Verificar si la ruta requiere rol específico
          const requiredRole = route.data['role'];
          if (requiredRole && user.role !== requiredRole) {
            this.router.navigate(['/calculator']);
            return of(false);
          }
          return of(true);
        } else {
          // Si no hay usuario en el estado local, verificar sesión en el servidor
          return this.authService.checkSession().pipe(
            switchMap(session => {
              if (session.authenticated && session.user) {
                // Si hay sesión activa en el servidor, actualizar el estado local
                const userData = {
                  id: 0, // ID temporal ya que el backend no lo proporciona
                  username: session.user.username,
                  role: session.user.role
                };
                this.authService.setUser(userData as any);
                
                // Verificar si la ruta requiere rol específico
                const requiredRole = route.data['role'];
                if (requiredRole && userData.role !== requiredRole) {
                  this.router.navigate(['/calculator']);
                  return of(false);
                }
                return of(true);
              } else {
                // Redirigir al login si no hay sesión activa
                this.router.navigate(['/login']);
                return of(false);
              }
            })
          );
        }
      })
    );
  }
}

export const authGuard: CanActivateFn = (route: ActivatedRouteSnapshot, state: RouterStateSnapshot) => {
  const authService = inject(AuthService);
  const router = inject(Router);
  
  return authService.currentUser$.pipe(
    switchMap(user => {
      if (user) {
        // Verificar si la ruta requiere rol específico
        const requiredRole = route.data['role'];
        if (requiredRole && user.role !== requiredRole) {
          router.navigate(['/calculator']);
          return of(false);
        }
        return of(true);
      } else {
        // Si no hay usuario en el estado local, verificar sesión en el servidor
        return authService.checkSession().pipe(
          switchMap(session => {
            if (session.authenticated && session.user) {
              // Si hay sesión activa en el servidor, actualizar el estado local
              const userData = {
                id: 0, // ID temporal ya que el backend no lo proporciona
                username: session.user.username,
                role: session.user.role
              };
              authService.setUser(userData as any);
              
              // Verificar si la ruta requiere rol específico
              const requiredRole = route.data['role'];
              if (requiredRole && userData.role !== requiredRole) {
                router.navigate(['/calculator']);
                return of(false);
              }
              return of(true);
            } else {
              // Redirigir al login si no hay sesión activa
              router.navigate(['/login']);
              return of(false);
            }
          })
        );
      }
    })
  );
};