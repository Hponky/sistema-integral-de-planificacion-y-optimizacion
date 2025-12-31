import { Injectable, NgZone, PLATFORM_ID, Inject } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { AuthService } from './auth.service';
import { fromEvent, merge, Subscription, timer } from 'rxjs';
import { switchMap, tap } from 'rxjs/operators';

@Injectable({
    providedIn: 'root'
})
export class SessionInactivityService {
    private readonly INACTIVITY_TIME = 30 * 60 * 1000; // 30 minutes
    private activitySubscription?: Subscription;
    private isBrowser: boolean;

    constructor(
        private authService: AuthService,
        private ngZone: NgZone,
        @Inject(PLATFORM_ID) platformId: Object
    ) {
        this.isBrowser = isPlatformBrowser(platformId);
    }

    startTracking(): void {
        if (!this.isBrowser) return;

        this.stopTracking();

        this.ngZone.runOutsideAngular(() => {
            const activityEvents$ = merge(
                fromEvent(window, 'mousemove'),
                fromEvent(window, 'keydown'),
                fromEvent(window, 'click'),
                fromEvent(window, 'scroll'),
                fromEvent(window, 'touchstart')
            );

            this.activitySubscription = activityEvents$
                .pipe(
                    // Reset timer on every activity
                    switchMap(() => timer(this.INACTIVITY_TIME)),
                    // When timer expires
                    tap(() => {
                        this.ngZone.run(() => {
                            if (this.authService.isAuthenticated()) {
                                console.log('User inactive (Session remains indeterminate).');
                                // this.authService.logout();
                                // window.location.reload();
                            }
                        });
                    })
                )
                .subscribe();
        });
    }

    stopTracking(): void {
        if (this.activitySubscription) {
            this.activitySubscription.unsubscribe();
        }
    }
}
