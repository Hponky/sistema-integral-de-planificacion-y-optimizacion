import { ProgressHelperService } from '../services/progress-helper.service';
import { Status } from './stepper.enums';

export enum UiState {
  ACTIVE = 'active',
  COMPLETE = 'complete',
}

export interface StepProgress {
  stepIndex: number;
  status: string;
}

export class UiHelper {
  public itemProgressList: StepProgress[] = [];
  public activeIndex = 0;

  constructor(protected progressHelper: ProgressHelperService) {}

  protected completeLastStep(): void {
    if (this.itemProgressList.length > 0 && this.activeIndex >= 0 && this.activeIndex < this.itemProgressList.length) {
      this.itemProgressList[this.activeIndex].status = Status.COMPLETED;
    }
  }

  protected undoLastComplete(): void {
    if (this.itemProgressList.length > 0 && this.activeIndex >= 0 && this.activeIndex < this.itemProgressList.length) {
      this.itemProgressList[this.activeIndex].status = Status.IN_PROGRESS;
    }
  }

  protected switchStatusNext(index: number): void {
    if (this.activeIndex > 0 && this.activeIndex <= this.itemProgressList.length) {
      this.itemProgressList[this.activeIndex - 1].status = Status.COMPLETED;
    }
    if (index >= 0 && index < this.itemProgressList.length) {
      this.itemProgressList[index].status = Status.IN_PROGRESS;
    }
  }

  protected switchStatusPrev(index: number): void {
    const nextIndex = this.activeIndex + 1;
    if (nextIndex >= 0 && nextIndex < this.itemProgressList.length) {
      this.itemProgressList[nextIndex].status = Status.PENDING;
    }
    if (index >= 0 && index < this.itemProgressList.length) {
      this.itemProgressList[index].status = Status.IN_PROGRESS;
    }
  }

  public initializeSteps(totalSteps: number): void {
    this.itemProgressList = Array.from({ length: totalSteps }, (_, index) => ({
      stepIndex: index,
      status: index === 0 ? Status.IN_PROGRESS : Status.PENDING
    }));
    this.activeIndex = 0;
  }

  public getCurrentStepStatus(): string {
    if (this.activeIndex >= 0 && this.activeIndex < this.itemProgressList.length) {
      return this.itemProgressList[this.activeIndex].status;
    }
    return Status.PENDING;
  }

  public getStepStatus(index: number): string {
    if (index >= 0 && index < this.itemProgressList.length) {
      return this.itemProgressList[index].status;
    }
    return Status.PENDING;
  }

  public isLastStep(): boolean {
    return this.activeIndex === this.itemProgressList.length - 1;
  }

  public isFirstStep(): boolean {
    return this.activeIndex === 0;
  }

  public canGoNext(): boolean {
    return !this.isLastStep() && this.getCurrentStepStatus() === Status.COMPLETED;
  }

  public canGoPrev(): boolean {
    return !this.isFirstStep();
  }
}