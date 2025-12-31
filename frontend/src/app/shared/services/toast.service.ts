import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

export interface Toast {
  id: number;
  title: string;
  message: string;
  type: 'success' | 'error' | 'warning' | 'info';
  icon: string;
  removing?: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class ToastService {
  private toasts = new BehaviorSubject<Toast[]>([]);
  private toastIdCounter = 0;

  constructor() { }

  getToasts() {
    return this.toasts.asObservable();
  }

  showError(message: string, title: string = 'Error', duration: number = 5000): void {
    this.showToast(title, message, 'error', duration);
  }

  showSuccess(message: string, title: string = 'Éxito', duration: number = 3000): void {
    this.showToast(title, message, 'success', duration);
  }

  showWarning(message: string, title: string = 'Advertencia', duration: number = 4000): void {
    this.showToast(title, message, 'warning', duration);
  }

  showInfo(message: string, title: string = 'Información', duration: number = 3000): void {
    this.showToast(title, message, 'info', duration);
  }

  remove(id: number): void {
    const currentToasts = this.toasts.value;
    const toast = currentToasts.find(t => t.id === id);

    if (toast) {
      toast.removing = true;
      this.toasts.next([...currentToasts]);

      setTimeout(() => {
        this.toasts.next(currentToasts.filter(t => t.id !== id));
      }, 300); // Match animation duration
    }
  }

  private showToast(title: string, message: string, type: 'success' | 'error' | 'warning' | 'info', duration: number): void {
    const icons = {
      success: '✅',
      error: '❌',
      warning: '⚠️',
      info: 'ℹ️'
    };

    const toast: Toast = {
      id: this.toastIdCounter++,
      title,
      message,
      type,
      icon: icons[type]
    };

    const currentToasts = this.toasts.value;
    this.toasts.next([...currentToasts, toast]);

    setTimeout(() => {
      this.remove(toast.id);
    }, duration);
  }
}