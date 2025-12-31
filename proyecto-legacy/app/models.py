# app/models.py

"""
Define todos los modelos de la base de datos SQLAlchemy para la aplicación.
Versión refactorizada con nombres de tablas explícitos para evitar errores de migración.
"""

from . import db
import datetime

# --- Tablas de Asociación ---

user_campaign_permissions = db.Table('user_campaign_permission',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('campaign_id', db.Integer, db.ForeignKey('campaign.id'), primary_key=True)
)

# --- Modelos de Base de Datos ---

class User(db.Model):
    __tablename__ = 'user' # Mantenemos singular por compatibilidad con tu auth existente
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(80), nullable=False, default='user')
    campaigns = db.relationship('Campaign', secondary=user_campaign_permissions, lazy='subquery',
                                backref=db.backref('users', lazy=True))

class Campaign(db.Model):
    __tablename__ = 'campaign' # Mantenemos singular por compatibilidad
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    country = db.Column(db.String(50), nullable=False)
    segments = db.relationship('Segment', backref='campaign', lazy=True, cascade="all, delete-orphan")

# --- MODELOS ACTUALIZADOS (PLURALIZADOS) ---

class Segment(db.Model):
    __tablename__ = 'segments'  # <--- NOMBRE EXPLÍCITO
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    service_type = db.Column(db.String(50), nullable=False, default='INBOUND')
    bo_sla_hours = db.Column(db.Integer, nullable=False, default=24)
    
    # Horarios
    lunes_apertura = db.Column(db.String(5)); lunes_cierre = db.Column(db.String(5))
    martes_apertura = db.Column(db.String(5)); martes_cierre = db.Column(db.String(5))
    miercoles_apertura = db.Column(db.String(5)); miercoles_cierre = db.Column(db.String(5))
    jueves_apertura = db.Column(db.String(5)); jueves_cierre = db.Column(db.String(5))
    viernes_apertura = db.Column(db.String(5)); viernes_cierre = db.Column(db.String(5))
    sabado_apertura = db.Column(db.String(5)); sabado_cierre = db.Column(db.String(5))
    domingo_apertura = db.Column(db.String(5)); domingo_cierre = db.Column(db.String(5))
    
    weekend_policy = db.Column(db.String(50), nullable=False, default='REQUIRE_ONE_DAY_OFF')
    min_full_weekends_off_per_month = db.Column(db.Integer, nullable=False, default=2)
    required_skills = db.Column(db.String(255), nullable=True, comment="Habilidades requeridas")

    staffing_results = db.relationship('StaffingResult', backref='segment', lazy=True, cascade="all, delete-orphan")
    __table_args__ = (db.UniqueConstraint('name', 'campaign_id', name='_name_campaign_uc'),)


class SchedulingRule(db.Model):
    __tablename__ = 'scheduling_rules' # <--- NOMBRE EXPLÍCITO
    
    id = db.Column(db.Integer, primary_key=True)
    rule_name = db.Column(db.String(120), unique=True, nullable=False)
    country_code = db.Column(db.String(2), nullable=False, index=True)
    weekly_hours = db.Column(db.Float, nullable=False)
    days_per_week = db.Column(db.Integer, nullable=False)
    min_daily_hours = db.Column(db.Float, nullable=False)
    max_daily_hours = db.Column(db.Float, nullable=False)
    max_consecutive_work_days = db.Column(db.Integer, nullable=True)
    min_full_weekends_off_per_month = db.Column(db.Integer, default=1)
    relevant_skills = db.Column(db.String(100), nullable=True)
    agents = db.relationship('Agent', backref='scheduling_rule', lazy='dynamic')


class Agent(db.Model):
    __tablename__ = 'agents' # <--- NOMBRE EXPLÍCITO (ESTO ARREGLA EL ERROR DE ABSENCE)
    
    id = db.Column(db.Integer, primary_key=True)
    identificacion = db.Column(db.String(50), unique=True, nullable=False)
    nombre_completo = db.Column(db.String(200), nullable=False)

    scheduling_rule_id = db.Column(db.Integer, db.ForeignKey('scheduling_rules.id'), nullable=False)
    skill = db.Column(db.String(50), default='INBOUND', nullable=False)

    segment_id = db.Column(db.Integer, db.ForeignKey('segments.id')) # Apunta a 'segments.id'
    segment = db.relationship('Segment', backref=db.backref('agents', lazy=True))
    
    centro = db.Column(db.String(100))
    turno_sugerido = db.Column(db.String(50))
    
    # Ventanas horarias
    ventana_lunes = db.Column(db.String(50))
    ventana_martes = db.Column(db.String(50))
    ventana_miercoles = db.Column(db.String(50))
    ventana_jueves = db.Column(db.String(50))
    ventana_viernes = db.Column(db.String(50))
    ventana_sabado = db.Column(db.String(50))
    ventana_domingo = db.Column(db.String(50))
    
    modalidad_finde = db.Column(db.String(20), default='UNICO')
    rotacion_mensual_domingo = db.Column(db.String(20), default='NORMAL')
    semanas_libres_finde = db.Column(db.String(20))
    fecha_alta = db.Column(db.Date, nullable=False, default=datetime.date(1900, 1, 1))
    fecha_baja = db.Column(db.Date, nullable=True)
    is_concrecion = db.Column(db.Boolean, default=False, nullable=False)
    scenario_id = db.Column(db.Integer, db.ForeignKey('scenarios.id'), nullable=True)
    is_simulated = db.Column(db.Boolean, default=False)


class Schedule(db.Model):
    __tablename__ = 'schedules'
    
    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.Integer, db.ForeignKey('agents.id'), nullable=False)
    schedule_date = db.Column(db.Date, nullable=False)
    
    # ... (resto de tus columnas de horas y descansos igual) ...
    shift = db.Column(db.String(50), default='LIBRE')
    hours = db.Column(db.Float, default=0.0)
    is_manual_edit = db.Column(db.Boolean, default=False)
    
    agent = db.relationship('Agent', backref=db.backref('schedule_entries', lazy=True))
    
    descanso1_he = db.Column(db.String(5), nullable=True); descanso1_hs = db.Column(db.String(5), nullable=True)
    descanso2_he = db.Column(db.String(5), nullable=True); descanso2_hs = db.Column(db.String(5), nullable=True)
    pvd1 = db.Column(db.String(5), nullable=True); pvd2 = db.Column(db.String(5), nullable=True)
    pvd3 = db.Column(db.String(5), nullable=True); pvd4 = db.Column(db.String(5), nullable=True)
    pvd5 = db.Column(db.String(5), nullable=True); pvd6 = db.Column(db.String(5), nullable=True)
    pvd7 = db.Column(db.String(5), nullable=True); pvd8 = db.Column(db.String(5), nullable=True)
    pvd9 = db.Column(db.String(5), nullable=True); pvd10 = db.Column(db.String(5), nullable=True)
    
    # Defino la columna scenario_id antes de usarla en args (buena práctica, aunque no estricta)
    scenario_id = db.Column(db.Integer, db.ForeignKey('scenarios.id'), nullable=True)

    # --- AQUÍ ESTÁ EL CAMBIO CLAVE ---
    # Antes: db.UniqueConstraint('agent_id', 'schedule_date', name='_agent_date_uc')
    # Ahora: Agregamos 'scenario_id' a la tupla
    __table_args__ = (
        db.UniqueConstraint('agent_id', 'schedule_date', 'scenario_id', name='_agent_date_scenario_uc'),
    )
    

class StaffingResult(db.Model):
    __tablename__ = 'staffing_results'
    id = db.Column(db.Integer, primary_key=True)
    result_date = db.Column(db.Date, nullable=False)
    # ... (tus columnas de datos siguen igual) ...
    agents_online = db.Column(db.Text, nullable=False)
    agents_total = db.Column(db.Text, nullable=False)
    calls_forecast = db.Column(db.Text, nullable=True)
    aht_forecast = db.Column(db.Text, nullable=True)
    reducers_forecast = db.Column(db.Text, nullable=True)
    
    segment_id = db.Column(db.Integer, db.ForeignKey('segments.id'), nullable=False)
    sla_target_percentage = db.Column(db.Float, nullable=True)
    sla_target_time = db.Column(db.Integer, nullable=True)
    
    # NUEVO: Vinculación obligatoria (o nullable temporalmente)
    scenario_id = db.Column(db.Integer, db.ForeignKey('scenarios.id'), nullable=True)

    # IMPORTANTE: La clave única ahora incluye scenario_id para evitar choques
    __table_args__ = (db.UniqueConstraint('result_date', 'segment_id', 'scenario_id', name='_date_seg_scen_uc'),)


class ActualsData(db.Model):
    __tablename__ = 'actuals_data'
    
    id = db.Column(db.Integer, primary_key=True)
    result_date = db.Column(db.Date, nullable=False)
    actuals_data = db.Column(db.Text, nullable=False)
    segment_id = db.Column(db.Integer, db.ForeignKey('segments.id'), nullable=False) # Apunta a 'segments.id'
    __table_args__ = (db.UniqueConstraint('result_date', 'segment_id', name='_date_segment_actuals_uc'),)

class BreakRule(db.Model):
    __tablename__ = 'break_rules'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    country = db.Column(db.String(50), nullable=False)
    min_shift_hours = db.Column(db.Float, nullable=False); max_shift_hours = db.Column(db.Float, nullable=False)
    break_duration_minutes = db.Column(db.Integer, default=0); pvd_minutes_per_hour = db.Column(db.Integer, default=0)
    number_of_pvds = db.Column(db.Integer, default=0)

class MonthlyForecast(db.Model):
    __tablename__ = 'monthly_forecasts'
    
    id = db.Column(db.Integer, primary_key=True)
    segment_id = db.Column(db.Integer, db.ForeignKey('segments.id'), nullable=False, unique=True) # Apunta a 'segments.id'
    forecast_pivot_data = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    segment = db.relationship('Segment', backref=db.backref('monthly_forecast', uselist=False, lazy=True))

class Absence(db.Model):
    __tablename__ = 'absences'
    
    id = db.Column(db.Integer, primary_key=True)
    # Claves foráneas corregidas:
    agent_id = db.Column(db.Integer, db.ForeignKey('agents.id'), nullable=False) 
    segment_id = db.Column(db.Integer, db.ForeignKey('segments.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    absence_code = db.Column(db.String(20), nullable=False)
    
    # Relaciones
    agent = db.relationship('Agent', backref=db.backref('stored_absences', lazy=True))
    segment = db.relationship('Segment', backref=db.backref('stored_absences', lazy=True))

class ShiftChangeRequest(db.Model):
    __tablename__ = 'shift_change_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.Integer, db.ForeignKey('agents.id'), nullable=False)
    requester_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # El TL
    
    request_date = db.Column(db.Date, nullable=False) # Día a cambiar
    current_shift = db.Column(db.String(50))          # Turno actual
    requested_shift = db.Column(db.String(50))        # Turno deseado
    reason_type = db.Column(db.String(50))            # Ej: "Cambio Turno", "Libranza", "Error"
    comment = db.Column(db.String(255))               # Observación del TL
    
    status = db.Column(db.String(20), default='PENDING') # PENDING, APPROVED, REJECTED
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    processed_at = db.Column(db.DateTime)
    processed_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # El Analista
    
    # Relaciones
    agent = db.relationship('Agent', backref='requests')
    requester = db.relationship('User', foreign_keys=[requester_id], backref='requests_created')
    processor = db.relationship('User', foreign_keys=[processed_by], backref='requests_processed')    

class Scenario(db.Model):
    __tablename__ = 'scenarios'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    segment_id = db.Column(db.Integer, db.ForeignKey('segments.id'), nullable=False)
    is_official = db.Column(db.Boolean, default=False)
    
    # --- NUEVOS CAMPOS PARA FILTRADO ---
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    staffing_results = db.relationship('StaffingResult', backref='scenario', cascade="all, delete-orphan")
    schedules = db.relationship('Schedule', backref='scenario', cascade="all, delete-orphan")
    simulated_agents = db.relationship('Agent', backref='scenario', cascade="all, delete-orphan")