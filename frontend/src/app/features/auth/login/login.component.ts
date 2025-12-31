import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, ActivatedRoute } from '@angular/router';
import { AuthService, LoginRequest } from '../../../core/services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css']
})
export class LoginComponent implements OnInit {
  credentials: LoginRequest = {
    Login: '',
    Password: ''
  };

  adCredentials: {
    Domain: string;
    UserName: string;
    Password: string;
  } = {
      Domain: '',
      UserName: '',
      Password: ''
    };

  loginMethod: 'EOS' | 'AD' = 'EOS';
  domains: any[] = [];
  loading = false;
  error = '';

  constructor(
    private authService: AuthService,
    private router: Router,
    private route: ActivatedRoute
  ) { }

  ngOnInit(): void {
    if (this.authService.isAuthenticated()) {
      this.router.navigate(['/landing']);
    }
  }

  toggleLoginMethod(method: 'EOS' | 'AD'): void {
    this.loginMethod = method;
    this.error = '';
    if (method === 'AD' && this.domains.length === 0) {
      this.fetchDomains();
    }
  }

  fetchDomains(): void {
    this.loading = true;
    this.authService.getActiveDirectoryDomains().subscribe({
      next: (response) => {
        this.loading = false;
        if (response.ResultadoExitoso) {
          this.domains = response.Datos;
        } else {
          this.error = 'Error al cargar dominios';
        }
      },
      error: () => {
        this.loading = false;
        this.error = 'Error al cargar dominios';
      }
    });
  }

  onSubmit(): void {
    this.error = '';

    if (this.loginMethod === 'EOS') {
      if (!this.credentials.Login || !this.credentials.Password) {
        this.error = 'Por favor complete todos los campos';
        return;
      }
      this.loginEOS();
    } else {
      if (!this.adCredentials.Domain || !this.adCredentials.UserName || !this.adCredentials.Password) {
        this.error = 'Por favor complete todos los campos';
        return;
      }
      this.loginAD();
    }
  }

  loginEOS(): void {
    this.loading = true;
    this.authService.login(this.credentials).subscribe({
      next: (response) => {
        this.loading = false;
        if (response.ResultadoExitoso) {
          this.handleSuccess();
        } else {
          const rawError = response.MensajeError || response.VariablesDeUsuarioLogadoDTO?.ErrorUsuario || '';
          if (rawError.includes('ORA-') || rawError.includes('TNS-')) {
            this.error = '⚠️ El servicio EOS tiene problemas de conexión con la base de datos (Error Oracle). Por favor, intenta de nuevo en unos momentos.';
          } else {
            this.error = rawError || 'Error al iniciar sesión';
          }
        }
      },
      error: (error) => {
        this.loading = false;
        console.error('Login error:', error);

        const errorMessage = error.error?.message || error.message || '';
        const errorBody = typeof error.error === 'string' ? error.error : JSON.stringify(error.error);
        const fullErrorStack = JSON.stringify(error);

        // 1. Detectar cualquier error de Oracle (ORA-XXXXX) o TNS
        if (fullErrorStack.includes('ORA-') || fullErrorStack.includes('TNS-') ||
          errorBody?.includes('ORA-') || errorBody?.includes('TNS-')) {
          this.error = '⚠️ El servicio EOS está temporalmente fuera de servicio por problemas en la base de datos Oracle. Por favor, intenta de nuevo en unos minutos.';
        }
        // 2. Detectar errores de texto plano / HTML (cuando el servidor falla y devuelve una página de error)
        else if (errorMessage.includes('text/html') || errorMessage.includes('Unexpected token') || errorBody?.includes('<!DOCTYPE html>')) {
          this.error = '⚠️ El servidor de autenticación EOS no está respondiendo correctamente (Error de servidor). Es posible que esté en mantenimiento.';
        }
        else {
          this.error = 'Error de conexión o servidor no disponible';
        }
      }
    });
  }

  loginAD(): void {
    this.loading = true;
    this.authService.loginActiveDirectory(this.adCredentials).subscribe({
      next: (response) => {
        this.loading = false;
        if (response.ResultadoExitoso) {
          this.handleSuccess();
        } else {
          this.error = response.Mensaje || 'Error al iniciar sesión';
        }
      },
      error: (error) => {
        this.loading = false;
        console.error('AD Login error:', error);

        const errorMessage = error.error?.message || error.message || '';
        const errorBody = typeof error.error === 'string' ? error.error : JSON.stringify(error.error);
        const fullErrorStack = JSON.stringify(error);

        // 1. Detectar ORA-01033 o problemas de base de datos
        if (fullErrorStack.includes('ORA-01033') || errorBody?.includes('ORA-01033')) {
          this.error = '⚠️ El servicio de Directorio Activo está en mantenimiento (Problema de base de datos). Por favor, intenta de nuevo en unos minutos.';
        }
        // 2. Manejar casos donde el servidor responde con texto plano "Ocurrió un..."
        else if (errorMessage.includes('Unexpected token') && errorMessage.includes('Ocurrió un')) {
          this.error = '⚠️ El servidor de Directorio Activo respondió: "Ocurrió un error inesperado". Por favor, verifica tus credenciales o intenta más tarde.';
        }
        else {
          this.error = 'Error de conexión con Directorio Activo o servidor no disponible';
        }
      }
    });
  }

  handleSuccess(): void {
    const returnUrl = this.route.snapshot.queryParams['returnUrl'] || '/landing';
    console.log('Redirecting to:', returnUrl);
    this.router.navigateByUrl(returnUrl);
  }

  fillDemoCredentials(): void {
    this.credentials = {
      Login: '',
      Password: ''
    };
    this.error = '';
  }
}