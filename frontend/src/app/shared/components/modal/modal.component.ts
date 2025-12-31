import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
    selector: 'app-modal',
    standalone: true,
    imports: [CommonModule],
    template: `
    @if (isOpen) {
      <div class="modal-backdrop" (click)="onBackdropClick()">
        <div class="modal-content" [class]="size" (click)="$event.stopPropagation()">
          <ng-content></ng-content>
        </div>
      </div>
    }
  `,
    styleUrls: ['./modal.component.css']
})
export class ModalComponent {
    @Input() isOpen = false;
    @Input() size: 'small' | 'medium' | 'large' = 'medium';
    @Input() closeOnBackdrop = true;
    @Output() close = new EventEmitter<void>();

    onBackdropClick() {
        if (this.closeOnBackdrop) {
            this.close.emit();
        }
    }
}
