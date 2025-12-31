# app/admin_routes.py

from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash
import pandas as pd
import datetime

# Importamos la instancia de la DB y los modelos
from . import db
from .models import User, Campaign, Segment, SchedulingRule


# --- Decorador de autorización ---
# Este decorador protegerá todas las rutas de este blueprint
import functools

bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        # 2. CORRECCIÓN: Si falla la autorización, redirigimos a una ruta que exista, como 'auth.login' o 'main.calculator'
        #    (Asegúrate de que 'main.calculator' sea el nombre correcto del endpoint)
        if 'role' not in session or session['role'] != 'admin':
            flash("Acceso no autorizado. Se requieren permisos de administrador.", "error")
            return redirect(url_for('main.calculator')) # Asumiendo que tienes un blueprint 'main'
        return view(**kwargs)
    return wrapped_view

# Aplicamos el decorador a TODAS las rutas de este blueprint
@bp.before_request
@admin_required
def before_request():
    pass

@bp.route('/', methods=['GET', 'POST'])
def admin_panel():
    if request.method == 'POST':
        action = request.form.get('action')

        # --- GESTIÓN DE USUARIOS ---
        if action == 'create_user':
            username = request.form.get('new_username')
            password = request.form.get('new_password')
            role = request.form.get('new_role')
            if not username or not password or len(password) < 8:
                flash('Usuario y contraseña (mín 8 chars) son obligatorios.', 'error')
            elif User.query.filter_by(username=username).first():
                flash(f"El usuario '{username}' ya existe.", 'error')
            else:
                new_user = User(username=username, password_hash=generate_password_hash(password, method='pbkdf2:sha256'), role=role)
                db.session.add(new_user)
                db.session.commit()
                flash(f"Usuario '{username}' creado con éxito.", 'success')

        elif action == 'update_user':
            user_to_update = User.query.get(request.form.get('user_id'))
            if user_to_update and user_to_update.username != 'admin':
                user_to_update.role = request.form.get('role')
                all_campaigns_map = {c.id: c for c in Campaign.query.all()}
                permitted_ids = [int(id_str) for id_str in request.form.getlist('permissions')]
                user_to_update.campaigns = [all_campaigns_map.get(cid) for cid in permitted_ids if all_campaigns_map.get(cid)]
                db.session.commit()
                flash(f'Permisos de {user_to_update.username} actualizados.', 'success')
            else:
                flash('No se pudo actualizar el usuario.', 'error')

        elif action == 'delete_user':
            user_id = request.form.get('user_id_to_delete')
            if user_id and int(user_id) == session.get('user_id'):
                flash("No puedes eliminar tu propia cuenta.", 'error')
            else:
                user = User.query.get(user_id)
                if user:
                    db.session.delete(user)
                    db.session.commit()
                    flash(f"Usuario '{user.username}' eliminado.", 'success')
                else:
                    flash("Usuario no encontrado.", 'error')
        
        # --- GESTIÓN DE CAMPAÑAS ---
        elif action == 'create_campaign':
            code, name, country = request.form.get('new_campaign_code'), request.form.get('new_campaign_name'), request.form.get('new_campaign_country')
            if not name or not country:
                flash('El nombre y el país de la campaña son obligatorios.', 'error')
            elif Campaign.query.filter_by(name=name).first():
                flash(f"La campaña '{name}' ya existe.", 'error')
            else:
                db.session.add(Campaign(code=code, name=name, country=country))
                db.session.commit()
                flash(f"Campaña '{name}' creada con éxito.", 'success')
        
        elif action == 'delete_campaign':
            campaign = Campaign.query.get(request.form.get('delete_campaign_id'))
            if campaign:
                db.session.delete(campaign)
                db.session.commit()
                flash(f"Campaña '{campaign.name}' y sus segmentos han sido eliminados.", 'success')
            else:
                flash("No se encontró la campaña a eliminar.", 'error')

        # --- GESTIÓN DE SEGMENTOS ---
        elif action == 'create_segment' or action == 'update_segment':
            segment = None
            if action == 'create_segment':
                campaign_id, segment_name = request.form.get('campaign_id_for_segment'), request.form.get('segment_name')
                if not segment_name or not campaign_id:
                    flash('El nombre del segmento y la campaña son obligatorios.', 'error')
                elif Segment.query.filter_by(name=segment_name, campaign_id=campaign_id).first():
                    flash(f"El segmento '{segment_name}' ya existe.", 'error')
                else:
                    segment = Segment(campaign_id=campaign_id)
                    db.session.add(segment)
                    flash(f"Segmento '{segment_name}' creado.", 'success')
            else:
                segment = Segment.query.get(request.form.get('segment_id'))
                if not segment:
                    flash("Error: No se encontró el segmento.", "error")
                    return redirect(url_for('admin.admin_panel'))
                flash(f"Segmento '{segment.name}' actualizado.", 'success')
            
            if segment:
                segment.name = request.form.get('segment_name')
                segment.service_type = request.form.get('service_type', 'INBOUND')
                segment.bo_sla_hours = int(request.form.get('bo_sla_hours', 24))
                def format_time(t): return datetime.datetime.strptime(t, '%H:%M').strftime('%H:%M') if t else None
                segment.lunes_apertura=format_time(request.form.get('lunes_apertura')); segment.lunes_cierre=format_time(request.form.get('lunes_cierre'))
                segment.martes_apertura=format_time(request.form.get('martes_apertura')); segment.martes_cierre=format_time(request.form.get('martes_cierre'))
                segment.miercoles_apertura=format_time(request.form.get('miercoles_apertura')); segment.miercoles_cierre=format_time(request.form.get('miercoles_cierre'))
                segment.jueves_apertura=format_time(request.form.get('jueves_apertura')); segment.jueves_cierre=format_time(request.form.get('jueves_cierre'))
                segment.viernes_apertura=format_time(request.form.get('viernes_apertura')); segment.viernes_cierre=format_time(request.form.get('viernes_cierre'))
                segment.sabado_apertura=format_time(request.form.get('sabado_apertura')); segment.sabado_cierre=format_time(request.form.get('sabado_cierre'))
                segment.domingo_apertura=format_time(request.form.get('domingo_apertura')); segment.domingo_cierre=format_time(request.form.get('domingo_cierre'))
                segment.weekend_policy = request.form.get('weekend_policy')
                segment.min_full_weekends_off_per_month = int(request.form.get('min_full_weekends_off_per_month', 2))
                db.session.commit()
            
        elif action == 'delete_segment':
            segment = Segment.query.get(request.form.get('delete_segment_id'))
            if segment:
                db.session.delete(segment)
                db.session.commit()
                flash(f"Segmento '{segment.name}' eliminado.", 'success')
            else:
                flash("No se encontró el segmento a eliminar.", 'error')

        # --- IMPORTACIÓN MASIVA ---
        elif action == 'import_campaigns':
            if 'campaign_excel_file' not in request.files or not request.files['campaign_excel_file'].filename:
                flash('No se seleccionó ningún archivo para la importación.', 'error')
            else:
                try:
                    file = request.files['campaign_excel_file']
                    df = pd.read_excel(file, dtype=str).fillna('')
                    df.columns = [str(c).strip().lower().replace(' ', '_') for c in df.columns]
                    
                    required_cols = ['campaign_name', 'campaign_country', 'segment_name', 'service_type','weekend_policy', 'min_full_weekends_off_per_month']
                    missing_cols = [col for col in required_cols if col not in df.columns]

                    if missing_cols:
                        flash(f"Faltan columnas en el Excel: {', '.join(missing_cols)}", 'error')
                    else:
                        campaign_cache, created_c, created_s = {}, 0, 0
                        for index, row in df.iterrows():
                            c_name = row.get('campaign_name').strip()
                            c_country = row.get('campaign_country').strip()
                            s_name = row.get('segment_name').strip()
                            if not all([c_name, c_country, s_name]): continue

                            key = (c_name, c_country)
                            if key not in campaign_cache:
                                camp = Campaign.query.filter_by(name=c_name, country=c_country).first()
                                if not camp:
                                    camp = Campaign(name=c_name, country=c_country)
                                    db.session.add(camp); db.session.flush(); created_c += 1
                                campaign_cache[key] = camp
                            
                            campaign_obj = campaign_cache[key]
                            if not Segment.query.filter_by(name=s_name, campaign_id=campaign_obj.id).first():
                                def format_excel_time(time_str):
                                    if not time_str or time_str == '': return None
                                    try: return pd.to_datetime(time_str).strftime('%H:%M')
                                    except: return None

                                new_segment = Segment(
                                    name=s_name, campaign_id=campaign_obj.id,
                                    service_type=row.get('service_type', 'INBOUND').strip(),
                                    lunes_apertura=format_excel_time(row.get('lunes_apertura')), lunes_cierre=format_excel_time(row.get('lunes_cierre')),
                                    martes_apertura=format_excel_time(row.get('martes_apertura')), martes_cierre=format_excel_time(row.get('martes_cierre')),
                                    miercoles_apertura=format_excel_time(row.get('miercoles_apertura')), miercoles_cierre=format_excel_time(row.get('miercoles_cierre')),
                                    jueves_apertura=format_excel_time(row.get('jueves_apertura')), jueves_cierre=format_excel_time(row.get('jueves_cierre')),
                                    viernes_apertura=format_excel_time(row.get('viernes_apertura')), viernes_cierre=format_excel_time(row.get('viernes_cierre')),
                                    sabado_apertura=format_excel_time(row.get('sabado_apertura')), sabado_cierre=format_excel_time(row.get('sabado_cierre')),
                                    domingo_apertura=format_excel_time(row.get('domingo_apertura')), domingo_cierre=format_excel_time(row.get('domingo_cierre')),
                                    weekend_policy=row.get('weekend_policy', 'FLEXIBLE').strip(),
                                    min_full_weekends_off_per_month=int(row.get('min_full_weekends_off_per_month', 2))
                                )
                                db.session.add(new_segment); created_s += 1
                        
                        db.session.commit()
                        flash(f"Importación completa: {created_c} campañas y {created_s} segmentos nuevos creados.", 'success')
                except Exception as e:
                    db.session.rollback()
                    flash(f"Error al procesar el archivo Excel: {e}", 'error')

        # --- GESTIÓN DE REGLAS DE CONTRATO ---
        elif action == 'create_rule':
            # Ahora leemos todos los campos del formulario
            name = request.form.get('new_rule_name')
            country = request.form.get('new_rule_country')

            if not name or not country:
                flash("El nombre y el país de la regla son obligatorios.", "error")
            elif SchedulingRule.query.filter_by(rule_name=name).first(): # Buscamos por rule_name
                flash(f"La regla '{name}' ya existe.", "error")
            else:
                try:
                    # Creamos la instancia de SchedulingRule directamente con todos los datos
                    rule = SchedulingRule(
                        rule_name=name, 
                        country_code=country, # Usamos country_code
                        weekly_hours=float(request.form['new_rule_weekly_hours']),
                        max_daily_hours=float(request.form['new_rule_max_daily_hours']),
                        min_daily_hours=float(request.form['new_rule_min_daily_hours']),
                        days_per_week=int(request.form['new_rule_days_per_week']),
                        max_consecutive_work_days=int(request.form['new_rule_max_consecutive']),
                        
                        # === INICIO: LÍNEA AÑADIDA ===
                        # Lee el valor del nuevo campo del formulario. Si no se envía, usa 2 por defecto.
                        min_full_weekends_off_per_month=int(request.form.get('min_full_weekends_off_per_month', 2)),
                        # === FIN: LÍNEA AÑADIDA ===
                        
                    )
                    # Ya no necesitamos crear una instancia de WorkdayRule
                    db.session.add(rule)
                    db.session.commit()
                    flash(f"Regla '{name}' creada con éxito.", "success")
                except (ValueError, TypeError, KeyError) as e:
                    db.session.rollback()
                    flash(f"Error en los valores de la regla: {e}", "error")

        elif action == 'delete_rule':
            rule = SchedulingRule.query.get(request.form.get('delete_rule_id'))
            if rule:
                db.session.delete(rule)
                db.session.commit()
                flash(f"Regla '{rule.rule_name}' eliminada.", 'success') # Usamos rule.rule_name
            else:
                flash("No se encontró la regla a eliminar.", 'error')
        
        return redirect(url_for('admin.admin_panel'))

    # Lógica GET
    users = User.query.order_by(User.username).all()
    campaigns = Campaign.query.order_by(Campaign.name).all()
    # Ahora consultamos SchedulingRule directamente
    rules = SchedulingRule.query.order_by(SchedulingRule.country_code, SchedulingRule.rule_name).all()
    users_data_json = { u.id: {"role": u.role, "campaigns": [c.id for c in u.campaigns]} for u in users if u.username != 'admin' }
    
    return render_template('admin_users.html', users=users, campaigns=campaigns, rules=rules, users_data_json=users_data_json)