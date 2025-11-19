import { ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { Router } from '@angular/router';
import { HeroComponent } from './hero.component';
import axe from 'axe-core';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { AuthService } from '../../../../core/services/auth.service';

describe('HeroComponent', () => {
  let component: HeroComponent;
  let fixture: ComponentFixture<HeroComponent>;
  let mockRouter: jasmine.SpyObj<Router>;

  beforeEach(async () => {
    mockRouter = jasmine.createSpyObj('Router', ['navigate']);
    (mockRouter.navigate as jasmine.Spy).and.returnValue(Promise.resolve(true));

    await TestBed.configureTestingModule({
      imports: [HeroComponent, NoopAnimationsModule, HttpClientTestingModule],
      providers: [
        { provide: Router, useValue: mockRouter },
        { provide: AuthService, useValue: { isAuthenticated: () => false } }
      ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(HeroComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should have proper component structure', () => {
    const heroSection = fixture.debugElement.query(By.css('.hero-section'));
    const heroContent = fixture.debugElement.query(By.css('.hero-content'));
    const heroTitle = fixture.debugElement.query(By.css('.hero-title'));
    const heroSubtitle = fixture.debugElement.query(By.css('.hero-subtitle'));
    const heroDescription = fixture.debugElement.query(By.css('.hero-description'));
    const heroButton = fixture.debugElement.query(By.css('.hero-cta'));

    expect(heroSection).toBeTruthy();
    expect(heroContent).toBeTruthy();
    expect(heroTitle).toBeTruthy();
    expect(heroSubtitle).toBeTruthy();
    expect(heroDescription).toBeTruthy();
    expect(heroButton).toBeTruthy();
  });

  it('should display correct content', () => {
    const heroTitle = fixture.debugElement.query(By.css('.hero-title'));
    const heroSubtitle = fixture.debugElement.query(By.css('.hero-subtitle'));
    const heroDescription = fixture.debugElement.query(By.css('.hero-description'));
    const heroButton = fixture.debugElement.query(By.css('.hero-cta'));

    expect(heroTitle.nativeElement.textContent).toContain('Sistema Integral de Planificación y Optimización');
    expect(heroSubtitle.nativeElement.textContent).toContain('Optimiza tus recursos con cálculos Erlang precisos');
    expect(heroDescription.nativeElement.textContent).toContain('Herramienta avanzada para dimensionamiento de personal');
    expect(heroButton.nativeElement.textContent).toContain('Comenzar ahora');
  });

  it('should navigate to login when CTA button is clicked', () => {
    const heroButton = fixture.debugElement.query(By.css('.hero-cta'));
    heroButton.nativeElement.click();
    
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/login']);
  });

  it('should be accessible', async () => {
    const results = await axe.run(fixture.nativeElement);
    expect(results.violations.length).toBe(0);
  });
});
