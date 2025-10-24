import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Segment } from '../../calculator.interfaces';

@Component({
  selector: 'app-basic-data-step',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './basic-data-step.component.html',
  styleUrls: ['./basic-data-step.component.css']
})
export class BasicDataStepComponent {
  @Input() segments: Segment[] = [];
  @Input() selectedSegment: number | null = null;
  @Input() startDate: string = '';
  @Input() endDate: string = '';
  @Input() plantillaExcel: File | null = null;

  @Output() selectedSegmentChange = new EventEmitter<number | null>();
  @Output() startDateChange = new EventEmitter<string>();
  @Output() endDateChange = new EventEmitter<string>();
  @Output() plantillaExcelChange = new EventEmitter<File | null>();

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      this.plantillaExcelChange.emit(input.files[0]);
    } else {
      this.plantillaExcelChange.emit(null);
    }
  }
}