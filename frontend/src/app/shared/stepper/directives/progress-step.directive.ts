import { Directive, ElementRef, HostListener, Input, OnInit } from '@angular/core';
import { ProgressHelperService } from '../services/progress-helper.service';

@Directive({
  selector: '[progressStepNext], [progressStepPrev]',
  standalone: true
})
export class ProgressStepDirective implements OnInit {
  @Input('progressStepNext') next: boolean | undefined;
  @Input('progressStepPrev') prev: boolean | undefined;

  private methods = {
    next: false,
    prev: false,
  };

  constructor(
    private progressHelper: ProgressHelperService,
    private el: ElementRef<HTMLButtonElement>
  ) {}

  ngOnInit() {
    this.initMethods();
  }

  @HostListener('click', ['$event'])
  listen(event: Event) {
    this.progressHelper.eventHelper.next(this.methods);
  }

  private initMethods(): void {
    if (this.next !== undefined) {
      this.methods = {
        ...this.methods,
        next: true,
      };
    }

    if (this.prev !== undefined) {
      this.methods = {
        ...this.methods,
        prev: true,
      };
    }
  }
}