"""
Módulo para decoradores de utilidad en la aplicación SIPO.
"""

from flask import session, flash, redirect, url_for
import functools

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
