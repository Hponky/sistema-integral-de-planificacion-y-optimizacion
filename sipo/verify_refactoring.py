#!/usr/bin/env python3
"""
Script para verificar que la refactorización del CalculatorService mantiene la funcionalidad existente.
Este script ejecuta pruebas básicas para asegurar que los resultados son consistentes
con la implementación original.
"""

import sys
import os

# Agregar el directorio sipo al path de Python para poder importar los módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.calculator_service import CalculatorService

def test_basic_functionality():
    """
    Prueba la funcionalidad básica del CalculatorService refactorizado.
    """
    print("Verificando la refactorización del CalculatorService...")
    
    # Crear instancia del servicio refactorizado
    service = CalculatorService()
    
    # Casos de prueba básicos
    test_cases = [
        {
            'name': 'Erlang B con valores estándar',
            'method': 'vba_erlang_b',
            'args': (5, 2),
            'expected_range': (0.06, 0.07)  # Rango aproximado
        },
        {
            'name': 'Erlang C con valores estándar',
            'method': 'vba_erlang_c',
            'args': (5, 2),
            'expected_range': (0.14, 0.15)  # Rango aproximado
        },
        {
            'name': 'SLA con valores estándar',
            'method': 'vba_sla',
            'args': (5, 20, 100, 180),
            'expected_range': (0.7, 0.9)  # Rango aproximado
        },
        {
            'name': 'Agentes Requeridos con valores estándar',
            'method': 'vba_agents_required',
            'args': (0.8, 20, 100, 180),
            'expected_range': (5, 7)  # Rango aproximado
        }
    ]
    
    # Ejecutar pruebas
    all_passed = True
    for test_case in test_cases:
        method = getattr(service, test_case['method'])
        result = method(*test_case['args'])
        min_expected, max_expected = test_case['expected_range']
        
        passed = min_expected <= result <= max_expected
        status = "✓ PASÓ" if passed else "✗ FALLÓ"
        
        print(f"{status}: {test_case['name']}")
        print(f"  Resultado: {result:.4f}")
        print(f"  Esperado: entre {min_expected} y {max_expected}")
        print()
        
        if not passed:
            all_passed = False
    
    # Verificar estrategias disponibles
    available_strategies = service.strategy_context.get_available_strategies()
    print(f"Estrategias disponibles: {available_strategies}")
    
    # Verificar manejo de errores
    try:
        service.vba_erlang_b(-1, 2)
        print("✗ FALLÓ: No se detectó valor negativo para Erlang B")
        all_passed = False
    except ValueError:
        print("✓ PASÓ: Se detectó correctamente valor negativo para Erlang B")
    
    try:
        service.vba_erlang_c(0, 2)
        print("✗ FALLÓ: No se detectó valor cero para Erlang C")
        all_passed = False
    except ValueError:
        print("✓ PASÓ: Se detectó correctamente valor cero para Erlang C")
    
    # Resumen final
    if all_passed:
        print("=== TODAS LAS PRUEBAS PASARON ===")
        print("La refactorización mantiene la funcionalidad existente.")
        return True
    else:
        print("=== ALGUNAS PRUEBAS FALLARON ===")
        print("La refactorización requiere revisión.")
        return False

if __name__ == "__main__":
    success = test_basic_functionality()
    sys.exit(0 if success else 1)