# Plan de Implementación: Sistema de Autenticación Integrado

## Análisis del Sistema Legacy

### Características del Sistema Legacy (`Planificador-WFM-main`)

**Modelo de Autenticación:**
- **Sesiones Flask** con `session['user']` y `session['role']`
- **Base de datos** SQLAlchemy con tabla `User`
- **Roles:** `admin` y `user` con permisos por campaña
- **Decorador** `@admin_required` para protección de rutas
- **Hash de contraseñas** con `werkzeug.security`

**Estructura de Usuario:**
```python
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(80), nullable=False, default='user')
    campaigns = db.relationship('Campaign', secondary=user_campaign_permissions)
```

## Estrategia de Autenticación para Backend Flask (`/sipo`)

### 1. Migración de Modelos de Usuario
- **Reutilizar** el modelo `User` existente del legacy
- **Mantener** la estructura de permisos por campaña
- **Preservar** el sistema de hash de contraseñas

### 2. Middleware de Autenticación
```python
# Decorador para verificar autenticación
def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return jsonify({'error': 'No autorizado'}), 401
        return f(*args, **kwargs)
    return decorated_function

# Decorador para verificar rol admin
def admin_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session or session['role'] != 'admin':
            return jsonify({'error': 'Acceso denegado'}), 403
        return f(*args, **kwargs)
    return decorated_function
```

### 3. Rutas de Autenticación
```python
# POST /auth/login - Iniciar sesión
# POST /auth/logout - Cerrar sesión
# GET /auth/me - Información del usuario actual
# POST /auth/refresh - Renovar sesión (opcional)
```

### 4. Protección de APIs Existentes
- **Aplicar** `@login_required` a todas las rutas de calculadora
- **Mantener** `@admin_required` para rutas administrativas
- **Validar** permisos por campaña para usuarios no-admin

## Estrategia de Autenticación para Frontend Angular (`/frontend`)

### 1. Servicio de Autenticación
```typescript
@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiUrl = environment.apiUrl;
  
  constructor(private http: HttpClient) {}
  
  login(username: string, password: string): Observable<AuthResponse>
  logout(): Observable<void>
  getCurrentUser(): Observable<User>
  isAuthenticated(): boolean
  hasRole(role: string): boolean
}
```

### 2. Interceptor de Autenticación
```typescript
@Injectable()
export class AuthInterceptor implements HttpInterceptor {
  intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    // Adjuntar credenciales de sesión a todas las requests
    const authReq = req.clone({
      withCredentials: true
    });
    return next.handle(authReq);
  }
}
```

### 3. Guards de Ruta
```typescript
// AuthGuard - Verifica autenticación
@Injectable({
  providedIn: 'root'
})
export class AuthGuard implements CanActivate {
  canActivate(): boolean {
    return this.authService.isAuthenticated();
  }
}

// RoleGuard - Verifica roles específicos
@Injectable({
  providedIn: 'root'
})
export class RoleGuard implements CanActivate {
  canActivate(route: ActivatedRouteSnapshot): boolean {
    const expectedRole = route.data['role'];
    return this.authService.hasRole(expectedRole);
  }
}
```

### 4. Componentes de UI
- **LoginComponent** - Formulario de inicio de sesión
- **LogoutComponent** - Cierre de sesión
- **UserProfileComponent** - Perfil de usuario actual

## Flujo de Autenticación Integrado

### 1. Inicio de Sesión
```
Frontend (Angular) → POST /auth/login → Backend (Flask)
                    ↓
              Validar credenciales
                    ↓
           Crear sesión Flask + Cookie
                    ↓
    Frontend redirige a dashboard/calculadora
```

### 2. Acceso a APIs Protegidas
```
Frontend → Request a API protegida → Interceptor adjunta credenciales
          ↓
    Backend valida sesión → Ejecuta endpoint → Devuelve respuesta
```

### 3. Cierre de Sesión
```
Frontend → POST /auth/logout → Backend limpia sesión
          ↓
    Frontend redirige a login y limpia estado local
```

## Implementación Detallada

### Fase 1: Backend Flask
1. **Extender** modelo `User` en `sipo/models.py`
2. **Implementar** decoradores de autenticación en `sipo/utils/decorators.py`
3. **Crear** rutas de auth en `sipo/routes/auth.py`
4. **Proteger** rutas existentes en `sipo/routes/calculator.py`

### Fase 2: Frontend Angular
1. **Crear** `AuthService` en `frontend/src/app/core/services/auth.service.ts`
2. **Implementar** `AuthInterceptor` en `frontend/src/app/core/interceptors/auth.interceptor.ts`
3. **Crear** guards en `frontend/src/app/core/guards/`
4. **Desarrollar** componentes de login/logout
5. **Configurar** enrutamiento protegido

### Fase 3: Integración y Pruebas
1. **Probar** flujo completo de autenticación
2. **Validar** permisos por campaña
3. **Verificar** protección de rutas administrativas
4. **Testear** manejo de errores y estados

## Consideraciones de Seguridad

### 1. Sesiones vs JWT
- **Sesiones Flask**: Más simple, estado en servidor
- **Compatibilidad** con sistema legacy existente
- **Seguridad**: CSRF protection, cookie secure flags

### 2. Permisos Granulares
- **Usuarios admin**: Acceso completo
- **Usuarios regulares**: Solo campañas asignadas
- **Validación** en cada endpoint protegido

### 3. Manejo de Errores
- **401 Unauthorized**: No autenticado
- **403 Forbidden**: Sin permisos suficientes
- **Mensajes** de error claros para el frontend

## Migración de Datos de Usuarios

### Opción 1: Base de Datos Compartida
- **Ventaja**: Usuarios existentes funcionan inmediatamente
- **Desventaja**: Acoplamiento con sistema legacy

### Opción 2: Base de Datos Separada
- **Ventaja**: Independencia entre sistemas
- **Desventaja**: Requiere migración de usuarios

**Recomendación**: Iniciar con base de datos compartida para facilitar transición.

## Plan de Implementación por Prioridad

### ALTA PRIORIDAD (Funcionalidad básica)
1. Implementar decoradores de autenticación en backend
2. Crear servicio de autenticación en frontend
3. Proteger rutas de calculadora existentes
4. Implementar componente de login

### MEDIA PRIORIDAD (Mejoras UX/seguridad)
5. Implementar interceptor de autenticación
6. Crear guards de ruta
7. Manejo de errores de autenticación
8. Componente de perfil de usuario

### BAJA PRIORIDAD (Características avanzadas)
9. Refresh automático de sesión
10. Recordar sesión (remember me)
11. Cambio de contraseña
12. Auditoría de acceso

## Próximos Pasos Inmediatos

1. **Implementar middleware** de autenticación en backend Flask
2. **Proteger endpoints** existentes de calculadora
3. **Crear servicio** de autenticación en Angular
4. **Desarrollar componente** de login
5. **Configurar interceptor** para manejo automático de credenciales

Este plan asegura una integración robusta del sistema de autenticación manteniendo compatibilidad con el sistema legacy existente.