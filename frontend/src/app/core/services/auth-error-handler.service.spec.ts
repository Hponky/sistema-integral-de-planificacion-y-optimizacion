import { TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';
import { tap } from 'rxjs/operators';
import { HttpErrorResponse } from '@angular/common/http';
import { AuthErrorHandlerService, AuthErrorType, AuthError, RetryConfig } from './auth-error-handler.service';
import { AuthenticationStateService, AuthenticationState } from './authentication-state.service';
import { AuthNavigationService } from './auth-navigation.service';

describe('AuthErrorHandlerService', () => {
  let service: AuthErrorHandlerService;
  let authenticationStateServiceSpy: jasmine.SpyObj<AuthenticationStateService>;
  let authNavigationServiceSpy: jasmine.SpyObj<AuthNavigationService>;

  beforeEach(() => {
    const authenticationStateSpy = jasmine.createSpyObj('AuthenticationStateService', ['setState']);
    const authNavigationSpy = jasmine.createSpyObj('AuthNavigationService', ['navigateToLanding']);

    TestBed.configureTestingModule({
      providers: [
        AuthErrorHandlerService,
        { provide: AuthenticationStateService, useValue: authenticationStateSpy },
        { provide: AuthNavigationService, useValue: authNavigationSpy }
      ]
    });

    service = TestBed.inject(AuthErrorHandlerService);
    authenticationStateServiceSpy = TestBed.inject(AuthenticationStateService) as jasmine.SpyObj<AuthenticationStateService>;
    authNavigationServiceSpy = TestBed.inject(AuthNavigationService) as jasmine.SpyObj<AuthNavigationService>;
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('getUserFriendlyMessage', () => {
    it('should return appropriate messages for each error type', () => {
      expect(service.getUserFriendlyMessage(AuthErrorType.NETWORK_ERROR))
        .toBe('No se pudo conectar con el servidor. Por favor, verifica tu conexión a internet.');
      
      expect(service.getUserFriendlyMessage(AuthErrorType.SESSION_EXPIRED))
        .toBe('Tu sesión ha expirado. Por favor, inicia sesión nuevamente.');
      
      expect(service.getUserFriendlyMessage(AuthErrorType.UNAUTHORIZED))
        .toBe('No tienes permisos para acceder a esta página.');
      
      expect(service.getUserFriendlyMessage(AuthErrorType.SERVER_ERROR))
        .toBe('El servidor está experimentando problemas. Por favor, intenta más tarde.');
      
      expect(service.getUserFriendlyMessage(AuthErrorType.VALIDATION_ERROR))
        .toBe('Los datos proporcionados no son válidos. Por favor, verifica e intenta nuevamente.');
      
      expect(service.getUserFriendlyMessage(AuthErrorType.UNKNOWN_ERROR))
        .toBe('Ha ocurrido un error inesperado. Por favor, intenta nuevamente.');
    });
  });

  describe('createAuthError', () => {
    it('should create a properly formatted AuthError', () => {
      const originalError = new Error('Test error');
      const authError = service.createAuthError(
        AuthErrorType.NETWORK_ERROR,
        'Network connection failed',
        originalError,
        true,
        3
      );

      expect(authError.type).toBe(AuthErrorType.NETWORK_ERROR);
      expect(authError.message).toBe('Network connection failed');
      expect(authError.userFriendlyMessage).toBe(service.getUserFriendlyMessage(AuthErrorType.NETWORK_ERROR));
      expect(authError.originalError).toBe(originalError);
      expect(authError.retryable).toBe(true);
      expect(authError.maxRetries).toBe(3);
      expect(authError.timestamp).toBeInstanceOf(Date);
    });

    it('should create AuthError with default values', () => {
      const authError = service.createAuthError(
        AuthErrorType.VALIDATION_ERROR,
        'Invalid input'
      );

      expect(authError.type).toBe(AuthErrorType.VALIDATION_ERROR);
      expect(authError.message).toBe('Invalid input');
      expect(authError.retryable).toBe(false);
      expect(authError.maxRetries).toBeUndefined();
    });
  });

  describe('normalizeError', () => {
    it('should return the same AuthError if input is already an AuthError', () => {
      const originalAuthError: AuthError = {
        type: AuthErrorType.SESSION_EXPIRED,
        message: 'Session expired',
        userFriendlyMessage: 'Test message',
        timestamp: new Date(),
        retryable: false
      };

      const normalizedError = (service as any).normalizeError(originalAuthError);

      expect(normalizedError).toBe(originalAuthError);
    });

    it('should normalize HttpErrorResponse with 401 status', () => {
      const httpError = new HttpErrorResponse({
        status: 401,
        statusText: 'Unauthorized',
        url: '/api/test'
      });

      const normalizedError = (service as any).normalizeError(httpError);

      expect(normalizedError.type).toBe(AuthErrorType.SESSION_EXPIRED);
      expect(normalizedError.retryable).toBe(false);
      expect(normalizedError.originalError).toBe(httpError);
    });

    it('should normalize HttpErrorResponse with 403 status', () => {
      const httpError = new HttpErrorResponse({
        status: 403,
        statusText: 'Forbidden',
        url: '/api/test'
      });

      const normalizedError = (service as any).normalizeError(httpError);

      expect(normalizedError.type).toBe(AuthErrorType.UNAUTHORIZED);
      expect(normalizedError.retryable).toBe(false);
    });

    it('should normalize HttpErrorResponse with 400 status', () => {
      const httpError = new HttpErrorResponse({
        status: 400,
        statusText: 'Bad Request',
        url: '/api/test'
      });

      const normalizedError = (service as any).normalizeError(httpError);

      expect(normalizedError.type).toBe(AuthErrorType.VALIDATION_ERROR);
      expect(normalizedError.retryable).toBe(false);
    });

    it('should normalize HttpErrorResponse with 500 status', () => {
      const httpError = new HttpErrorResponse({
        status: 500,
        statusText: 'Internal Server Error',
        url: '/api/test'
      });

      const normalizedError = (service as any).normalizeError(httpError);

      expect(normalizedError.type).toBe(AuthErrorType.SERVER_ERROR);
      expect(normalizedError.retryable).toBe(true);
      expect(normalizedError.maxRetries).toBe(3);
    });

    it('should normalize HttpErrorResponse with 0 status (network error)', () => {
      const httpError = new HttpErrorResponse({
        status: 0,
        statusText: 'Unknown Error',
        url: '/api/test'
      });

      const normalizedError = (service as any).normalizeError(httpError);

      expect(normalizedError.type).toBe(AuthErrorType.NETWORK_ERROR);
      expect(normalizedError.retryable).toBe(true);
      expect(normalizedError.maxRetries).toBe(2);
    });

    it('should normalize generic Error as UNKNOWN_ERROR', () => {
      const genericError = new Error('Something went wrong');

      const normalizedError = (service as any).normalizeError(genericError);

      expect(normalizedError.type).toBe(AuthErrorType.UNKNOWN_ERROR);
      expect(normalizedError.message).toBe('Something went wrong');
      expect(normalizedError.retryable).toBe(false);
    });
  });

  describe('handleError', () => {
    it('should handle authentication errors by setting state and navigating to login', () => {
      authenticationStateServiceSpy.setState.and.returnValue(of(AuthenticationState.NOT_AUTHENTICATED));
      authNavigationServiceSpy.navigateToLogin.and.returnValue(of(true));

      const authError: AuthError = {
        type: AuthErrorType.SESSION_EXPIRED,
        message: 'Session expired',
        userFriendlyMessage: 'Test message',
        timestamp: new Date(),
        retryable: false
      };

      service.handleError(authError).subscribe({
        error: (error) => {
          expect(error).toBe(authError);
          expect(authenticationStateServiceSpy.setState).toHaveBeenCalledWith(AuthenticationState.NOT_AUTHENTICATED);
          expect(authNavigationServiceSpy.navigateToLogin).toHaveBeenCalled();
        }
      });
    });

    it('should handle retryable errors by throwing them', () => {
      const authError: AuthError = {
        type: AuthErrorType.NETWORK_ERROR,
        message: 'Network error',
        userFriendlyMessage: 'Test message',
        timestamp: new Date(),
        retryable: true
      };

      service.handleError(authError).subscribe({
        error: (error) => {
          expect(error).toBe(authError);
        }
      });
    });
  });

  describe('handleWithRetry', () => {
    it('should retry operation on retryable errors', (done) => {
      const retryConfig: Partial<RetryConfig> = {
        maxRetries: 2,
        backoffDelay: 10
      };

      let attemptCount = 0;
      const operation$ = throwError(() => new Error('Network error')).pipe(
        tap(() => attemptCount++)
      );

      service.handleWithRetry(operation$, retryConfig).subscribe({
        error: () => {
          expect(attemptCount).toBe(3); // Initial attempt + 2 retries
          done();
        }
      });
    });

    it('should not retry operation on non-retryable errors', (done) => {
      const retryConfig: Partial<RetryConfig> = {
        maxRetries: 2,
        backoffDelay: 10
      };

      let attemptCount = 0;
      const httpError = new HttpErrorResponse({ status: 401 });
      const operation$ = throwError(() => httpError).pipe(
        tap(() => attemptCount++)
      );

      service.handleWithRetry(operation$, retryConfig).subscribe({
        error: () => {
          expect(attemptCount).toBe(1); // Only initial attempt, no retries
          done();
        }
      });
    });

    it('should succeed on successful operation', (done) => {
      const retryConfig: Partial<RetryConfig> = {
        maxRetries: 2,
        backoffDelay: 10
      };

      const operation$ = of('success');

      service.handleWithRetry(operation$, retryConfig).subscribe({
        next: (result) => {
          expect(result).toBe('success');
          done();
        }
      });
    });
  });
});