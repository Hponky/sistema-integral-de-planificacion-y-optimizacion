# app/main_routes.py

from flask import Blueprint, render_template, session, redirect, url_for
from sqlalchemy.orm import joinedload
import json
from .models import Segment, Campaign, ShiftChangeRequest, User 
import functools

bp = Blueprint('main', __name__)

# --- Decorador de Seguridad ---
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return view(**kwargs)
    return wrapped_view

# --- Rutas ---

@bp.route('/')
@login_required
def index():
    return render_template('index.html')

@bp.route('/scheduling')
@login_required
def scheduling():
    # 1. Cargar todas las campañas
    campaigns = Campaign.query.order_by(Campaign.name).all()
    
    # 2. Crear estructura de datos para el JavaScript: { 'id_campaña': [lista_segmentos] }
    segments_by_campaign = {}
    for camp in campaigns:
        segments = Segment.query.filter_by(campaign_id=camp.id).all()
        segments_by_campaign[str(camp.id)] = [{'id': s.id, 'name': s.name} for s in segments]
    
    # 3. Enviar a la plantilla (IMPORTANTE: segments_by_campaign_json)
    return render_template(
        'scheduling.html',
        campaigns=campaigns,
        segments_by_campaign_json=json.dumps(segments_by_campaign)
    )

@bp.route('/calculator')
@login_required
def calculator():
    segments = Segment.query.options(joinedload(Segment.campaign)).all()
    return render_template(
        'calculator.html', 
        segments=segments
    )

@bp.route('/summary')
@login_required
def summary():
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    
    # Lógica de permisos: Admin ve todo, otros solo lo asignado
    if user.role == 'admin':
        campaigns = Campaign.query.order_by(Campaign.name).all()
    else:
        campaigns = user.campaigns

    # Construir diccionario para el selector dinámico
    segments_by_campaign = {}
    for camp in campaigns:
        segs = Segment.query.filter_by(campaign_id=camp.id).all()
        segments_by_campaign[str(camp.id)] = [{'id': s.id, 'name': s.name} for s in segs]
        
    return render_template(
        'summary.html', 
        campaigns=campaigns,
        segments_by_campaign_json=json.dumps(segments_by_campaign)
    )

# --- Rutas de Forecasting ---
@bp.route('/forecasting')
@login_required
def forecasting():
    campaigns = Campaign.query.all()
    return render_template('forecasting.html', campaigns=campaigns)

@bp.route('/intraday_forecaster')
@login_required
def intraday_forecaster():
    segments = Segment.query.options(joinedload(Segment.campaign)).all()
    return render_template('intraday_forecaster.html', segments=segments)

@bp.route('/monthly_forecaster')
@login_required
def monthly_forecaster():
    segments = Segment.query.options(joinedload(Segment.campaign)).all()
    return render_template('history.html', segments=segments)

@bp.route('/intramonth_forecaster')
@login_required
def intramonth_forecaster():
    segments = Segment.query.options(joinedload(Segment.campaign)).all()
    return render_template('intramonth_forecaster.html', segments=segments)

# --- Gestión de Cambios ---
@bp.route('/tl_dashboard')
@login_required
def tl_dashboard():
    return render_template('tl_dashboard.html')

@bp.route('/analyst_dashboard')
@login_required
def analyst_dashboard():
    if session.get('role') not in ['admin', 'analista']:
        return redirect(url_for('main.index'))
    pending_requests = ShiftChangeRequest.query.filter_by(status='PENDING').order_by(ShiftChangeRequest.created_at.desc()).all()
    return render_template('analyst_dashboard.html', requests=pending_requests)

@bp.route('/breaks')
@login_required
def breaks():
    segments = Segment.query.options(joinedload(Segment.campaign)).all()
    return render_template('breaks.html', segments=segments)