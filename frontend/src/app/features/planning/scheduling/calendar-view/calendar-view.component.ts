import { Component, inject, effect, ViewChild, ElementRef, AfterViewInit, OnDestroy, PLATFORM_ID } from '@angular/core';
import { CommonModule, isPlatformBrowser } from '@angular/common';
import Chart, { ChartData } from 'chart.js/auto';
import type { Chart as ChartType } from 'chart.js';

import { SchedulingFacadeService } from '../scheduling-facade.service';
import type { Schedule, Shift } from '../interfaces';

@Component({
  selector: 'app-calendar-view',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './calendar-view.component.html',
  styleUrls: ['./calendar-view.component.css']
})
export class CalendarViewComponent implements AfterViewInit, OnDestroy {
  @ViewChild('chartCanvas') canvasRef!: ElementRef<HTMLCanvasElement>;
  private platformId = inject(PLATFORM_ID);
  isBrowser = isPlatformBrowser(this.platformId);
  private chart?: ChartType<'doughnut', number[], string>;

  facade = inject(SchedulingFacadeService);

  constructor() {
    effect((onCleanup) => {
      const schedule = this.facade.schedule();
      onCleanup(() => { });
      if (this.isBrowser && this.canvasRef) {
        this.updateChart(schedule);
      }
    });
  }

  ngAfterViewInit() {
    if (this.isBrowser) {
      this.updateChart(this.facade.schedule());
    }
  }

  ngOnDestroy() {
    this.chart?.destroy();
  }

  private updateChart(schedule: Schedule) {
    if (!this.isBrowser || !this.canvasRef) return;

    if (this.chart) {
      this.chart.destroy();
    }
    const data = this.computeChartData(schedule);
    this.chart = new Chart<'doughnut', number[], string>(this.canvasRef.nativeElement, {
      type: 'doughnut',
      data,
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              padding: 20,
              font: {
                size: 13,
                weight: 'bold'
              },
              usePointStyle: true,
              pointStyle: 'circle'
            }
          },
          tooltip: {
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            padding: 12,
            cornerRadius: 8,
            titleFont: {
              size: 14,
              weight: 'bold'
            },
            bodyFont: {
              size: 13
            }
          }
        },
        cutout: '65%'
      }
    });
  }

  private computeChartData(schedule: Schedule): ChartData<'doughnut', number[], string> {
    const tipoCount: Record<Shift['tipo'], number> = {
      'LIBRE': 0,
      'VAC': 0,
      'BMED': 0,
      '08:00-17:00': 0,
      '16:00-00:00': 0,
      '00:00-08:00': 0
    };
    schedule.days.forEach(day => {
      Object.values(day.agentShifts).forEach(shift => {
        if (shift && shift.tipo) {
          tipoCount[shift.tipo] = (tipoCount[shift.tipo] || 0) + 1;
        }
      });
    });
    const labels = Object.keys(tipoCount);
    const dataValues = Object.values(tipoCount);
    return {
      labels,
      datasets: [{
        data: dataValues,
        backgroundColor: [
          '#ffc107', // LIBRE
          '#dc3545', // VAC
          '#6c757d', // BMED
          '#28a745', // 08-17
          '#007bff', // 16-00
          '#fd7e14'  // 00-08
        ],
        borderWidth: 0,
        hoverOffset: 15
      }]
    };
  }
}