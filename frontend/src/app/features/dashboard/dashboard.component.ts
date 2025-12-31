import { Component, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';
import { CalculationHistoryComponent } from '../calculator/calculation-history/calculation-history.component';

interface StatCard {
  icon: string;
  title: string;
  value: string;
  change: string;
  changeType: 'positive' | 'negative' | 'neutral';
  color: string;
}

interface QuickAction {
  icon: string;
  title: string;
  description: string;
  route: string;
  color: string;
}

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule, CalculationHistoryComponent],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css']
})
export class DashboardComponent implements OnInit {
  constructor(private router: Router) { }

  currentTime = signal(new Date());

  // Estadísticas del dashboard
  stats = signal<StatCard[]>([
    {
      icon: '📊',
      title: 'Cálculos Totales',
      value: '156',
      change: '+12%',
      changeType: 'positive',
      color: 'purple'
    },
    {
      icon: '👥',
      title: 'Agentes Activos',
      value: '1,234',
      change: '+5.2%',
      changeType: 'positive',
      color: 'blue'
    },
    {
      icon: '📅',
      title: 'Horarios Generados',
      value: '89',
      change: '+8%',
      changeType: 'positive',
      color: 'green'
    },
    {
      icon: '⚡',
      title: 'Eficiencia Promedio',
      value: '94.5%',
      change: '+2.1%',
      changeType: 'positive',
      color: 'orange'
    }
  ]);

  // Acciones rápidas
  quickActions = signal<QuickAction[]>([
    {
      icon: '🧮',
      title: 'Nueva Calculadora',
      description: 'Dimensiona tu equipo',
      route: '/calculator',
      color: 'purple'
    },
    {
      icon: '📅',
      title: 'Generar Horarios',
      description: 'Planifica turnos',
      route: '/planning/scheduling',
      color: 'blue'
    },
    {
      icon: '📈',
      title: 'Ver Reportes',
      description: 'Análisis detallado',
      route: '/reports',
      color: 'green'
    },
    {
      icon: '⚙️',
      title: 'Configuración',
      description: 'Ajustes del sistema',
      route: '/settings',
      color: 'orange'
    }
  ]);

  ngOnInit(): void {
    // Actualizar reloj cada segundo
    setInterval(() => {
      this.currentTime.set(new Date());
    }, 1000);
  }

  getGreeting(): string {
    const hour = new Date().getHours();
    if (hour < 12) return 'Buenos días';
    if (hour < 18) return 'Buenas tardes';
    return 'Buenas noches';
  }

  onViewHistoryDetails(id: number): void {
    this.router.navigate(['/calculator'], { queryParams: { scenarioId: id } });
  }

  navigateTo(route: string): void {
    this.router.navigate([route]);
  }
}