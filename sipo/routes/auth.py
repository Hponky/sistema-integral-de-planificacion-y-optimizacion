"""
Módulo de rutas para la autenticación de usuarios.
"""

from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from sipo.app import db
from sipo.models import User # Importar el modelo User desde sipo.models

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Maneja el inicio de sesión de usuarios.
    """
    if 'user' in session:
        return redirect(url_for('calculator.calculator_page')) # Redirigir a la calculadora si ya está logueado

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password): # Usar el método check_password del modelo User
            session['user'] = user.username
            session['role'] = user.role
            flash('Inicio de sesión exitoso.', 'success')
            return redirect(url_for('calculator.calculator_page'))
        else:
            flash('Usuario o contraseña incorrectos.', 'error')
            
    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    """
    Cierra la sesión del usuario.
    """
    session.clear()
    flash('Has cerrado sesión exitosamente.', 'success')
    return redirect(url_for('auth.login'))
