import { Component, EventEmitter, Output, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { HttpErrorResponse } from '@angular/common/http';
import { MaterialModule } from '../../../shared/material.module';
import { MatSnackBar } from '@angular/material/snack-bar';

@Component({
  selector: 'app-file-upload',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    FormsModule,
    ReactiveFormsModule,
    MaterialModule
  ],
  templateUrl: './file-upload.component.html',
  styleUrls: ['./file-upload.component.css']
})
export class FileUploadComponent {
  @Input() acceptedFormats: string[] = ['.xlsx', '.xls'];
  @Input() maxFileSizeMB: number = 10;
  @Input() uploadEndpoint: string = '/upload';
  @Output() fileUploaded = new EventEmitter<any>();
  @Output() uploadError = new EventEmitter<string>();

  selectedFile: File | null = null;
  uploadStatus: string = '';
  isDragging: boolean = false;
  isUploading: boolean = false;
  uploadProgress: number = 0;
  
  // Formulario reactivo para validaciones
  uploadForm: FormGroup;

  constructor(
    private readonly apiService: ApiService,
    private readonly fb: FormBuilder,
    private readonly snackBar: MatSnackBar
  ) {
    this.uploadForm = this.fb.group({
      file: [null, [Validators.required]]
    });
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      this.processFile(input.files[0]);
    } else {
      this.resetFileSelection();
    }
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
      this.processFile(event.dataTransfer.files[0]);
    }
  }

  private processFile(file: File): void {
    // Validar tipo de archivo
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!this.acceptedFormats.includes(fileExtension)) {
      this.snackBar.open(
        `Formato de archivo no válido. Se aceptan: ${this.acceptedFormats.join(', ')}`, 
        'Cerrar', 
        { duration: 5000, panelClass: ['error-snackbar'] }
      );
      this.resetFileSelection();
      return;
    }

    // Validar tamaño de archivo
    const fileSizeMB = file.size / (1024 * 1024);
    if (fileSizeMB > this.maxFileSizeMB) {
      this.snackBar.open(
        `El archivo es demasiado grande. Tamaño máximo: ${this.maxFileSizeMB}MB`, 
        'Cerrar', 
        { duration: 5000, panelClass: ['error-snackbar'] }
      );
      this.resetFileSelection();
      return;
    }

    this.selectedFile = file;
    this.uploadForm.patchValue({ file: file });
    this.uploadForm.updateValueAndValidity();
    this.uploadStatus = '';
    this.uploadProgress = 0;
  }

  private resetFileSelection(): void {
    this.selectedFile = null;
    this.uploadForm.patchValue({ file: null });
    this.uploadForm.updateValueAndValidity();
    this.uploadStatus = '';
    this.uploadProgress = 0;
  }

  onUpload(): void {
    if (!this.selectedFile || this.isUploading) {
      return;
    }

    this.isUploading = true;
    this.uploadStatus = 'Preparando carga...';
    this.uploadProgress = 0;

    // Simular progreso de carga
    const progressInterval = setInterval(() => {
      if (this.uploadProgress < 90) {
        this.uploadProgress += Math.random() * 10;
      }
    }, 200);

    this.apiService.uploadFile(this.selectedFile).subscribe({
      next: (response: any) => {
        clearInterval(progressInterval);
        this.uploadProgress = 100;
        this.isUploading = false;
        
        const message = typeof response === 'string' ? response : 'Archivo cargado exitosamente';
        this.uploadStatus = message;
        
        this.snackBar.open(
          'Archivo cargado exitosamente', 
          'Cerrar', 
          { duration: 3000, panelClass: ['success-snackbar'] }
        );
        
        this.fileUploaded.emit(response);
        
        // Resetear después de un tiempo
        setTimeout(() => {
          this.resetFileSelection();
        }, 3000);
      },
      error: (error: HttpErrorResponse) => {
        clearInterval(progressInterval);
        this.isUploading = false;
        const errorMessage = error.message || 'Error al cargar el archivo';
        this.uploadStatus = errorMessage;
        
        this.snackBar.open(
          errorMessage, 
          'Cerrar', 
          { duration: 5000, panelClass: ['error-snackbar'] }
        );
        
        this.uploadError.emit(errorMessage);
      }
    });
  }

  removeFile(): void {
    this.resetFileSelection();
  }

  formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  getFileIcon(): string {
    if (!this.selectedFile) return 'upload_file';
    
    const extension = this.selectedFile.name.split('.').pop()?.toLowerCase();
    switch (extension) {
      case 'xlsx':
      case 'xls':
        return 'table_chart';
      case 'csv':
        return 'description';
      case 'pdf':
        return 'picture_as_pdf';
      case 'doc':
      case 'docx':
        return 'description';
      default:
        return 'insert_drive_file';
    }
  }
}
