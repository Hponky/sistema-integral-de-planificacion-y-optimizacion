# Plan Integral: Implementación de Toast para Sesión Expirada

**ID de Tarea:** 20251118023048-toast-sesion-expirada  
**Estado:** En Progreso  
**Fecha de Creación:** 2025-11-18  
**Responsable:** Code Mode

## Resumen Ejecutivo

Se requiere implementar un toast para cuando se expira la sesión del usuario y manejar este error adecuadamente. Actualmente, el sistema detecta errores 401 y los procesa a través del `AuthErrorHandlerService`, pero no muestra un toast al usuario cuando la sesión expira.

## Análisis de Requisitos

### Requisito Principal
- Mostrar un toast informativo cuando la sesión del usuario expira
- Manejar el error 401 (SESSION_EXPIRED) de manera adecuada

### Especificaciones Técnicas
- Utilizar el `ToastService` existente para mostrar la notificación
- Integrar la notificación en el flujo actual de manejo de errores de autenticación
- Asegurar que el toast se muestre antes de redirigir al usuario

## Proceso de Implementación Requerido

### 1. Análisis del Flujo Actual
- [ ] Revisar el flujo actual de manejo de errores en `AuthErrorHandlerService`
- [ ] Identificar dónde se debe integrar el toast para sesión expirada
- [ ] Verificar la configuración actual del `ToastService`

### 2. Implementación del Toast
- [ ] Inyectar `ToastService` en `AuthErrorHandlerService`
- [ ] Modificar el método `handleAuthenticationError` para mostrar el toast
- [ ] Configurar el toast con el mensaje adecuado para sesión expirada
- [ ] Asegurar que el toast se muestre antes de la redirección

### 3. Verificación y Pruebas
- [ ] Verificar que el toast se muestra correctamente cuando la sesión expira
- [ ] Comprobar que no hay conflictos con el flujo de redirección
- [ ] Validar que la implementación sigue los principios de calidad del proyecto

## Principios de Calidad Aplicados

1. **Modularidad y Cohesión**: La implementación debe estar contenida dentro del servicio existente
2. **Abstracción y Encapsulación**: Utilizar las interfaces existentes del `ToastService`
3. **DRY**: Reutilizar el mensaje ya definido en `getUserFriendlyMessage`
4. **Manejo Robusto de Errores**: Asegurar que el toast no interrumpa el flujo de manejo de errores
5. **Experiencia de Usuario**: Proporcionar feedback claro y oportuno al usuario

## Criterios de Éxito

1. ✅ El toast se muestra cuando la sesión del usuario expira
2. ✅ El mensaje del toast es claro y comprensible para el usuario
3. ✅ El toast no interfiere con el flujo de redirección
4. ✅ El código sigue los estándares de calidad del proyecto
5. ✅ La implementación es mantenible y sigue las convenciones de Angular

## Subtareas

### 1. Análisis del Flujo Actual
- [ ] Revisar el flujo actual de manejo de errores en `AuthErrorHandlerService`
- [ ] Identificar dónde se debe integrar el toast para sesión expirada
- [ ] Verificar la configuración actual del `ToastService`

### 2. Implementación del Toast
- [ ] Inyectar `ToastService` en `AuthErrorHandlerService`
- [ ] Modificar el método `handleAuthenticationError` para mostrar el toast
- [ ] Configurar el toast con el mensaje adecuado para sesión expirada
- [ ] Asegurar que el toast se muestre antes de la redirección

### 3. Verificación y Pruebas
- [ ] Verificar que el toast se muestra correctamente cuando la sesión expira
- [ ] Comprobar que no hay conflictos con el flujo de redirección
- [ ] Validar que la implementación sigue los principios de calidad del proyecto

## Próximos Pasos

1. [ ] Completar análisis del flujo actual
2. [ ] Implementar el toast en `AuthErrorHandlerService`
3. [ ] Verificar y probar la implementación
4. [ ] Documentar cambios si es necesario