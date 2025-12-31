
import { Component, EventEmitter, Output, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { SchedulingRules } from '../interfaces';

@Component({
    selector: 'app-rules-configuration',
    standalone: true,
    imports: [CommonModule, FormsModule],
    templateUrl: './rules-configuration.component.html',
    styleUrls: ['./rules-configuration.component.css']
})
export class RulesConfigurationComponent {
    @Output() save = new EventEmitter<SchedulingRules>();
    @Output() close = new EventEmitter<void>();

    // Default Rules State
    rules = signal<SchedulingRules>({
        weeklyDayOff: true,
        maxSundays: 2,
        minRestHours: 12,
        nightDayAlternation: true,
        minShiftDuration: 4,
        maxShiftDuration: 9,
        enableBreaks: true,
        enablePVDs: true
    });

    onSave() {
        this.save.emit(this.rules());
    }

    onClose() {
        this.close.emit();
    }

    // Helpers to update signals from template (ngModel handles mutation, but signals are immutable-ish)
    // We can just bind to a mutable object copy or handle inputs.
    // Ideally with signals we use separate signals or a form group.
    // For simplicity, I'll use a getter/setter approach or just a plain object property if I wasn't using OnPush. 
    // Let's stick to simple property binding for now.

    // Actually, to keep it simple with ngModel and Signals:
    // We can unwrap the signal to a local object, modify it, and update signal on save?
    // Or just use a plain object property.

    config: SchedulingRules = {
        weeklyDayOff: true,
        maxSundays: 2,
        minRestHours: 12,
        nightDayAlternation: true,
        minShiftDuration: 4,
        maxShiftDuration: 9,
        enableBreaks: true,
        enablePVDs: true
    };
}
