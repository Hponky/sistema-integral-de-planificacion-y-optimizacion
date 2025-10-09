import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { ApiService } from 'src/app/core/services/api.service';
import { HttpErrorResponse } from '@angular/common/http';

@Component({
  selector: 'app-file-upload',
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule],
  templateUrl: './file-upload.component.html',
  styleUrls: ['./file-upload.component.css']
})
export class FileUploadComponent {
  selectedFile: File | null = null;
  uploadStatus: string = '';
  isDragging: boolean = false;
  // excelData: DemandData[] | null = null; // No se usará directamente ya que el backend no devuelve los datos del Excel en la carga

  constructor(private readonly apiService: ApiService) { }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      this.selectedFile = input.files; // Tomar el primer archivo
    } else {
      this.selectedFile = null;
    }
    this.uploadStatus = '';
    // this.excelData = null; // Limpiar datos anteriores al seleccionar un nuevo archivo
  }

  onDragOver(event: DragEvent): void {
    event.preventDefault();
    this.isDragging = true;
  }

  onDragLeave(event: DragEvent): void {
    event.preventDefault();
    this.isDragging = false;
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    this.isDragging = false;
    if (event.dataTransfer && event.dataTransfer.files.length > 0) {
      this.selectedFile = event.dataTransfer.files; // Tomar el primer archivo
    }
    this.uploadStatus = '';
    // this.excelData = null; // Limpiar datos anteriores al soltar un nuevo archivo
  }

  onUpload(): void {
    if (this.selectedFile) {
      this.uploadStatus = 'Cargando...';
      this.apiService.uploadFile(this.selectedFile).subscribe({
        next: (response: string) => { // La respuesta es un string del backend
          this.uploadStatus = `Archivo cargado exitosamente: ${response}`;
          console.log('Archivo cargado:', response);
          // Aquí podrías llamar a otro servicio para obtener los datos del Excel si el backend los expone en otro endpoint
        },
        error: (error: HttpErrorResponse) => {
          this.uploadStatus = `Error al cargar el archivo: ${error.message}`;
          console.error('Error al cargar el archivo:', error);
        }
      });
    } else {
      this.uploadStatus = 'Por favor, selecciona un archivo.';
    }
  }
}
