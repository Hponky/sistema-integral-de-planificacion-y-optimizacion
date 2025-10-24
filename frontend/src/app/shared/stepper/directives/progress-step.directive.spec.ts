import { Component, DebugElement } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { ProgressHelperService } from '../services/progress-helper.service';
import { ProgressStepDirective } from './progress-step.directive';

@Component({
  template: `
    <button progressStepNext>Next</button>
    <button progressStepPrev>Previous</button>
    <button progressStepNext progressStepPrev>Both</button>
    <button>None</button>
  `,
  standalone: true,
  imports: [ProgressStepDirective]
})
class TestComponent {}

describe('ProgressStepDirective', () => {
  let component: TestComponent;
  let fixture: ComponentFixture<TestComponent>;
  let progressHelperService: jasmine.SpyObj<ProgressHelperService>;
  let nextButton: DebugElement;
  let prevButton: DebugElement;
  let bothButton: DebugElement;
  let noneButton: DebugElement;

  beforeEach(async () => {
    const spy = jasmine.createSpyObj('ProgressHelperService', [], ['eventHelper']);
    spy.eventHelper = jasmine.createSpyObj('Subject', ['next']);

    await TestBed.configureTestingModule({
      imports: [TestComponent, ProgressStepDirective],
      providers: [
        { provide: ProgressHelperService, useValue: spy }
      ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(TestComponent);
    component = fixture.componentInstance;
    progressHelperService = TestBed.inject(ProgressHelperService) as jasmine.SpyObj<ProgressHelperService>;
    
    fixture.detectChanges();

    nextButton = fixture.debugElement.query(By.css('button[progressStepNext]:not([progressStepPrev])'));
    prevButton = fixture.debugElement.query(By.css('button[progressStepPrev]:not([progressStepNext])'));
    bothButton = fixture.debugElement.query(By.css('button[progressStepNext][progressStepPrev]'));
    noneButton = fixture.debugElement.query(By.css('button:not([progressStepNext]):not([progressStepPrev])'));
  });

  it('should create test component', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize next button with next method', () => {
    const directive = nextButton.injector.get(ProgressStepDirective);
    expect(directive['methods'].next).toBe(true);
    expect(directive['methods'].prev).toBe(false);
  });

  it('should initialize previous button with prev method', () => {
    const directive = prevButton.injector.get(ProgressStepDirective);
    expect(directive['methods'].next).toBe(false);
    expect(directive['methods'].prev).toBe(true);
  });

  it('should initialize button with both directives correctly', () => {
    const directive = bothButton.injector.get(ProgressStepDirective);
    expect(directive['methods'].next).toBe(true);
    expect(directive['methods'].prev).toBe(true);
  });

  it('should emit event when next button is clicked', () => {
    nextButton.triggerEventHandler('click', null);
    
    expect(progressHelperService.eventHelper.next).toHaveBeenCalledWith({
      next: true,
      prev: false
    });
  });

  it('should emit event when previous button is clicked', () => {
    prevButton.triggerEventHandler('click', null);
    
    expect(progressHelperService.eventHelper.next).toHaveBeenCalledWith({
      next: false,
      prev: true
    });
  });

  it('should emit event when button with both directives is clicked', () => {
    bothButton.triggerEventHandler('click', null);
    
    expect(progressHelperService.eventHelper.next).toHaveBeenCalledWith({
      next: true,
      prev: true
    });
  });

  it('should not have directive on button without attributes', () => {
    expect(noneButton.injector.get(ProgressStepDirective, null)).toBeNull();
  });

  it('should have ElementRef injected', () => {
    const directive = nextButton.injector.get(ProgressStepDirective);
    expect(directive['el']).toBeDefined();
    expect(directive['el'] instanceof HTMLElement).toBe(true);
  });
});