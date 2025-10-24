import { ComponentFixture, TestBed } from '@angular/core/testing';
import { CommonModule } from '@angular/common';

import { ProgressComponent } from './progress.component';
import { ProgressStepComponent } from './progress-step.component';
import { ProgressHelperService } from '../services/progress-helper.service';

describe('ProgressComponent', () => {
  let component: ProgressComponent;
  let fixture: ComponentFixture<ProgressComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        CommonModule,
        ProgressComponent,
        ProgressStepComponent
      ],
      providers: [
        ProgressHelperService
      ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(ProgressComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize with default values', () => {
    expect(component.itemLength).toBe(0);
    expect(component.activeIndex).toBe(0);
    expect(component.itemProgressList).toEqual([]);
  });

  it('should set selectedIndex correctly', () => {
    component.selectedIndex = 2;
    expect(component.activeIndex).toBe(2);
  });
});