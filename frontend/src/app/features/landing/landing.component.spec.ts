import { ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { provideRouter } from '@angular/router';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { LandingComponent } from './landing.component';
import { HeroComponent } from './sections/hero/hero.component';

describe('LandingComponent', () => {
  let component: LandingComponent;
  let fixture: ComponentFixture<LandingComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        LandingComponent,
        HeroComponent,
        NoopAnimationsModule,
        HttpClientTestingModule
      ],
      providers: [
        provideRouter([])
      ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(LandingComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should have the correct title', () => {
    expect(component.title).toBe('Sistema Integral de Planificación y Optimización');
  });

  it('should render the hero component', () => {
    const heroElement = fixture.debugElement.query(By.css('app-hero'));
    expect(heroElement).toBeTruthy();
  });

  it('should render the main title', () => {
    const titleElement = fixture.debugElement.query(By.css('h1'));
    expect(titleElement).toBeTruthy();
    expect(titleElement.nativeElement.textContent).toContain('Sistema Integral de Planificación y Optimización');
  });

  it('should render navigation links', () => {
    const navLinks = fixture.debugElement.queryAll(By.css('a'));
    expect(navLinks.length).toBeGreaterThan(0);
  });

  it('should have proper component structure', () => {
    const mainElement = fixture.debugElement.query(By.css('main.landing-container'));
    expect(mainElement).toBeTruthy();
    
    const heroSection = fixture.debugElement.query(By.css('app-hero'));
    expect(heroSection).toBeTruthy();
    
    const featuresSection = fixture.debugElement.query(By.css('.features-section'));
    expect(featuresSection).toBeTruthy();
    
    const benefitsSection = fixture.debugElement.query(By.css('.benefits-section'));
    expect(benefitsSection).toBeTruthy();
  });
});