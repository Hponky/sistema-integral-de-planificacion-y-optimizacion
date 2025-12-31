import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, Router, RouterLinkActive } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatToolbarModule } from '@angular/material/toolbar';
import { Observable, map } from 'rxjs';
import { AsyncPipe } from '@angular/common';

import { AuthenticationStateService, AuthenticationState } from '../../../core/services/authentication-state.service';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    RouterLinkActive,
    MatButtonModule,
    MatIconModule,
    MatToolbarModule,
    AsyncPipe
  ],
  templateUrl: './navbar.component.html',
  styleUrl: './navbar.component.css'
})
export class NavbarComponent implements OnInit {
  isAuthenticated$!: Observable<boolean>;
  isMobileMenuOpen = false;
  isModulesDropdownOpen = false;

  constructor(
    private authService: AuthService,
    private authenticationStateService: AuthenticationStateService,
    private router: Router
  ) { }

  ngOnInit(): void {
    this.isAuthenticated$ = this.authenticationStateService.currentState$.pipe(
      map((state: AuthenticationState) => state === AuthenticationState.AUTHENTICATED)
    );
  }

  toggleMobileMenu(): void {
    this.isMobileMenuOpen = !this.isMobileMenuOpen;

    // Lock/unlock body scroll
    if (this.isMobileMenuOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
      this.isModulesDropdownOpen = false;
    }
  }

  closeMobileMenu(): void {
    this.isMobileMenuOpen = false;
    this.isModulesDropdownOpen = false;
    document.body.style.overflow = '';
  }

  toggleModulesDropdown(): void {
    this.isModulesDropdownOpen = !this.isModulesDropdownOpen;
  }

  showModulesDropdown(): void {
    // Only for desktop hover (above 1024px)
    if (window.innerWidth > 1024) {
      this.isModulesDropdownOpen = true;
    }
  }

  hideModulesDropdown(): void {
    // Only for desktop hover (above 1024px)
    if (window.innerWidth > 1024) {
      this.isModulesDropdownOpen = false;
    }
  }

  logout(): void {
    const currentUrl = this.router.url;
    this.authService.logout();
    this.router.navigate(['/login'], { queryParams: { returnUrl: currentUrl } });
    this.closeMobileMenu();
  }

  getCurrentUser(): string {
    const user = this.authService.getCurrentUser();
    return user?.fullName || user?.username || 'Usuario';
  }

  getUserRole(): string {
    try {
      const variablesStr = localStorage.getItem('VariablesDeUsuarioLogado');
      if (!variablesStr) return '';

      const variables = JSON.parse(variablesStr);
      const permisos = variables?.Permisos || [];

      // Check permissions in priority order
      if (permisos.includes(51781)) {
        return 'Administrador';
      } else if (permisos.includes(51782)) {
        return 'Planificador';
      } else if (permisos.includes(51783)) {
        return 'Sólo lectura';
      }

      return '';
    } catch (error) {
      console.error('Error getting user role:', error);
      return '';
    }
  }
}