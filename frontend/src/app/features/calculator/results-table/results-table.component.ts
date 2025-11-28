import { Component, Input, Output, EventEmitter, ChangeDetectionStrategy, OnChanges, SimpleChanges, TrackByFunction } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { TableData, SortConfig } from '../calculator.interfaces';
import { TableDataService } from '../table-data.service';

@Component({
  selector: 'app-results-table',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './results-table.component.html',
  styleUrls: ['./results-table.component.css'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class ResultsTableComponent implements OnChanges {
  hasValidData = false;
  @Input() tableData!: TableData;
  @Input() title!: string;
  @Output() sortChange = new EventEmitter<SortConfig>();

  sortedData: (string | number)[][] = [];
  filteredData: (string | number)[][] = [];
  searchTerm = '';
  currentSort: SortConfig = { column: '', direction: 'asc' };
  displayedColumns: string[] = [];
  paginationConfig = {
    pageIndex: 0,
    pageSize: 10,
    totalItems: 0
  };

  constructor(private tableDataService: TableDataService) {}

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['tableData'] && this.tableData) {
      this.displayedColumns = this.tableData.columns || [];
      this.updateSortedData();
    }
  }

  onSort(column: string): void {
    if (this.currentSort.column === column) {
      this.currentSort.direction = this.currentSort.direction === 'asc' ? 'desc' : 'asc';
    } else {
      this.currentSort = { column, direction: 'asc' };
    }
    
    this.sortChange.emit(this.currentSort);
    this.updateSortedData();
  }

  onSearch(): void {
    this.paginationConfig.pageIndex = 0; // Reset a primera página al buscar
    this.updateSortedData();
  }

  onPageChange(pageIndex: number | string): void {
    const numPageIndex = typeof pageIndex === 'string' ? parseInt(pageIndex, 10) : pageIndex;
    this.paginationConfig.pageIndex = numPageIndex;
    this.tableDataService.updatePagination({ pageIndex: numPageIndex });
  }

  onPageSizeChange(pageSize: number | string): void {
    const numPageSize = typeof pageSize === 'string' ? parseInt(pageSize, 10) : pageSize;
    this.paginationConfig.pageSize = numPageSize;
    this.paginationConfig.pageIndex = 0; // Reset a primera página
    this.updateSortedData();
  }

  private updateSortedData(): void {
    if (!this.tableData || !this.tableData.data || !Array.isArray(this.tableData.data)) {
      this.hasValidData = false;
      this.sortedData = [];
      this.filteredData = [];
      this.paginationConfig.totalItems = 0;
      return;
    }

    this.hasValidData = true;
    let data = [...this.tableData.data];
    
    // Aplicar búsqueda
    this.filteredData = this.tableDataService.filterData(data, this.searchTerm);
    
    // Aplicar sorting
    this.sortedData = this.tableDataService.applySorting(this.filteredData, this.currentSort);
    
    // Actualizar paginación local
    this.paginationConfig.totalItems = this.filteredData.length;
  }

  get paginatedData(): (string | number)[][] {
    if (!this.hasValidData || !this.sortedData.length) {
      return [];
    }
    return this.tableDataService.paginateData(
      this.sortedData,
      this.paginationConfig.pageIndex,
      this.paginationConfig.pageSize
    );
  }

  get totalPages(): number {
    return Math.ceil(this.paginationConfig.totalItems / this.paginationConfig.pageSize);
  }

  get startItem(): number {
    return this.paginationConfig.totalItems === 0 ? 0 :
      this.paginationConfig.pageIndex * this.paginationConfig.pageSize + 1;
  }

  get endItem(): number {
    const end = (this.paginationConfig.pageIndex + 1) * this.paginationConfig.pageSize;
    return Math.min(end, this.paginationConfig.totalItems);
  }

  getPageNumbers(): number[] {
    return Array.from({ length: this.totalPages }, (_, i) => i);
  }

  exportToCSV(): void {
    if (!this.hasValidData || !this.paginatedData.length || !this.displayedColumns.length) return;
    
    this.tableDataService.exportToCSV(
      this.paginatedData,
      this.displayedColumns,
      `${this.title.replace(/\s+/g, '_').toLowerCase()}_export`
    );
  }

  exportToExcel(): void {
    if (!this.hasValidData || !this.paginatedData.length || !this.displayedColumns.length) return;
    
    this.tableDataService.exportToExcel(
      this.paginatedData,
      this.displayedColumns,
      `${this.title.replace(/\s+/g, '_').toLowerCase()}_export`
    );
  }

  getSortIcon(column: string): string {
    if (this.currentSort.column !== column) return '↕️';
    return this.currentSort.direction === 'asc' ? '↑' : '↓';
  }

  trackByRow: TrackByFunction<(string | number)[]> = (index: number, row: (string | number)[]): string => {
    return row.join('|');
  };

  isNumericCell(cell: string | number): boolean {
    return !isNaN(Number(cell));
  }
}