import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ProgressStepComponent } from './progress-step.component';

describe('ProgressStepComponent', () => {
  let component: ProgressStepComponent;
  let fixture: ComponentFixture<ProgressStepComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ProgressStepComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ProgressStepComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize with stepIndex 0', () => {
    expect(component.stepIndex).toBe(0);
  });

  it('should initialize with isActive false', () => {
    expect(component.isActive).toBe(false);
  });

  it('should set isActive to true when setting activeState to itself', () => {
    component.activeState = component;
    expect(component.isActive).toBe(true);
  });

  it('should set isActive to false when setting activeState to different component', () => {
    const otherComponent = new ProgressStepComponent();
    component.activeState = otherComponent;
    expect(component.isActive).toBe(false);
  });

  it('should have hostBinding class activeStep when isActive is true', () => {
    component.isActive = true;
    fixture.detectChanges();
    
    const element = fixture.nativeElement;
    expect(element.classList.contains('activeStep')).toBe(true);
  });

  it('should not have hostBinding class activeStep when isActive is false', () => {
    component.isActive = false;
    fixture.detectChanges();
    
    const element = fixture.nativeElement;
    expect(element.classList.contains('activeStep')).toBe(false);
  });
});