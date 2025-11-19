import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ToastService {
  private toastState = new BehaviorSubject<{ show: boolean; message: string; type: string }>({
    show: false,
    message: '',
    type: ''
  });

  constructor() {}

  getToastState() {
    return this.toastState.asObservable();
  }

  showError(message: string, duration: number = 5000): void {
    this.showToast(message, 'error', duration);
  }

  showSuccess(message: string, duration: number = 3000): void {
    this.showToast(message, 'success', duration);
  }

  showWarning(message: string, duration: number = 4000): void {
    this.showToast(message, 'warning', duration);
  }

  showInfo(message: string, duration: number = 3000): void {
    this.showToast(message, 'info', duration);
  }

  hide(): void {
    this.toastState.next({ show: false, message: '', type: '' });
  }

  private showToast(message: string, type: string, duration: number): void {
    this.toastState.next({ show: true, message, type });
    
    setTimeout(() => {
      this.hide();
    }, duration);
  }
}