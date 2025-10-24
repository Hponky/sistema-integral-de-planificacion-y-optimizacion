import {
  AfterContentInit,
  Component,
  ContentChildren,
  EventEmitter,
  Input,
  OnInit,
  Output,
  QueryList,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { ProgressHelperService } from '../services/progress-helper.service';
import { ProgressStepComponent } from './progress-step.component';
import { Status } from '../utils/stepper.enums';

@Component({
  selector: 'app-progress',
  templateUrl: './progress.component.html',
  styleUrls: ['./progress.component.css'],
  standalone: true,
  imports: [CommonModule, ProgressStepComponent],
  providers: [ProgressHelperService]
})
export class ProgressComponent implements OnInit, AfterContentInit {
  itemLength: number = 0;
  itemProgressList: { stepIndex: number; status: string }[] = [];
  activeIndex = 0;

  @Input() public set selectedIndex(value: number) {
    this.activeIndex = value || 0;
  }

  @Output() public stateChange = new EventEmitter<{
    activeIndex: number;
    activeStep: ProgressStepComponent;
  }>();

  @ContentChildren(ProgressStepComponent) public steps!: QueryList<
    ProgressStepComponent
  >;

  constructor(private progressHelper: ProgressHelperService) {}

  ngOnInit(): void {
    this.progressHelper.eventHelper.subscribe({
      next: ({ prev, next }) => {
        if (next) {
          this.next();
        }

        if (prev) {
          this.prev();
        }
      },
    });
  }

  ngAfterContentInit() {
    this.initProgress(this.progressSteps.length);
    this.setActiveActiveStep(this.activeIndex);
    this.initStepIndex();
  }

  public next() {
    this.increaseStep();
  }

  public prev() {
    this.decreaseStep();
  }

  private increaseStep() {
    if (
      this.activeIndex === this.itemLength - 1 &&
      this.itemProgressList[this.activeIndex].status !== Status.COMPLETED
    ) {
      this.completeLastStep();
    }

    if (this.activeIndex < this.itemLength - 1) {
      this.activeIndex++;
      this.switchStatusNext(this.activeIndex);
      this.setActiveActiveStep(this.activeIndex);
      this.emitStateChange();
    }
  }

  private decreaseStep() {
    if (
      this.activeIndex === this.itemLength - 1 &&
      this.itemProgressList[this.activeIndex].status === Status.COMPLETED
    ) {
      this.undoLastComplete();
    } else {
      if (this.activeIndex > 0) {
        this.activeIndex--;
        this.switchStatusPrev(this.activeIndex);
        this.setActiveActiveStep(this.activeIndex);
        this.emitStateChange();
      }
    }
  }

  private emitStateChange(): void {
    this.stateChange.emit({
      activeIndex: this.activeIndex,
      activeStep: this.activeStep,
    });
  }

  private setActiveActiveStep(index: number): void {
    if (this.stepsExists) {
      this.removeActiveStep();
      this.updateActiveStep(index);
    }
  }

  private updateActiveStep(index: number) {
    this.progressSteps[index].activeState = this.progressSteps[index];
  }

  private removeActiveStep() {
    this.progressSteps.map((step) => {
      if (step.isActive) {
        step.isActive = false;
      }
    });
  }

  private initStepIndex() {
    this.progressSteps.forEach((step, i) => (step.stepIndex = i));
  }

  public get activeStep(): ProgressStepComponent {
    return this.progressSteps[this.activeIndex];
  }

  private get stepsExists(): boolean {
    return this.progressSteps && Array.isArray(this.progressSteps);
  }

  private get progressSteps(): ProgressStepComponent[] {
    return this.steps.toArray();
  }

  private generateProgressArray(length: number): any[] {
    return [...Array(length).keys()].map((key) => {
      return {
        stepIndex: key,
        status: key === this.activeIndex ? Status.IN_PROGRESS : Status.PENDING,
      };
    });
  }

  private initProgress(value: number): void {
    this.itemLength = value || 0;
    this.itemProgressList = this.generateProgressArray(this.itemLength);
  }

  private completeLastStep() {
    this.itemProgressList[this.activeIndex].status = Status.COMPLETED;
  }

  private undoLastComplete() {
    this.itemProgressList[this.activeIndex].status = Status.IN_PROGRESS;
  }

  private switchStatusNext(index: number): void {
    this.itemProgressList[this.activeIndex - 1].status = Status.COMPLETED;
    this.itemProgressList[index].status = Status.IN_PROGRESS;
  }

  private switchStatusPrev(index: number) {
    this.itemProgressList[this.activeIndex + 1].status = Status.PENDING;
    this.itemProgressList[index].status = Status.IN_PROGRESS;
  }
}