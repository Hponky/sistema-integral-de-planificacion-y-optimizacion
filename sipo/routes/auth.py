"""
Módulo de rutas para la autenticación de usuarios.
"""

from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from sipo.app import db
from sipo.models import User # Importar el modelo User desde sipo.models
from werkzeug.security import generate_password_hash

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Maneja el inicio de sesión de usuarios.
    """
    if 'user' in session:
        return redirect(url_for('calculator.calculator_page')) # Redirigir a la calculadora si ya está logueado

    if request.method == 'POST':
        # Verificar si es una solicitud JSON (API) o formulario tradicional
        if request.is_json:
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
        else:
            username = request.form['username']
            password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password): # Usar el método check_password del modelo User
            session['user'] = user.username
            session['role'] = user.role
            
            if request.is_json:
                return jsonify({
                    'success': True,
                    'message': 'Inicio de sesión exitoso',
                    'user': {
                        'username': user.username,
                        'role': user.role
                    }
                })
            else:
                flash('Inicio de sesión exitoso.', 'success')
                return redirect(url_for('calculator.calculator_page'))
        else:
            if request.is_json:
                return jsonify({
                    'success': False,
                    'message': 'Usuario o contraseña incorrectos'
                }), 401
            else:
                flash('Usuario o contraseña incorrectos.', 'error')
    
    # Si es GET o POST fallido, renderizar template
    return render_template('auth/login.html')

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    Cierra la sesión del usuario.
    """
    session.clear()
    
    if request.is_json:
        return jsonify({
            'success': True,
            'message': 'Sesión cerrada exitosamente'
        })
    else:
        flash('Has cerrado sesión exitosamente.', 'success')
        return redirect(url_for('auth.login'))

@auth_bp.route('/check_session', methods=['GET'])
def check_session():
    """
    Verifica si hay una sesión activa.
    """
    if 'user' in session:
        return jsonify({
            'authenticated': True,
            'user': {
                'username': session['user'],
                'role': session['role']
            }
        })
    else:
        return jsonify({'authenticated': False})
