import { Injectable, inject } from '@angular/core';
import { CanActivateFn, ActivatedRouteSnapshot, RouterStateSnapshot, Router } from '@angular/router';
import { Observable, map, take } from 'rxjs';
import { AuthService } from '../services/auth.service';

@Injectable({
  providedIn: 'root'
})
export class AuthGuardService {
  constructor(private authService: AuthService, private router: Router) {}

  canActivate(
    route: ActivatedRouteSnapshot,
    state: RouterStateSnapshot
  ): Observable<boolean> | boolean {
    return this.authService.currentUser$.pipe(
      take(1),
      map(user => {
        if (user) {
          // Verificar si la ruta requiere rol específico
          const requiredRole = route.data['role'];
          if (requiredRole && user.role !== requiredRole) {
            this.router.navigate(['/calculator']);
            return false;
          }
          return true;
        } else {
          // Si no hay usuario en el estado local, verificar sesión en el servidor
          this.authService.checkSession().subscribe({
            next: (session) => {
              if (session.authenticated && session.user) {
                // Si hay sesión activa en el servidor, actualizar el estado local
                const user = {
                  id: 0, // ID temporal ya que el backend no lo proporciona
                  username: session.user.username,
                  role: session.user.role
                };
                this.authService.setUser(user as any);
                // Recargar la página para que el guard pueda verificar nuevamente
                window.location.reload();
              } else {
                // Redirigir al login si no hay sesión activa
                this.router.navigate(['/login']);
              }
            },
            error: () => {
              // En caso de error, redirigir al login
              this.router.navigate(['/login']);
            }
          });
          return false;
        }
      })
    );
  }
}

export const authGuard: CanActivateFn = (route: ActivatedRouteSnapshot, state: RouterStateSnapshot) => {
  const authService = inject(AuthService);
  const router = inject(Router);
  
  return authService.currentUser$.pipe(
    take(1),
    map(user => {
      if (user) {
        // Verificar si la ruta requiere rol específico
        const requiredRole = route.data['role'];
        if (requiredRole && user.role !== requiredRole) {
          router.navigate(['/calculator']);
          return false;
        }
        return true;
      } else {
        // Si no hay usuario en el estado local, verificar sesión en el servidor
        authService.checkSession().subscribe({
          next: (session) => {
            if (session.authenticated && session.user) {
              // Si hay sesión activa en el servidor, actualizar el estado local
              const user = {
                id: 0, // ID temporal ya que el backend no lo proporciona
                username: session.user.username,
                role: session.user.role
              };
              authService.setUser(user as any);
              // Recargar la página para que el guard pueda verificar nuevamente
              window.location.reload();
            } else {
              // Redirigir al login si no hay sesión activa
              router.navigate(['/login']);
            }
          },
          error: () => {
            // En caso de error, redirigir al login
            router.navigate(['/login']);
          }
        });
        return false;
      }
    })
  );
};