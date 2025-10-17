/**
 * ===================================
 * MÓDULO COMPARTIDO PRINCIPAL - SIPO
 * ===================================
 *
 * Este módulo exporta todos los componentes y módulos
 * compartidos utilizados en la aplicación.
 */

import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MaterialModule } from './material.module';

@NgModule({
  declarations: [],
  imports: [
    CommonModule,
    MaterialModule
  ],
  exports: [
    CommonModule,
    MaterialModule
  ]
})
export class SharedModule { }