import { Component, inject, computed, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { SchedulingFacadeService } from '../scheduling-facade.service';
import type { Agent } from '../interfaces';

@Component({
  selector: 'app-agent-list',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './agent-list.component.html',
  styleUrls: ['./agent-list.component.css']
})
export class AgentListComponent {
  protected facade = inject(SchedulingFacadeService);
  protected allAgents = this.facade.agents;

  // Paginación
  currentPage = signal(1);
  itemsPerPage = signal(12);
  searchTerm = signal('');

  // Agentes filtrados por búsqueda
  filteredAgents = computed(() => {
    const agents = this.allAgents();
    const search = this.searchTerm().toLowerCase();

    if (!search) return agents;

    return agents.filter(agent =>
      agent.nombre.toLowerCase().includes(search) ||
      agent.identificacion?.toLowerCase().includes(search) ||
      agent.perfil?.toLowerCase().includes(search)
    );
  });

  // Total de páginas
  totalPages = computed(() => {
    return Math.ceil(this.filteredAgents().length / this.itemsPerPage());
  });

  // Agentes paginados
  paginatedAgents = computed(() => {
    const filtered = this.filteredAgents();
    const start = (this.currentPage() - 1) * this.itemsPerPage();
    const end = start + this.itemsPerPage();
    return filtered.slice(start, end);
  });

  // Array de números de página para mostrar
  pageNumbers = computed(() => {
    const total = this.totalPages();
    const current = this.currentPage();
    const pages: number[] = [];

    // Mostrar máximo 5 páginas
    let start = Math.max(1, current - 2);
    let end = Math.min(total, start + 4);

    // Ajustar si estamos cerca del final
    if (end - start < 4) {
      start = Math.max(1, end - 4);
    }

    for (let i = start; i <= end; i++) {
      pages.push(i);
    }

    return pages;
  });

  onSearchChange(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.searchTerm.set(input.value);
    this.currentPage.set(1); // Reset a primera página al buscar
  }

  goToPage(page: number): void {
    if (page >= 1 && page <= this.totalPages()) {
      this.currentPage.set(page);
    }
  }

  previousPage(): void {
    if (this.currentPage() > 1) {
      this.currentPage.set(this.currentPage() - 1);
    }
  }

  nextPage(): void {
    if (this.currentPage() < this.totalPages()) {
      this.currentPage.set(this.currentPage() + 1);
    }
  }

  changeItemsPerPage(items: number): void {
    this.itemsPerPage.set(items);
    this.currentPage.set(1);
  }
  // --- Selección de Agentes ---
  selectedAgentIds = signal<Set<string>>(new Set());

  isAgentSelected(id: string | undefined): boolean {
    if (!id) return false;
    return this.selectedAgentIds().has(id);
  }

  toggleSelection(id: string | undefined, event?: Event): void {
    if (!id) return;
    if (event) event.stopPropagation();

    const current = new Set(this.selectedAgentIds());
    if (current.has(id)) {
      current.delete(id);
    } else {
      current.add(id);
    }
    this.selectedAgentIds.set(current);
  }

  isAllSelected = computed(() => {
    const filtered = this.filteredAgents();
    if (filtered.length === 0) return false;
    const selected = this.selectedAgentIds();
    return filtered.every(a => a.identificacion && selected.has(a.identificacion));
  });

  toggleSelectAll(): void {
    const filtered = this.filteredAgents();
    const current = new Set(this.selectedAgentIds());

    if (this.isAllSelected()) {
      filtered.forEach(a => a.identificacion && current.delete(a.identificacion));
    } else {
      filtered.forEach(a => a.identificacion && current.add(a.identificacion));
    }
    this.selectedAgentIds.set(current);
  }

  exportSelected(): void {
    const selected = Array.from(this.selectedAgentIds());
    if (selected.length === 0) {
      alert('Por favor selecciona al menos un agente.');
      return;
    }

    this.facade.exportFilteredReport(selected);
  }

  clearSelection(): void {
    this.selectedAgentIds.set(new Set());
  }
}
