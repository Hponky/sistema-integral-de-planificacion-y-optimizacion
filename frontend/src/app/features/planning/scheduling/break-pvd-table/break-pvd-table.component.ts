
import { Component, inject, computed, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { SchedulingFacadeService } from '../scheduling-facade.service';
import { ModalComponent } from '../../../../shared/components/modal/modal.component';

@Component({
    selector: 'app-break-pvd-table',
    standalone: true,
    imports: [CommonModule, FormsModule, ModalComponent],
    templateUrl: './break-pvd-table.component.html',
    styleUrls: ['./break-pvd-table.component.css']
})
export class BreakPvdTableComponent {
    facade = inject(SchedulingFacadeService);

    data = computed(() => this.facade.breakPvdData());

    searchTerm = signal('');
    isEditModalOpen = signal(false);
    selectedRow = signal<any>(null);

    // Form fields for editing
    editForm = signal<any>({
        inicio_descanso: '',
        fin_descanso: '',
        pvds: new Array(10).fill('')
    });

    filteredRows = computed(() => {
        const term = this.searchTerm().toLowerCase();
        const rows = this.data().tableData;
        if (!term) return rows;
        return rows.filter(row =>
            row.nombre.toLowerCase().includes(term) ||
            row.dni.toLowerCase().includes(term) ||
            row.fecha.includes(term) ||
            row.turno.includes(term)
        );
    });

    onSearch(event: any) {
        this.searchTerm.set(event.target.value);
    }

    generateActivities() {
        this.facade.recalculate();
    }

    onEdit(row: any) {
        this.selectedRow.set(row);
        const pvds = [];
        for (let i = 1; i <= 10; i++) {
            pvds.push(row[`pvd${i}`] || '');
        }
        this.editForm.set({
            inicio_descanso: row.inicio_descanso,
            fin_descanso: row.fin_descanso,
            pvds: pvds
        });
        this.isEditModalOpen.set(true);
    }

    closeEditModal() {
        this.isEditModalOpen.set(false);
        this.selectedRow.set(null);
    }

    async saveEdit() {
        const row = this.selectedRow();
        const form = this.editForm();
        if (!row) return;

        const manualActivities: any[] = [];

        // Add Break if times are provided
        if (form.inicio_descanso && form.fin_descanso) {
            manualActivities.push({
                type: 'BREAK',
                startStr: form.inicio_descanso,
                endStr: form.fin_descanso
            });
        }

        // Add PVDs
        form.pvds.forEach((pvdTime: string) => {
            if (pvdTime) {
                // PVDs are usually 5 mins
                const [h, m] = pvdTime.split(':').map(Number);
                const endM = (m + 5);
                const endH = h + Math.floor(endM / 60);
                const finalM = endM % 60;
                const endStr = `${endH.toString().padStart(2, '0')}:${finalM.toString().padStart(2, '0')}`;

                manualActivities.push({
                    type: 'PVD',
                    startStr: pvdTime,
                    endStr: endStr
                });
            }
        });

        await this.facade.updateActivities(row.agentId, row.fecha, manualActivities);
        this.closeEditModal();
    }
}
