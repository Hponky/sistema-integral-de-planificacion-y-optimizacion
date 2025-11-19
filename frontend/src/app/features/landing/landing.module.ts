import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatGridListModule } from '@angular/material/grid-list';
import { MatIconModule } from '@angular/material/icon';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatTabsModule } from '@angular/material/tabs';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { LandingRoutingModule } from './landing-routing.module';

@NgModule({
  declarations: [
  ],
  imports: [
    CommonModule,

    BrowserAnimationsModule,
    MatButtonModule,
    MatCardModule,
    MatGridListModule,
    MatIconModule,
    MatToolbarModule,
    MatTabsModule,
    MatProgressSpinnerModule,
    LandingRoutingModule
  ],
  exports: [
  ]
})
export class LandingModule { }
