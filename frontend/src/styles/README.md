# Sistema de Diseño SIPO - Calculadora de Agentes

## Overview

Este documento describe el sistema de diseño implementado para la aplicación SIPO, basado en Material Design 3.0 y cumpliendo con los estándares de accesibilidad WCAG 2.2 AA.

## Arquitectura del Sistema de Diseño

### Estructura de Archivos

```
frontend/src/styles/
├── design-system.css      # Sistema de diseño base (variables CSS, utilidades)
├── main.css              # Archivo principal que integra todos los estilos
├── material-theme.css    # Tema personalizado de Angular Material
├── styles.css            # Estilos globales de la aplicación
└── README.md             # Esta documentación
```

### Principios de Diseño

1. **Basado en Material Design 3.0**: Sistema moderno y consistente
2. **Accesibilidad WCAG 2.2 AA**: Contraste mínimo de 4.5:1 para texto normal
3. **Arquitectura CSS Modular**: Siguiendo principios SOLID
4. **Paleta Cromática Basada en Morado**: Identidad visual consistente
5. **Sistema de Espaciado Consistente**: Base de 8px para toda la aplicación

## Paleta de Colores

### Colores Primarios (Morado)

```css
--sipo-color-primary-50: #F5F3FF;
--sipo-color-primary-100: #EDE9FE;
--sipo-color-primary-200: #DDD6FE;
--sipo-color-primary-300: #C4B5FD;
--sipo-color-primary-400: #A78BFA;
--sipo-color-primary-500: #8B5CF6;
--sipo-color-primary-600: #7C3AED;  /* Color primario principal */
--sipo-color-primary-700: #6D28D9;
--sipo-color-primary-800: #5B21B6;
--sipo-color-primary-900: #4C1D95;
```

### Colores de Superficie (Neutros)

```css
--sipo-color-surface-50: #F8FAFC;
--sipo-color-surface-100: #F1F5F9;
--sipo-color-surface-200: #E2E8F0;
--sipo-color-surface-300: #CBD5E1;
--sipo-color-surface-400: #94A3B8;
--sipo-color-surface-500: #64748B;
--sipo-color-surface-600: #475569;
--sipo-color-surface-700: #334155;
--sipo-color-surface-800: #1E293B;
--sipo-color-surface-900: #0F172A;
```

### Colores Semánticos

- **Éxito**: Verde (#10B981)
- **Error**: Rojo (#EF4444)
- **Advertencia**: Amarillo (#F59E0B)
- **Información**: Azul (#3B82F6)

## Tipografía

### Fuentes

- **Primaria**: Inter, Roboto, Helvetica Neue, Arial, sans-serif
- **Monoespaciada**: JetBrains Mono, Fira Code, Consolas, monospace

### Escala Tipográfica

| Clase              | Tamaño | Uso                          |
|--------------------|--------|------------------------------|
| `sipo-text-xs`     | 12px   | Texto muy pequeño            |
| `sipo-text-sm`     | 14px   | Texto pequeño, captions      |
| `sipo-text-base`   | 16px   | Texto base del cuerpo        |
| `sipo-text-lg`     | 18px   | Texto grande                 |
| `sipo-text-xl`     | 20px   | Subtítulos                   |
| `sipo-text-2xl`    | 24px   | Títulos pequeños             |
| `sipo-text-3xl`    | 30px   | Títulos medianos             |
| `sipo-text-4xl`    | 36px   | Títulos grandes              |
| `sipo-text-5xl`    | 48px   | Títulos extra grandes        |

### Jerarquía Semántica

- `sipo-text-display`: Títulos principales
- `sipo-text-headline`: Subtítulos principales
- `sipo-text-title-large`: Títulos de sección
- `sipo-text-title-medium`: Títulos de subsección
- `sipo-text-title-small`: Títulos pequeños
- `sipo-text-body-large`: Texto del cuerpo grande
- `sipo-text-body-medium`: Texto del cuerpo normal
- `sipo-text-body-small`: Texto del cuerpo pequeño
- `sipo-text-label`: Etiquetas de formulario

## Sistema de Espaciado

Basado en una unidad de 8px para mantener consistencia en toda la aplicación.

```css
--sipo-space-0: 0;
--sipo-space-1: 4px;    /* 0.5 * 8px */
--sipo-space-2: 8px;    /* 1 * 8px */
--sipo-space-3: 12px;   /* 1.5 * 8px */
--sipo-space-4: 16px;   /* 2 * 8px */
--sipo-space-5: 20px;   /* 2.5 * 8px */
--sipo-space-6: 24px;   /* 3 * 8px */
--sipo-space-8: 32px;   /* 4 * 8px */
--sipo-space-10: 40px;  /* 5 * 8px */
--sipo-space-12: 48px;  /* 6 * 8px */
--sipo-space-16: 64px;  /* 8 * 8px */
--sipo-space-20: 80px;  /* 10 * 8px */
--sipo-space-24: 96px;  /* 12 * 8px */
--sipo-space-32: 128px; /* 16 * 8px */
```

## Bordes y Sombras

### Radio de Bordes

```css
--sipo-radius-none: 0;
--sipo-radius-sm: 4px;
--sipo-radius-base: 8px;
--sipo-radius-md: 12px;
--sipo-radius-lg: 16px;
--sipo-radius-xl: 24px;
--sipo-radius-full: 9999px;
```

### Sombras (Material Design Elevation)

- `--sipo-shadow-1` a `--sipo-shadow-8`: Diferentes niveles de elevación

## Componentes

### Botones

- `.btn-primary`: Botón principal con fondo morado
- `.btn-secondary`: Botón secundario con fondo gris
- `.btn-outline`: Botón con borde morado y fondo transparente
- `.btn-ghost`: Botón transparente con hover sutil

### Campos de Formulario

- `.form-input`: Campos de texto personalizados
- `.form-textarea`: Áreas de texto
- `.form-select`: Selects desplegables

### Tarjetas

- `.card`: Tarjetas con sombra y bordes consistentes

### Alertas

- `.alert-success`: Alertas de éxito
- `.alert-error`: Alertas de error
- `.alert-warning`: Alertas de advertencia
- `.alert-info`: Alertas de información

### Badges

- `.badge-primary`, `.badge-success`, etc: Indicadores pequeños

## Integración con Tailwind CSS

El sistema de diseño está completamente integrado con Tailwind CSS mediante configuración personalizada en `tailwind.config.js`:

- Colores personalizados mapeados a las variables CSS
- Espaciado consistente con el sistema de diseño
- Tipografía personalizada
- Sombras y bordes personalizados

## Integración con Angular Material

Se ha creado un tema personalizado para Angular Material en `material-theme.css` que:

- Utiliza la paleta de colores del sistema de diseño
- Personaliza todos los componentes de Material
- Mantiene consistencia visual con el resto de la aplicación
- Cumple con estándares de accesibilidad

## Accesibilidad

### WCAG 2.2 AA Compliance

- **Contraste mínimo**: 4.5:1 para texto normal
- **Contraste grande**: 3:1 para texto grande (18px+ o 14px+ bold)
- **Focus visible**: Indicadores claros de enfoque
- **Reducción de movimiento**: Respeto a `prefers-reduced-motion`
- **Alto contraste**: Soporte para `prefers-contrast: high`

### Mejoras de Accesibilidad

- Indicadores de enfoque visibles y consistentes
- Estructura semántica HTML5
- Atributos ARIA apropiados
- Navegación por teclado completa

## Uso en Componentes

### CSS Puro

```css
.mi-componente {
  background-color: var(--sipo-color-primary-600);
  color: var(--sipo-color-surface-50);
  padding: var(--sipo-space-4);
  border-radius: var(--sipo-radius-base);
  font-family: var(--sipo-font-family-primary);
}
```

### Clases de Utilidad

```html
<div class="sipo-text-title-medium sipo-text-primary sipo-p-4 sipo-rounded-lg">
  Contenido con estilos del sistema de diseño
</div>
```

### Tailwind CSS

```html
<div class="bg-primary-600 text-surface-50 p-4 rounded-lg font-medium">
  Contenido con clases Tailwind personalizadas
</div>
```

### Angular Material

```typescript
import { MaterialModule } from '../shared/material.module';

@NgModule({
  imports: [MaterialModule],
  // ...
})
export class MiModulo { }
```

```html
<mat-card class="card">
  <mat-card-header>
    <mat-card-title>Título</mat-card-title>
  </mat-card-header>
  <mat-card-content>
    Contenido
  </mat-card-content>
</mat-card>
```

## Mantenimiento y Extensión

### Agregar Nuevos Colores

1. Definir variables CSS en `design-system.css`
2. Agregar colores a `tailwind.config.js`
3. Actualizar tema de Angular Material si es necesario

### Agregar Nuevos Componentes

1. Definir estilos base en `design-system.css`
2. Crear clases de utilidad en `main.css`
3. Documentar en este README

### Actualizar Tipografía

1. Modificar variables CSS en `design-system.css`
2. Actualizar configuración de Tailwind
3. Probar en diferentes navegadores

## Consideraciones de Rendimiento

- Uso de CSS Custom Properties para主题 dinámico
- Optimización de Tailwind CSS con purgado de clases no utilizadas
- Lazy loading de estilos específicos de componentes cuando sea necesario
- Minificación de CSS en producción

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Herramientas de Desarrollo

- Chrome DevTools para inspección de estilos
- Tailwind CSS IntelliSense para VS Code
- Angular Material DevTools para depuración de componentes
- Contrast Checker para verificación de accesibilidad

## Recursos Externos

- [Material Design 3.0](https://m3.material.io/)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [Angular Material Documentation](https://material.angular.io/)
- [WCAG 2.2 Guidelines](https://www.w3.org/WAI/WCAG22/quickref/)