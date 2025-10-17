/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{html,ts}",
  ],
  theme: {
    extend: {
      // Paleta de colores personalizada basada en morado
      colors: {
        // Colores primarios (morado)
        primary: {
          50: '#F5F3FF',
          100: '#EDE9FE',
          200: '#DDD6FE',
          300: '#C4B5FD',
          400: '#A78BFA',
          500: '#8B5CF6',
          600: '#7C3AED', // Color primario principal
          700: '#6D28D9',
          800: '#5B21B6',
          900: '#4C1D95',
          950: '#2E1065',
        },
        // Colores de superficie (neutros)
        surface: {
          50: '#F8FAFC',
          100: '#F1F5F9',
          200: '#E2E8F0',
          300: '#CBD5E1',
          400: '#94A3B8',
          500: '#64748B',
          600: '#475569',
          700: '#334155',
          800: '#1E293B',
          900: '#0F172A',
          950: '#020617',
        },
        // Colores semánticos
        success: {
          50: '#ECFDF5',
          100: '#D1FAE5',
          500: '#10B981',
          600: '#059669',
          700: '#047857',
          800: '#065F46',
          900: '#064E3B',
        },
        error: {
          50: '#FEF2F2',
          100: '#FEE2E2',
          500: '#EF4444',
          600: '#DC2626',
          700: '#B91C1C',
          800: '#991B1B',
          900: '#7F1D1D',
        },
        warning: {
          50: '#FFFBEB',
          100: '#FEF3C7',
          500: '#F59E0B',
          600: '#D97706',
          700: '#B45309',
          800: '#92400E',
          900: '#78350F',
        },
        info: {
          50: '#EFF6FF',
          100: '#DBEAFE',
          500: '#3B82F6',
          600: '#2563EB',
          700: '#1D4ED8',
          800: '#1E40AF',
          900: '#1E3A8A',
        },
      },
      // Familia de fuentes personalizada
      fontFamily: {
        sans: ['Inter', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'Consolas', 'monospace'],
      },
      // Escala tipográfica personalizada
      fontSize: {
        'xs': ['0.75rem', { lineHeight: '1.25' }],
        'sm': ['0.875rem', { lineHeight: '1.5' }],
        'base': ['1rem', { lineHeight: '1.5' }],
        'lg': ['1.125rem', { lineHeight: '1.5' }],
        'xl': ['1.25rem', { lineHeight: '1.5' }],
        '2xl': ['1.5rem', { lineHeight: '1.5' }],
        '3xl': ['1.875rem', { lineHeight: '1.25' }],
        '4xl': ['2.25rem', { lineHeight: '1.25' }],
        '5xl': ['3rem', { lineHeight: '1.25' }],
      },
      // Pesos de fuente personalizados
      fontWeight: {
        light: '300',
        normal: '400',
        medium: '500',
        semibold: '600',
        bold: '700',
      },
      // Sistema de espaciado basado en 8px
      spacing: {
        '0': '0',
        '1': '4px',    // 0.5 * 8px
        '2': '8px',    // 1 * 8px
        '3': '12px',   // 1.5 * 8px
        '4': '16px',   // 2 * 8px
        '5': '20px',   // 2.5 * 8px
        '6': '24px',   // 3 * 8px
        '8': '32px',   // 4 * 8px
        '10': '40px',  // 5 * 8px
        '12': '48px',  // 6 * 8px
        '16': '64px',  // 8 * 8px
        '20': '80px',  // 10 * 8px
        '24': '96px',  // 12 * 8px
        '32': '128px', // 16 * 8px
      },
      // Radio de bordes personalizado
      borderRadius: {
        'none': '0',
        'sm': '4px',
        'base': '8px',
        'md': '12px',
        'lg': '16px',
        'xl': '24px',
        'full': '9999px',
      },
      // Sombras personalizadas basadas en Material Design
      boxShadow: {
        '1': '0px 2px 1px -1px rgba(0, 0, 0, 0.06), 0px 1px 1px 0px rgba(0, 0, 0, 0.04), 0px 1px 3px 0px rgba(0, 0, 0, 0.04)',
        '2': '0px 3px 1px -2px rgba(0, 0, 0, 0.06), 0px 2px 2px 0px rgba(0, 0, 0, 0.04), 0px 1px 5px 0px rgba(0, 0, 0, 0.04)',
        '3': '0px 3px 3px -2px rgba(0, 0, 0, 0.06), 0px 3px 4px 0px rgba(0, 0, 0, 0.04), 0px 1px 8px 0px rgba(0, 0, 0, 0.04)',
        '4': '0px 2px 4px -1px rgba(0, 0, 0, 0.06), 0px 4px 5px 0px rgba(0, 0, 0, 0.04), 0px 1px 10px 0px rgba(0, 0, 0, 0.04)',
        '6': '0px 3px 5px -1px rgba(0, 0, 0, 0.06), 0px 6px 10px 0px rgba(0, 0, 0, 0.04), 0px 1px 18px 0px rgba(0, 0, 0, 0.04)',
        '8': '0px 5px 5px -3px rgba(0, 0, 0, 0.06), 0px 8px 10px 1px rgba(0, 0, 0, 0.04), 0px 3px 14px 2px rgba(0, 0, 0, 0.04)',
      },
      // Transiciones personalizadas
      transitionDuration: {
        'fast': '150ms',
        'normal': '300ms',
        'slow': '500ms',
      },
      transitionTimingFunction: {
        'material': 'cubic-bezier(0.4, 0, 0.2, 1)',
      },
      // Z-index personalizado
      zIndex: {
        'dropdown': '1000',
        'sticky': '1020',
        'fixed': '1030',
        'modal-backdrop': '1040',
        'modal': '1050',
        'popover': '1060',
        'tooltip': '1070',
        'toast': '1080',
      },
      // Breakpoints personalizados (Material Design)
      screens: {
        'xs': '0px',
        'sm': '600px',
        'md': '960px',
        'lg': '1280px',
        'xl': '1920px',
      },
      // Animaciones personalizadas
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [
    // Plugin para componentes de formulario personalizados
    require('@tailwindcss/forms'),
    // Plugin para tipografía mejorada
    require('@tailwindcss/typography'),
    // Plugin para aspect ratio
    require('@tailwindcss/aspect-ratio'),
  ],
  // Configuración para modo oscuro futuro
  darkMode: 'class',
}
