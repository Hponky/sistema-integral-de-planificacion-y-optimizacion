import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, Router } from '@angular/router';
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

  constructor(
    private authService: AuthService,
    private authenticationStateService: AuthenticationStateService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.isAuthenticated$ = this.authenticationStateService.currentState$.pipe(
      map((state: AuthenticationState) => state === AuthenticationState.AUTHENTICATED)
    );
    
    this.checkInitialAuthState();
  }
  
  private checkInitialAuthState(): void {
    const currentUser = this.authService.getCurrentUser();
    if (currentUser) {
      this.authenticationStateService.setState(AuthenticationState.AUTHENTICATED).subscribe();
    }
  }

  logout(): void {
    this.authService.logout().subscribe({
      next: () => {
        this.authenticationStateService.setState(AuthenticationState.NOT_AUTHENTICATED);
        this.router.navigate(['/login']);
      },
      error: (error) => {
        console.error('Error durante el logout:', error);
      }
    });
  }

  getCurrentUser(): string {
    const user = this.authService.getCurrentUser();
    return user?.username || 'Usuario';
  }
}