import { Injectable, PLATFORM_ID, Inject } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { BehaviorSubject, Observable, tap, map } from 'rxjs';
import { environment } from '../../../environments/environment';
import { isPlatformBrowser } from '@angular/common';

import { AuthenticationStateService, AuthenticationState } from './authentication-state.service';

export interface User {
  id?: number;
  username: string;
  role?: string;
  email?: string;
  fullName?: string;
  idLegal?: string; // IdLegal from Active Directory
  permissions?: number[];
}

export interface LoginResponse {
  TipoRespuesta: string;
  ResultadoExitoso: boolean;
  MensajeError: string | null;
  Token: string;
  IdSesion: string;
  VariablesDeUsuarioLogadoDTO: any;
  IdPaisUsuarioLogado: string;
  IdCentroImputacion: string;
}

export interface LoginRequest {
  Login: string;
  Password: string;
}

export interface ActiveDirectoryDomain {
  Domain: string;
  Description: string;
}

export interface ActiveDirectoryResponse<T> {
  Datos: T;
  ResultadoExitoso: boolean;
  Mensaje: string;
  ErroresValidacion: any;
}

export interface ActiveDirectoryLoginRequest {
  Domain: string;
  UserName: string;
  Password: string;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private currentUserSubject = new BehaviorSubject<User | null>(null);
  public currentUser$ = this.currentUserSubject.asObservable();

  private readonly AUTH_API_URL = environment.apiUrlAutenticacion;
  private readonly AD_GET_DOMAINS_URL = environment.apiUrlGetDomains;
  private readonly AD_LOGIN_URL = environment.apiUrlLoginActiveDirectory;
  private readonly AD_KEY = environment.activeDirectoryKey;
  private isBrowser: boolean;
  private logoutChannel: BroadcastChannel | null = null;

  constructor(
    private http: HttpClient,
    @Inject(PLATFORM_ID) platformId: Object,
    private authenticationStateService: AuthenticationStateService
  ) {
    this.isBrowser = isPlatformBrowser(platformId);
    if (this.isBrowser) {
      this.logoutChannel = new BroadcastChannel('auth_channel');
      this.logoutChannel.onmessage = (event) => {
        if (event.data === 'logout') {
          this.clearUser();
          window.location.reload();
        } else if (event.data?.type === 'login') {
          // Sync login across tabs
          localStorage.setItem('token', event.data.token);
          localStorage.setItem('VariablesDeUsuarioLogado', JSON.stringify(event.data.variables));
          localStorage.setItem('idSesion', event.data.idSesion);
          localStorage.setItem('currentUser', JSON.stringify(event.data.user));

          this.authenticationStateService.setState(AuthenticationState.AUTHENTICATED).subscribe();
          window.location.reload();
        }
      };
      this.loadUserFromStorage();
    }
  }

  login(credentials: LoginRequest): Observable<LoginResponse> {
    const headers = new HttpHeaders().set('content-type', 'application/json');
    return this.http.post<LoginResponse>(this.AUTH_API_URL, credentials, { headers })
      .pipe(
        tap(response => {
          if (response.ResultadoExitoso && response.Token) {
            this.handleSuccessfulLogin(response);
          }
        })
      );
  }

  getActiveDirectoryDomains(): Observable<ActiveDirectoryResponse<ActiveDirectoryDomain[]>> {
    const headers = new HttpHeaders()
      .set('accept', '*/*')
      .set('Authorization-Key-EME', this.AD_KEY);
    return this.http.get<ActiveDirectoryResponse<ActiveDirectoryDomain[]>>(this.AD_GET_DOMAINS_URL, { headers });
  }

  loginActiveDirectory(credentials: ActiveDirectoryLoginRequest): Observable<ActiveDirectoryResponse<any>> {
    const headers = new HttpHeaders()
      .set('accept', '*/*')
      .set('Content-Type', 'application/json-patch+json');

    return this.http.post<ActiveDirectoryResponse<any>>(this.AD_LOGIN_URL, credentials, { headers })
      .pipe(
        tap(response => {
          if (response.ResultadoExitoso && response.Datos?.Token) {
            const loginResponse: LoginResponse = {
              TipoRespuesta: response.Datos.TipoRespuesta,
              ResultadoExitoso: response.ResultadoExitoso,
              MensajeError: null,
              Token: response.Datos.Token,
              IdSesion: response.Datos.IdSesion,
              VariablesDeUsuarioLogadoDTO: response.Datos.VariablesDeUsuarioLogadoDTO,
              IdPaisUsuarioLogado: response.Datos.IdPaisUsuarioLogado,
              IdCentroImputacion: response.Datos.IdCentroImputacion
            };

            this.handleSuccessfulLogin(loginResponse);
          }
        })
      );
  }

  logout(): void {
    if (this.isBrowser && this.logoutChannel) {
      this.logoutChannel.postMessage('logout');
    }
    this.clearUser();
    this.authenticationStateService.setState(AuthenticationState.NOT_AUTHENTICATED).subscribe();
  }

  getCurrentUser(): User | null {
    return this.currentUserSubject.value;
  }

  isAuthenticated(): boolean {
    if (!this.isBrowser) return false;
    const token = localStorage.getItem('token');
    return !!token;
  }

  getToken(): string | null {
    if (!this.isBrowser) return null;
    return localStorage.getItem('token');
  }

  private handleSuccessfulLogin(response: LoginResponse): void {
    if (!this.isBrowser) return;

    localStorage.setItem('token', response.Token);
    localStorage.setItem('VariablesDeUsuarioLogado', JSON.stringify(response.VariablesDeUsuarioLogadoDTO));
    localStorage.setItem('idSesion', response.IdSesion);

    const apiUser = response.VariablesDeUsuarioLogadoDTO?.UsuarioLogado;
    const permisos = response.VariablesDeUsuarioLogadoDTO?.Permisos || [];
    let derivedRole = response.VariablesDeUsuarioLogadoDTO?.NivelAcceso || '';

    if (permisos.includes(51781)) {
      derivedRole = 'Administrador';
    } else if (permisos.includes(51782)) {
      derivedRole = 'Planificador';
    } else if (permisos.includes(51783)) {
      derivedRole = 'Sólo lectura';
    }

    const user: User = {
      id: apiUser?.IdEmpleado,
      username: apiUser?.Login || '',
      fullName: apiUser?.NombreCompleto,
      role: derivedRole,
      idLegal: apiUser?.IdLegal,
      permissions: permisos
    };

    this.setUser(user);

    // Exchange AD token for backend JWT token
    this.exchangeTokenForBackend(response.Token, user).subscribe({
      next: (backendToken) => {
        // Store the backend token (overwrite AD token)
        localStorage.setItem('token', backendToken);

        // Broadcast login to other tabs
        if (this.logoutChannel) {
          this.logoutChannel.postMessage({
            type: 'login',
            token: backendToken,
            variables: response.VariablesDeUsuarioLogadoDTO,
            idSesion: response.IdSesion,
            user: user
          });
        }

        this.authenticationStateService.setState(AuthenticationState.AUTHENTICATED).subscribe();
      },
      error: (error) => {
        console.error('Error exchanging token:', error);
        // Even if token exchange fails, we still have the AD token
        // Broadcast login to other tabs with AD token
        if (this.logoutChannel) {
          this.logoutChannel.postMessage({
            type: 'login',
            token: response.Token,
            variables: response.VariablesDeUsuarioLogadoDTO,
            idSesion: response.IdSesion,
            user: user
          });
        }
        this.authenticationStateService.setState(AuthenticationState.AUTHENTICATED).subscribe();
      }
    });
  }

  private exchangeTokenForBackend(adToken: string, userData: User): Observable<string> {
    const payload = {
      adToken: adToken,
      userData: {
        username: userData.username,
        idLegal: userData.idLegal,
        role: userData.role,
        id: userData.id,
        fullName: userData.fullName
      }
    };

    return this.http.post<any>(`${environment.apiUrl}/auth/exchange-token`, payload)
      .pipe(
        tap(response => {
          if (response.status === 'success' && response.token) {
            console.log('Backend token obtained successfully');
          }
        }),
        map(response => response.token)
      );
  }

  private setUser(user: User): void {
    this.currentUserSubject.next(user);
    if (this.isBrowser) {
      localStorage.setItem('currentUser', JSON.stringify(user));
    }
  }

  private clearUser(): void {
    this.currentUserSubject.next(null);
    if (this.isBrowser) {
      localStorage.removeItem('token');
      localStorage.removeItem('VariablesDeUsuarioLogado');
      localStorage.removeItem('idSesion');
      localStorage.removeItem('currentUser');
    }
  }

  private loadUserFromStorage(): void {
    if (!this.isBrowser) return;

    const storedUser = localStorage.getItem('currentUser');
    const token = localStorage.getItem('token');

    if (storedUser && token) {
      try {
        const user = JSON.parse(storedUser);
        this.currentUserSubject.next(user);
      } catch (error) {
        this.clearUser();
      }
    } else {
      this.clearUser();
    }
  }
}