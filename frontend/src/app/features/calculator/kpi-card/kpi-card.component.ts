import { Component, Input, OnChanges, SimpleChanges, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';

export interface KpiData {
  label: string;
  value: number | string;
  icon?: string;
  trend?: {
    value: number;
    direction: 'up' | 'down' | 'neutral';
  };
  format?: 'percentage' | 'number' | 'currency';
  color?: string;
}

@Component({
  selector: 'app-kpi-card',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './kpi-card.component.html',
  styleUrls: ['./kpi-card.component.css'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class KpiCardComponent implements OnChanges {
  @Input() kpiData!: KpiData;
  @Input() animated: boolean = true;

  displayValue: string = '';
  trendIcon: string = '';
  trendClass: string = '';
  isAnimating: boolean = false;

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['kpiData'] && this.kpiData) {
      this.formatValue();
      this.setTrend();
      
      if (this.animated && changes['kpiData'].firstChange === false) {
        this.triggerAnimation();
      }
    }
  }

  private formatValue(): void {
    const { value, format } = this.kpiData;
    
    switch (format) {
      case 'percentage':
        this.displayValue = `${Number(value).toFixed(1)}%`;
        break;
      case 'currency':
        this.displayValue = new Intl.NumberFormat('es-CO', {
          style: 'currency',
          currency: 'COP'
        }).format(Number(value));
        break;
      case 'number':
      default:
        this.displayValue = new Intl.NumberFormat('es-CO').format(Number(value));
        break;
    }
  }

  private setTrend(): void {
    if (!this.kpiData.trend) {
      this.trendIcon = '';
      this.trendClass = '';
      return;
    }

    const { direction } = this.kpiData.trend;
    switch (direction) {
      case 'up':
        this.trendIcon = '📈';
        this.trendClass = 'trend-up';
        break;
      case 'down':
        this.trendIcon = '📉';
        this.trendClass = 'trend-down';
        break;
      case 'neutral':
      default:
        this.trendIcon = '➡️';
        this.trendClass = 'trend-neutral';
        break;
    }
  }

  private triggerAnimation(): void {
    this.isAnimating = true;
    setTimeout(() => {
      this.isAnimating = false;
    }, 600);
  }

  getTrendValue(): string {
    if (!this.kpiData.trend) return '';
    
    const { value, direction } = this.kpiData.trend;
    const sign = direction === 'up' ? '+' : direction === 'down' ? '-' : '';
    return `${sign}${Math.abs(value).toFixed(1)}%`;
  }

  getCardClasses(): string {
    const classes = ['kpi-card'];
    
    if (this.isAnimating) {
      classes.push('kpi-card--animating');
    }
    
    if (this.kpiData.color) {
      classes.push(`kpi-card--${this.kpiData.color}`);
    }
    
    if (this.trendClass) {
      classes.push(this.trendClass);
    }
    
    return classes.join(' ');
  }
}