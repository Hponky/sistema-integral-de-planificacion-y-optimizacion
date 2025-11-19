import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { AuthenticationStateService, AuthenticationState } from './authentication-state.service';
import { PLATFORM_ID } from '@angular/core';

describe('AuthenticationStateService', () => {
  let service: AuthenticationStateService;

  beforeEach(() => {
    const sessionStorageSpy = jasmine.createSpyObj('Storage', ['getItem', 'setItem', 'removeItem']);
    
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [
        { provide: PLATFORM_ID, useValue: 'browser' },
        {
          provide: Storage,
          useFactory: () => sessionStorageSpy
        }
      ]
    });
    
    sessionStorageSpy.getItem.and.returnValue(null);
    sessionStorageSpy.setItem.and.callFake(() => {});
    sessionStorageSpy.removeItem.and.callFake(() => {});
    
    service = TestBed.inject(AuthenticationStateService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should have initial state as NOT_AUTHENTICATED', () => {
    expect(service.getCurrentState()).toBe(AuthenticationState.NOT_AUTHENTICATED);
    expect(service.isChecking()).toBeFalsy();
    expect(service.isAuthenticated()).toBeFalsy();
    expect(service.isNotAuthenticated()).toBeTruthy();
  });

  it('should update state to AUTHENTICATED', (done) => {
    service.setState(AuthenticationState.AUTHENTICATED).subscribe({
      next: () => {
        expect(service.getCurrentState()).toBe(AuthenticationState.AUTHENTICATED);
        expect(service.isChecking()).toBeFalsy();
        expect(service.isAuthenticated()).toBeTruthy();
        expect(service.isNotAuthenticated()).toBeFalsy();
        done();
      },
      error: () => {
        fail('State update should not fail');
        done();
      }
    });
  });

  it('should update state to NOT_AUTHENTICATED', (done) => {
    service.setState(AuthenticationState.NOT_AUTHENTICATED).subscribe({
      next: () => {
        expect(service.getCurrentState()).toBe(AuthenticationState.NOT_AUTHENTICATED);
        expect(service.isChecking()).toBeFalsy();
        expect(service.isAuthenticated()).toBeFalsy();
        expect(service.isNotAuthenticated()).toBeTruthy();
        done();
      },
      error: () => {
        fail('State update should not fail');
        done();
      }
    });
  });

  it('should emit state changes through currentState$ observable', (done) => {
    let emissionCount = 0;
    let lastEmittedState: AuthenticationState | undefined;
    
    service.currentState$.subscribe(state => {
      emissionCount++;
      lastEmittedState = state;
      
      if (emissionCount === 1) {
        expect(state).toBe(AuthenticationState.NOT_AUTHENTICATED);
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

  it('should handle multiple state changes correctly', (done) => {
    let changeCount = 0;
    
    service.setState(AuthenticationState.AUTHENTICATED).subscribe({
      next: () => {
        changeCount++;
        if (changeCount === 1) {
          expect(service.getCurrentState()).toBe(AuthenticationState.AUTHENTICATED);
          
          service.setState(AuthenticationState.NOT_AUTHENTICATED).subscribe({
            next: () => {
              changeCount++;
              if (changeCount === 2) {
                expect(service.getCurrentState()).toBe(AuthenticationState.NOT_AUTHENTICATED);
                
                service.setState(AuthenticationState.CHECKING).subscribe({
                  next: () => {
                    changeCount++;
                    if (changeCount === 3) {
                      expect(service.getCurrentState()).toBe(AuthenticationState.CHECKING);
                      done();
                    }
                  },
                  error: () => {
                    fail('State update should not fail');
                    done();
                  }
                });
              }
            },
            error: () => {
              fail('State update should not fail');
              done();
            }
          });
        }
      },
      error: () => {
        fail('State update should not fail');
        done();
      }
    });
  });
});