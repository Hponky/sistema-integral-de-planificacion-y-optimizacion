"""
Módulo para decoradores de utilidad en la aplicación 
"""

from flask import session, flash, redirect, url_for, jsonify, request
import functools

def login_required(f):
    """
    Decorador que restringe el acceso a una ruta solo a usuarios autenticados.
    Para APIs JSON devuelve error 401, para rutas web redirige al login.
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            # Verificar si es una API request
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'error': 'No autorizado'}), 401
            flash("Por favor, inicia sesión para acceder a esta página.", "error")
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """
    Decorador que restringe el acceso a una ruta solo a usuarios con rol 'admin'.
    Redirige a la calculadora si el usuario no es admin.
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session or session['role'] != 'admin':
            flash("Acceso no autorizado. Se requiere rol de administrador.", "error")
            return redirect(url_for('calculator.calculator_page')) # Redirigir a la calculadora
        return f(*args, **kwargs)
    return decorated_function
