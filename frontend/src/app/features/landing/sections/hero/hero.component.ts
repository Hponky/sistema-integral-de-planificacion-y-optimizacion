import { Component } from '@angular/core';
import { trigger, state, style, transition, animate } from '@angular/animations';
import { Router } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { AuthService } from '../../../../core/services/auth.service';

@Component({
  selector: 'app-hero',
  standalone: true,
  imports: [MatButtonModule],
  templateUrl: './hero.component.html',
  styleUrl: './hero.component.css',
  animations: [
    trigger('heroEnter', [
      state('void', style({ opacity: 0 })),
      state('visible', style({ opacity: 1 })),
      transition('void => visible', animate('600ms ease-in'))
    ]),
    trigger('heroLeave', [
      state('visible', style({ opacity: 1 })),
      state('void', style({ opacity: 0 })),
      transition('visible => void', animate('600ms ease-out'))
    ])
  ]
})
export class HeroComponent {
  title = 'Sistema Integral de Planificación y Optimización';
  subtitle = 'Optimiza tus recursos con cálculos Erlang precisos';
  description = 'Herramienta avanzada para dimensionamiento de personal y planificación de turnos con análisis de SLA';
  ctaText = 'Comenzar ahora';
  isVisible = true;

  constructor(
    private readonly router: Router,
    private readonly authService: AuthService
  ) {}

  navigateToApp = () => {
    if (this.authService.isAuthenticated()) {
      this.router.navigate(['/calculator']);
    } else {
      this.router.navigate(['/login']);
    }
  };
}
