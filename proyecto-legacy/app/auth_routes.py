# app/auth_routes.py

from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from werkzeug.security import check_password_hash
from .models import User

# --- LA LÍNEA MÁS IMPORTANTE ---
# Aquí se crea la variable 'bp' que __init__.py está buscando.
bp = Blueprint('auth', __name__)
# -----------------------------

@bp.route('/', methods=['GET', 'POST'])
def login():
    # Si el usuario ya está en la sesión, se le redirige a la página principal
    if 'user' in session:
        # Nota: url_for ahora usa el formato 'nombre_blueprint.nombre_funcion'
        return redirect(url_for('main.calculator'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            # Guardar información del usuario en la sesión
            session['user'] = user.username
            session['role'] = user.role
            session['user_id'] = user.id
            flash('Inicio de sesión exitoso.', 'success')
            return redirect(url_for('main.calculator'))
        else:
            flash('Usuario o contraseña incorrectos.', 'error')

    return render_template('login.html')

@bp.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión exitosamente.', 'success')
    return redirect(url_for('auth.login'))