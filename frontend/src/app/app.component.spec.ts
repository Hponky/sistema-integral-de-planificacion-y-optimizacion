import { TestBed } from '@angular/core/testing';
import { AppComponent } from './app.component';
import { provideRouter } from '@angular/router';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { AuthService } from './core/services/auth.service';
import { ApiService } from './core/services/api.service';
import { AuthenticationStateService, AuthenticationState } from './core/services/authentication-state.service';
import { of } from 'rxjs';

describe('AppComponent', () => {
  let authServiceSpy: jasmine.SpyObj<AuthService>;
  let apiServiceSpy: jasmine.SpyObj<ApiService>;
  let authenticationStateServiceSpy: jasmine.SpyObj<AuthenticationStateService>;

  beforeEach(async () => {
    authServiceSpy = jasmine.createSpyObj('AuthService', ['logout']);
    apiServiceSpy = jasmine.createSpyObj('ApiService', ['getHealthCheck']);
    authenticationStateServiceSpy = jasmine.createSpyObj('AuthenticationStateService', ['setState']);
    authenticationStateServiceSpy.currentState$ = of(AuthenticationState.NOT_AUTHENTICATED);

    await TestBed.configureTestingModule({
      imports: [
        AppComponent,
        HttpClientTestingModule
      ],
      providers: [
        { provide: AuthService, useValue: authServiceSpy },
        { provide: ApiService, useValue: apiServiceSpy },
        { provide: AuthenticationStateService, useValue: authenticationStateServiceSpy },
        provideRouter([])
      ]
    }).compileComponents();
  });

  it('should create the app', () => {
    const fixture = TestBed.createComponent(AppComponent);
    const app = fixture.componentInstance;
    expect(app).toBeTruthy();
  });

  it(`should have the 'frontend' title`, () => {
    const fixture = TestBed.createComponent(AppComponent);
    const app = fixture.componentInstance;
    expect(app.title).toEqual('frontend');
  });

  it('should render title', () => {
    const fixture = TestBed.createComponent(AppComponent);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('h1')?.textContent).toContain('Hello, frontend');
  });

  it('should initialize authentication state on init', () => {
    authenticationStateServiceSpy.currentState$ = of(AuthenticationState.NOT_AUTHENTICATED);
    
    const fixture = TestBed.createComponent(AppComponent);
    fixture.detectChanges();
    
    expect(authenticationStateServiceSpy.currentState$).toHaveBeenCalled();
  });

  it('should call health check on init', () => {
    apiServiceSpy.getHealthCheck.and.returnValue(of({ status: 'healthy' }));
    
    const fixture = TestBed.createComponent(AppComponent);
    fixture.detectChanges();
    
    expect(apiServiceSpy.getHealthCheck).toHaveBeenCalled();
  });

  it('should handle logout correctly', () => {
    authServiceSpy.logout.and.returnValue(of({}));
    authenticationStateServiceSpy.setState.calls.reset();
    
    const fixture = TestBed.createComponent(AppComponent);
    const app = fixture.componentInstance;
    app.logout();
    
    expect(authServiceSpy.logout).toHaveBeenCalled();
    expect(authenticationStateServiceSpy.setState).toHaveBeenCalled();
  });
});
