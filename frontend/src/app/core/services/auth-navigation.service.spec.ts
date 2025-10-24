import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { of, throwError, timeout } from 'rxjs';
import { AuthNavigationService, NavigationError } from './auth-navigation.service';
import { AuthenticationStateService, AuthenticationState } from './authentication-state.service';

describe('AuthNavigationService', () => {
  let service: AuthNavigationService;
  let mockRouter: jasmine.SpyObj<Router>;
  let mockAuthenticationStateService: jasmine.SpyObj<AuthenticationStateService>;

  beforeEach(() => {
    const routerSpy = jasmine.createSpyObj('Router', ['navigate']);
    const authStateSpy = jasmine.createSpyObj('AuthenticationStateService', ['setState']);

    TestBed.configureTestingModule({
      providers: [
        AuthNavigationService,
        { provide: Router, useValue: routerSpy },
        { provide: AuthenticationStateService, useValue: authStateSpy }
      ]
    });

    service = TestBed.inject(AuthNavigationService);
    mockRouter = TestBed.inject(Router) as jasmine.SpyObj<Router>;
    mockAuthenticationStateService = TestBed.inject(AuthenticationStateService) as jasmine.SpyObj<AuthenticationStateService>;
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('navigateToLogin', () => {
    it('should navigate to login route successfully', () => {
      mockRouter.navigate.and.returnValue(Promise.resolve(true));
      
      service.navigateToLogin().subscribe(result => {
        expect(result).toBe(true);
        expect(mockRouter.navigate).toHaveBeenCalledWith(['/login']);
      });
    });

    it('should handle navigation errors', () => {
      mockRouter.navigate.and.returnValue(Promise.reject(new Error('Navigation failed')));
      
      service.navigateToLogin().subscribe({
        next: () => fail('Expected error'),
        error: (error) => {
          expect(error).toBeDefined();
          expect(mockRouter.navigate).toHaveBeenCalledWith(['/login']);
        }
      });
    });
  });

  describe('navigateToDashboard', () => {
    it('should navigate to calculator route successfully', () => {
      mockRouter.navigate.and.returnValue(Promise.resolve(true));
      
      service.navigateToDashboard().subscribe(result => {
        expect(result).toBe(true);
        expect(mockRouter.navigate).toHaveBeenCalledWith(['/calculator']);
      });
    });

    it('should handle navigation errors', () => {
      mockRouter.navigate.and.returnValue(Promise.reject(new Error('Navigation failed')));
      
      service.navigateToDashboard().subscribe({
        next: () => fail('Expected error'),
        error: (error) => {
          expect(error).toBeDefined();
          expect(mockRouter.navigate).toHaveBeenCalledWith(['/calculator']);
        }
      });
    });
  });

  describe('navigateToHome', () => {
    it('should navigate to home route successfully', () => {
      mockRouter.navigate.and.returnValue(Promise.resolve(true));
      
      service.navigateToHome().subscribe(result => {
        expect(result).toBe(true);
        expect(mockRouter.navigate).toHaveBeenCalledWith(['/']);
      });
    });

    it('should handle navigation errors', () => {
      mockRouter.navigate.and.returnValue(Promise.reject(new Error('Navigation failed')));
      
      service.navigateToHome().subscribe({
        next: () => fail('Expected error'),
        error: (error) => {
          expect(error).toBeDefined();
          expect(mockRouter.navigate).toHaveBeenCalledWith(['/']);
        }
      });
    });
  });

  describe('handleAuthenticationError', () => {
    it('should set authentication state to NOT_AUTHENTICATED and navigate to login', () => {
      mockAuthenticationStateService.setState.and.returnValue(of(AuthenticationState.NOT_AUTHENTICATED));
      mockRouter.navigate.and.returnValue(Promise.resolve(true));
      
      service.handleAuthenticationError().subscribe(result => {
        expect(result).toBe(true);
        expect(mockAuthenticationStateService.setState).toHaveBeenCalledWith(AuthenticationState.NOT_AUTHENTICATED);
        expect(mockRouter.navigate).toHaveBeenCalledWith(['/login']);
      });
    });

    it('should handle authentication state setting failure', () => {
      mockAuthenticationStateService.setState.and.returnValue(throwError(() => new Error('State change failed')));
      mockRouter.navigate.and.returnValue(Promise.resolve(true));
      
      service.handleAuthenticationError().subscribe(result => {
        expect(result).toBe(true);
        expect(mockRouter.navigate).toHaveBeenCalledWith(['/login']);
      });
    });

    it('should handle navigation timeout', () => {
      mockAuthenticationStateService.setState.and.returnValue(of(AuthenticationState.AUTHENTICATED));
      mockRouter.navigate.and.returnValue(new Promise(() => {})); // Never resolves
      
      service.handleAuthenticationError().pipe(
        timeout(100) // Short timeout for test
      ).subscribe({
        next: () => fail('Expected timeout'),
        error: () => {
          expect(mockAuthenticationStateService.setState).toHaveBeenCalledWith(AuthenticationState.NOT_AUTHENTICATED);
        }
      });
    });
  });

  describe('handleSuccessfulAuthentication', () => {
    it('should set authentication state to AUTHENTICATED and navigate to dashboard', () => {
      mockAuthenticationStateService.setState.and.returnValue(of(AuthenticationState.NOT_AUTHENTICATED));
      mockRouter.navigate.and.returnValue(Promise.resolve(true));
      
      service.handleSuccessfulAuthentication().subscribe(result => {
        expect(result).toBe(true);
        expect(mockAuthenticationStateService.setState).toHaveBeenCalledWith(AuthenticationState.AUTHENTICATED);
        expect(mockRouter.navigate).toHaveBeenCalledWith(['/calculator']);
      });
    });

    it('should handle authentication state setting failure', () => {
      mockAuthenticationStateService.setState.and.returnValue(throwError(() => new Error('State change failed')));
      mockRouter.navigate.and.returnValue(Promise.resolve(true));
      
      service.handleSuccessfulAuthentication().subscribe(result => {
        expect(result).toBe(true);
        expect(mockRouter.navigate).toHaveBeenCalledWith(['/calculator']);
      });
    });
  });

  describe('handleUnauthorizedAccess', () => {
    it('should set authentication state to NOT_AUTHENTICATED and navigate to login', () => {
      mockAuthenticationStateService.setState.and.returnValue(of(AuthenticationState.NOT_AUTHENTICATED));
      mockRouter.navigate.and.returnValue(Promise.resolve(true));
      
      service.handleUnauthorizedAccess().subscribe(result => {
        expect(result).toBe(true);
        expect(mockAuthenticationStateService.setState).toHaveBeenCalledWith(AuthenticationState.NOT_AUTHENTICATED);
        expect(mockRouter.navigate).toHaveBeenCalledWith(['/login']);
      });
    });

    it('should handle authentication state setting failure', () => {
      mockAuthenticationStateService.setState.and.returnValue(throwError(() => new Error('State change failed')));
      mockRouter.navigate.and.returnValue(Promise.resolve(true));
      
      service.handleUnauthorizedAccess().subscribe(result => {
        expect(result).toBe(true);
        expect(mockRouter.navigate).toHaveBeenCalledWith(['/login']);
      });
    });
  });

  describe('handleSessionExpiry', () => {
    it('should set authentication state to NOT_AUTHENTICATED and navigate to login', () => {
      mockAuthenticationStateService.setState.and.returnValue(of(AuthenticationState.NOT_AUTHENTICATED));
      mockRouter.navigate.and.returnValue(Promise.resolve(true));
      
      service.handleSessionExpiry().subscribe(result => {
        expect(result).toBe(true);
        expect(mockAuthenticationStateService.setState).toHaveBeenCalledWith(AuthenticationState.NOT_AUTHENTICATED);
        expect(mockRouter.navigate).toHaveBeenCalledWith(['/login']);
      });
    });

    it('should handle authentication state setting failure', () => {
      mockAuthenticationStateService.setState.and.returnValue(throwError(() => new Error('State change failed')));
      mockRouter.navigate.and.returnValue(Promise.resolve(true));
      
      service.handleSessionExpiry().subscribe(result => {
        expect(result).toBe(true);
        expect(mockRouter.navigate).toHaveBeenCalledWith(['/login']);
      });
    });
  });

  describe('error handling', () => {
    it('should emit navigation errors through error$ observable', () => {
      const testError = new Error('Test navigation error');
      mockRouter.navigate.and.returnValue(Promise.reject(testError));
      
      let emittedError: NavigationError | null = null;
      service.error$.subscribe(error => {
        emittedError = error;
      });
      
      service.navigateToLogin().subscribe({
        next: () => fail('Expected error'),
        error: () => {
          expect(emittedError).toBeTruthy();
          expect(emittedError?.message).toContain('Navigation error for login');
          expect(emittedError?.targetRoute).toEqual(['/login']);
          expect(emittedError?.originalError).toBe(testError);
        }
      });
    });

    it('should getCurrentError return the current error', () => {
      const testError = new Error('Test navigation error');
      mockRouter.navigate.and.returnValue(Promise.reject(testError));
      
      service.navigateToLogin().subscribe({
        next: () => fail('Expected error'),
        error: () => {
          const currentError = service.getCurrentError();
          expect(currentError).toBeTruthy();
          expect(currentError?.message).toContain('Navigation error for login');
        }
      });
    });

    it('should clearError remove the current error', () => {
      const testError = new Error('Test navigation error');
      mockRouter.navigate.and.returnValue(Promise.reject(testError));
      
      service.navigateToLogin().subscribe({
        next: () => fail('Expected error'),
        error: () => {
          expect(service.getCurrentError()).toBeTruthy();
          service.clearError();
          expect(service.getCurrentError()).toBeNull();
        }
      });
    });
  });
});