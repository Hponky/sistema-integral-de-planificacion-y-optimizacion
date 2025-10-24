import { TestBed } from '@angular/core/testing';
import { AuthenticationStateService, AuthenticationState } from './authentication-state.service';

describe('AuthenticationStateService', () => {
  let service: AuthenticationStateService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(AuthenticationStateService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should have initial state as CHECKING', () => {
    expect(service.getCurrentState()).toBe(AuthenticationState.CHECKING);
    expect(service.isChecking()).toBeTrue();
    expect(service.isAuthenticated()).toBeFalse();
    expect(service.isNotAuthenticated()).toBeFalse();
  });

  it('should update state to AUTHENTICATED', () => {
    service.setState(AuthenticationState.AUTHENTICATED);
    
    expect(service.getCurrentState()).toBe(AuthenticationState.AUTHENTICATED);
    expect(service.isChecking()).toBeFalse();
    expect(service.isAuthenticated()).toBeTrue();
    expect(service.isNotAuthenticated()).toBeFalse();
  });

  it('should update state to NOT_AUTHENTICATED', () => {
    service.setState(AuthenticationState.NOT_AUTHENTICATED);
    
    expect(service.getCurrentState()).toBe(AuthenticationState.NOT_AUTHENTICATED);
    expect(service.isChecking()).toBeFalse();
    expect(service.isAuthenticated()).toBeFalse();
    expect(service.isNotAuthenticated()).toBeTrue();
  });

  it('should emit state changes through currentState$ observable', (done) => {
    let emissionCount = 0;
    let lastEmittedState: AuthenticationState | undefined;
    
    service.currentState$.subscribe(state => {
      emissionCount++;
      lastEmittedState = state;
      
      if (emissionCount === 1) {
        expect(state).toBe(AuthenticationState.CHECKING);
      } else if (emissionCount === 2) {
        expect(state).toBe(AuthenticationState.AUTHENTICATED);
        service.setState(AuthenticationState.NOT_AUTHENTICATED);
      } else if (emissionCount === 3) {
        expect(state).toBe(AuthenticationState.NOT_AUTHENTICATED);
        done();
      }
    });
    
    service.setState(AuthenticationState.AUTHENTICATED);
  });

  it('should handle multiple state changes correctly', () => {
    service.setState(AuthenticationState.AUTHENTICATED);
    expect(service.getCurrentState()).toBe(AuthenticationState.AUTHENTICATED);
    
    service.setState(AuthenticationState.NOT_AUTHENTICATED);
    expect(service.getCurrentState()).toBe(AuthenticationState.NOT_AUTHENTICATED);
    
    service.setState(AuthenticationState.CHECKING);
    expect(service.getCurrentState()).toBe(AuthenticationState.CHECKING);
  });
});