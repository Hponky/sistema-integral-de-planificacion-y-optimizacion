import { Component, Input, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

@Component({
  selector: 'app-features',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatIconModule,
    MatButtonModule,
    MatProgressSpinnerModule
  ],
  templateUrl: './features.component.html',
  styleUrl: './features.component.css'
})
export class FeaturesComponent implements OnInit {
  features = [
    {
      id: 1,
      title: 'Cálculos Erlang Precisos',
      description: 'Algoritmos optimizados para dimensionamiento de personal y análisis de tráfico.',
      icon: 'calculate',
      color: 'primary'
    },
    {
      id: 2,
      title: 'Planificación de Turnos',
      description: 'Gestión eficiente de horarios y asignación de recursos.',
      icon: 'schedule',
      color: 'accent'
    },
    {
      id: 3,
      title: 'Análisis SLA',
      description: 'Evaluación de niveles de servicio y cumplimiento de objetivos.',
      icon: 'analytics',
      color: 'warn'
    }
  ];

  benefits = [
    {
      id: 1,
      title: 'Optimización de Recursos',
      description: 'Reduce costos operativos hasta en un 30%.',
      icon: 'trending_up',
      color: 'primary'
    },
    {
      id: 2,
      title: 'Mejora del Servicio',
      description: 'Aumenta la satisfacción del cliente mediante análisis de datos.',
      icon: 'thumb_up',
      color: 'accent'
    },
    {
      id: 3,
      title: 'Toma de Decisiones',
      description: 'Información basada en datos para una gestión estratégica.',
      icon: 'lightbulb',
      color: 'warn'
    }
  ];

  constructor() {}

  ngOnInit(): void {}
}