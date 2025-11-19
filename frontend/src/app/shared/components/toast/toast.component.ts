import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ToastService } from '../../services/toast.service';

@Component({
  selector: 'app-toast',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="toast-container" *ngIf="show" [ngClass]="type">
      <div class="toast-content">
        <span class="toast-message">{{ message }}</span>
      <button class="toast-close" (click)="closeToast()">&times;</button>
      </div>
    </div>
  `,
  styleUrls: ['./toast.component.css']
})
export class ToastComponent implements OnInit, OnDestroy {
  show = false;
  message = '';
  type = '';
  private timeoutId: any;

  constructor(private toastService: ToastService) {}

  ngOnInit(): void {
    this.toastService.getToastState().subscribe(state => {
      this.show = state.show;
      this.message = state.message;
      this.type = state.type;
    });
  }

  closeToast(): void {
    this.toastService.hide();
  }

  ngOnDestroy(): void {
    if (this.timeoutId) {
      clearTimeout(this.timeoutId);
    }
  }
}