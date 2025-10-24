import { Injectable } from '@angular/core';
import { Observable, throwError, timer, of, EMPTY } from 'rxjs';
import { catchError, map, delay, expand, takeWhile, finalize, retry } from 'rxjs/operators';
import { HttpErrorResponse } from '@angular/common/http';
import { AuthenticationStateService, AuthenticationState } from './authentication-state.service';
import { AuthNavigationService } from './auth-navigation.service';

export enum AuthErrorType {
  NETWORK_ERROR = 'NETWORK_ERROR',
  SESSION_EXPIRED = 'SESSION_EXPIRED',
  UNAUTHORIZED = 'UNAUTHORIZED',
  SERVER_ERROR = 'SERVER_ERROR',
  VALIDATION_ERROR = 'VALIDATION_ERROR',
  UNKNOWN_ERROR = 'UNKNOWN_ERROR'
}

export interface AuthError {
  type: AuthErrorType;
  message: string;
  userFriendlyMessage: string;
  timestamp: Date;
  originalError?: any;
  retryable: boolean;
  maxRetries?: number;
}

export interface RetryConfig {
  maxRetries: number;
  backoffDelay: number;
  maxBackoffDelay: number;
  shouldRetry: (error: any) => boolean;
}

@Injectable({
  providedIn: 'root'
})
export class AuthErrorHandlerService {
  private readonly DEFAULT_RETRY_CONFIG: RetryConfig = {
    maxRetries: 3,
    backoffDelay: 1000,
    maxBackoffDelay: 10000,
    shouldRetry: (error: any) => {
      if (error && error.type && error.message && error.timestamp) {
        return error.retryable;
      }
      
      if (error instanceof HttpErrorResponse) {
        return error.status >= 500 || error.status === 0;
      }
      
      return false;
    }
  };

  constructor(
    private authenticationStateService: AuthenticationStateService,
    private authNavigationService: AuthNavigationService
  ) {}

  handleError(error: any, context?: string): Observable<never> {
    const authError = this.normalizeError(error, context);
    this.logError(authError);
    
    return this.handleAuthError(authError);
  }

  handleWithRetry<T>(
    operation: Observable<T>,
    retryConfig: Partial<RetryConfig> = {},
    context?: string
  ): Observable<T> {
    const config = { ...this.DEFAULT_RETRY_CONFIG, ...retryConfig };
    
    return operation.pipe(
      expand((result) => {
        if (result instanceof Error) {
          const authError = this.normalizeError(result, context);
          
          if (!config.shouldRetry(authError)) {
            return throwError(() => result);
          }
          
          const retryCount = (result as any).retryCount || 0;
          
          if (retryCount >= config.maxRetries) {
            return throwError(() => result);
          }
          
          this.logRetryAttempt(authError, retryCount + 1);
          
          const delay = Math.min(
            config.backoffDelay * Math.pow(2, retryCount),
            config.maxBackoffDelay
          );
          
          return timer(delay).pipe(
            map(() => {
              const errorWithRetryCount = result as any;
              errorWithRetryCount.retryCount = retryCount + 1;
              return errorWithRetryCount;
            })
          );
        }
        
        return EMPTY;
      }),
      takeWhile((result) => !(result instanceof Error)),
      catchError((error) => this.handleError(error, context))
    );
  }

  getUserFriendlyMessage(errorType: AuthErrorType): string {
    switch (errorType) {
      case AuthErrorType.NETWORK_ERROR:
        return 'No se pudo conectar con el servidor. Por favor, verifica tu conexión a internet.';
      case AuthErrorType.SESSION_EXPIRED:
        return 'Tu sesión ha expirado. Por favor, inicia sesión nuevamente.';
      case AuthErrorType.UNAUTHORIZED:
        return 'No tienes permisos para acceder a esta página.';
      case AuthErrorType.SERVER_ERROR:
        return 'El servidor está experimentando problemas. Por favor, intenta más tarde.';
      case AuthErrorType.VALIDATION_ERROR:
        return 'Los datos proporcionados no son válidos. Por favor, verifica e intenta nuevamente.';
      default:
        return 'Ha ocurrido un error inesperado. Por favor, intenta nuevamente.';
    }
  }

  private normalizeError(error: any, context?: string): AuthError {
    if (error && error.type && error.message && error.timestamp) {
      return error;
    }

    if (error instanceof HttpErrorResponse) {
      return this.normalizeHttpError(error, context);
    }

    return {
      type: AuthErrorType.UNKNOWN_ERROR,
      message: error?.message || 'Error desconocido',
      userFriendlyMessage: this.getUserFriendlyMessage(AuthErrorType.UNKNOWN_ERROR),
      timestamp: new Date(),
      originalError: error,
      retryable: false
    };
  }

  private normalizeHttpError(error: HttpErrorResponse, context?: string): AuthError {
    if (error.status === 401) {
      return {
        type: AuthErrorType.SESSION_EXPIRED,
        message: 'Sesión expirada o no autorizada',
        userFriendlyMessage: this.getUserFriendlyMessage(AuthErrorType.SESSION_EXPIRED),
        timestamp: new Date(),
        originalError: error,
        retryable: false
      };
    }

    if (error.status === 403) {
      return {
        type: AuthErrorType.UNAUTHORIZED,
        message: 'Acceso no autorizado',
        userFriendlyMessage: this.getUserFriendlyMessage(AuthErrorType.UNAUTHORIZED),
        timestamp: new Date(),
        originalError: error,
        retryable: false
      };
    }

    if (error.status === 400) {
      return {
        type: AuthErrorType.VALIDATION_ERROR,
        message: 'Error de validación',
        userFriendlyMessage: this.getUserFriendlyMessage(AuthErrorType.VALIDATION_ERROR),
        timestamp: new Date(),
        originalError: error,
        retryable: false
      };
    }

    if (error.status >= 500) {
      return {
        type: AuthErrorType.SERVER_ERROR,
        message: 'Error del servidor',
        userFriendlyMessage: this.getUserFriendlyMessage(AuthErrorType.SERVER_ERROR),
        timestamp: new Date(),
        originalError: error,
        retryable: true,
        maxRetries: 3
      };
    }

    if (error.status === 0) {
      return {
        type: AuthErrorType.NETWORK_ERROR,
        message: 'Error de conexión',
        userFriendlyMessage: this.getUserFriendlyMessage(AuthErrorType.NETWORK_ERROR),
        timestamp: new Date(),
        originalError: error,
        retryable: true,
        maxRetries: 2
      };
    }

    return {
      type: AuthErrorType.UNKNOWN_ERROR,
      message: `Error HTTP ${error.status}: ${error.message}`,
      userFriendlyMessage: this.getUserFriendlyMessage(AuthErrorType.UNKNOWN_ERROR),
      timestamp: new Date(),
      originalError: error,
      retryable: false
    };
  }

  private handleAuthError(error: AuthError): Observable<never> {
    switch (error.type) {
      case AuthErrorType.SESSION_EXPIRED:
      case AuthErrorType.UNAUTHORIZED:
        return this.handleAuthenticationError(error);
      
      case AuthErrorType.NETWORK_ERROR:
      case AuthErrorType.SERVER_ERROR:
        if (error.retryable) {
          return throwError(() => error);
        }
        break;
      
      default:
        break;
    }

    return throwError(() => error);
  }

  private handleAuthenticationError(error: AuthError): Observable<never> {
    this.authenticationStateService.setState(AuthenticationState.NOT_AUTHENTICATED).subscribe({
      next: () => {
        this.authNavigationService.navigateToLogin().subscribe({
          error: (navError) => {
            console.error('Error durante la navegación al login:', navError);
          }
        });
      },
      error: (stateError) => {
        console.error('Error al establecer estado de no autenticado:', stateError);
      }
    });

    return throwError(() => error);
  }

  private logError(error: AuthError): void {
    const logEntry = {
      timestamp: error.timestamp.toISOString(),
      type: error.type,
      message: error.message,
      userFriendlyMessage: error.userFriendlyMessage,
      retryable: error.retryable,
      originalError: error.originalError
    };

    console.group(`🔐 Authentication Error [${error.type}]`);
    console.error('Error details:', logEntry);
    console.trace('Stack trace');
    console.groupEnd();
  }

  private logRetryAttempt(error: AuthError, attemptNumber: number): void {
    console.warn(`🔄 Authentication retry attempt ${attemptNumber} for error [${error.type}]: ${error.message}`);
  }

  createAuthError(
    type: AuthErrorType,
    message: string,
    originalError?: any,
    retryable: boolean = false,
    maxRetries?: number
  ): AuthError {
    return {
      type,
      message,
      userFriendlyMessage: this.getUserFriendlyMessage(type),
      timestamp: new Date(),
      originalError,
      retryable,
      maxRetries
    };
  }

  private createAuthErrorFromError(error: any, context?: string): AuthError {
    return this.normalizeError(error, context);
  }
}