import { TestBed } from '@angular/core/testing';
import { ProgressHelperService } from './progress-helper.service';

describe('ProgressHelperService', () => {
  let service: ProgressHelperService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(ProgressHelperService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should have eventHelper property initialized as Subject', () => {
    expect(service.eventHelper).toBeDefined();
    expect(service.eventHelper.next).toBeDefined();
    expect(typeof service.eventHelper.next).toBe('function');
  });

  it('should emit values through eventHelper', () => {
    const testValue = { prev: true, next: false };
    let emittedValue: { prev: boolean; next: boolean } | undefined;

    service.eventHelper.subscribe(value => {
      emittedValue = value;
    });

    service.eventHelper.next(testValue);

    expect(emittedValue).toEqual(testValue);
  });

  it('should handle multiple subscribers', () => {
    const testValue = { prev: false, next: true };
    const emittedValues: { prev: boolean; next: boolean }[] = [];

    service.eventHelper.subscribe(value => {
      emittedValues.push(value);
    });

    service.eventHelper.subscribe(value => {
      emittedValues.push(value);
    });

    service.eventHelper.next(testValue);

    expect(emittedValues.length).toBe(2);
    expect(emittedValues[0]).toEqual(testValue);
    expect(emittedValues[1]).toEqual(testValue);
  });

  it('should handle different event types', () => {
    const nextEvent = { prev: false, next: true };
    const prevEvent = { prev: true, next: false };
    const bothEvent = { prev: true, next: true };
    const noneEvent = { prev: false, next: false };

    const emittedValues: { prev: boolean; next: boolean }[] = [];

    service.eventHelper.subscribe(value => {
      emittedValues.push(value);
    });

    service.eventHelper.next(nextEvent);
    service.eventHelper.next(prevEvent);
    service.eventHelper.next(bothEvent);
    service.eventHelper.next(noneEvent);

    expect(emittedValues).toEqual([nextEvent, prevEvent, bothEvent, noneEvent]);
  });
});