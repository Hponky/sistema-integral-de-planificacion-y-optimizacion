"""
Definiciones de modelos de base de datos para la aplicación SIPO.
"""

# Importamos db de manera local para evitar problemas de importación circular
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import json
import pandas as pd
import numpy as np
from sqlalchemy.orm import joinedload
from sqlalchemy import or_, not_

# Constantes
VALID_AUSENCIA_CODES = ["VAC", "BMED", "LICMATER", "LICPATER", "LACT", "FEST", "ACC", "ENF", "ENFHOSP", "SIT-ESP", "OTRO"]

# Tabla de asociación para permisos de usuario-campaña
user_campaign_permissions = db.Table('user_campaign_permission',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('campaign_id', db.Integer, db.ForeignKey('campaign.id'), primary_key=True)
)

# --- MODELOS DE BASE DE DATOS ---
class User(db.Model):
    """Modelo para usuarios del sistema."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(80), nullable=False, default='user')
    campaigns = db.relationship('Campaign', secondary=user_campaign_permissions, lazy='subquery',
                                backref=db.backref('users', lazy=True))

    def set_password(self, password):
        """Genera el hash de la contraseña."""
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        """Verifica la contraseña."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Campaign(db.Model):
    """Modelo para campañas."""
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    country = db.Column(db.String(50), nullable=False)
    segments = db.relationship('Segment', backref='campaign', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Campaign {self.name}>'

class Segment(db.Model):
    """Modelo para segmentos dentro de una campaña."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    lunes_apertura = db.Column(db.String(5)); lunes_cierre = db.Column(db.String(5))
    martes_apertura = db.Column(db.String(5)); martes_cierre = db.Column(db.String(5))
    miercoles_apertura = db.Column(db.String(5)); miercoles_cierre = db.Column(db.String(5))
    jueves_apertura = db.Column(db.String(5)); jueves_cierre = db.Column(db.String(5))
    viernes_apertura = db.Column(db.String(5)); viernes_cierre = db.Column(db.String(5))
    sabado_apertura = db.Column(db.String(5)); sabado_cierre = db.Column(db.String(5))
    domingo_apertura = db.Column(db.String(5)); domingo_cierre = db.Column(db.String(5))
    weekend_policy = db.Column(db.String(50), nullable=False, default='REQUIRE_ONE_DAY_OFF')
    min_full_weekends_off_per_month = db.Column(db.Integer, nullable=False, default=2)
    staffing_results = db.relationship('StaffingResult', backref='segment', lazy=True, cascade="all, delete-orphan")
    __table_args__ = (db.UniqueConstraint('name', 'campaign_id', name='_name_campaign_uc'),)

    def __repr__(self):
        return f'<Segment {self.name} (Campaign: {self.campaign_id})>'

class StaffingResult(db.Model):
    """Modelo para almacenar los resultados de dimensionamiento."""
    id = db.Column(db.Integer, primary_key=True)
    result_date = db.Column(db.Date, nullable=False)
    agents_online = db.Column(db.Text, nullable=False) # JSON con agentes efectivos requeridos por intervalo
    agents_total = db.Column(db.Text, nullable=False)  # JSON con agentes dimensionados totales por intervalo
    calls_forecast = db.Column(db.Text, nullable=True) # JSON con llamadas pronosticadas por intervalo
    aht_forecast = db.Column(db.Text, nullable=True)   # JSON con AHT pronosticado por intervalo
    reducers_forecast = db.Column(db.Text, nullable=True) # JSON con reductores (absentismo, shrinkage, auxiliares)
    segment_id = db.Column(db.Integer, db.ForeignKey('segment.id'), nullable=False)
    sla_target_percentage = db.Column(db.Float, nullable=True) # SLA objetivo usado para el cálculo
    sla_target_time = db.Column(db.Integer, nullable=True)     # SLA tiempo usado para el cálculo
    __table_args__ = (db.UniqueConstraint('result_date', 'segment_id', name='_date_segment_uc'),)

    def __repr__(self):
        return f'<StaffingResult {self.result_date} for Segment {self.segment_id}>'

class ActualsData(db.Model):
    """Modelo para almacenar datos reales (actuals) por intervalo."""
    id = db.Column(db.Integer, primary_key=True)
    result_date = db.Column(db.Date, nullable=False)
    actuals_data = db.Column(db.Text, nullable=False) # JSON con datos reales por intervalo
    segment_id = db.Column(db.Integer, db.ForeignKey('segment.id'), nullable=False)
    __table_args__ = (db.UniqueConstraint('result_date', 'segment_id', name='_date_segment_actuals_uc'),)

    def __repr__(self):
        return f'<ActualsData {self.result_date} for Segment {self.segment_id}>'

class Agent(db.Model):
    """Modelo para agentes."""
    id = db.Column(db.Integer, primary_key=True)
    identificacion = db.Column(db.String(50), unique=True, nullable=False)
    nombre_completo = db.Column(db.String(200), nullable=False)
    segment_id = db.Column(db.Integer, db.ForeignKey('segment.id'))
    segment = db.relationship('Segment', backref=db.backref('agents', lazy=True))
    centro = db.Column(db.String(100)); contrato = db.Column(db.String(20))
    turno_sugerido = db.Column(db.String(50)); jornada = db.Column(db.String(50))
    concrecion = db.Column(db.String(100)); rotacion_finde = db.Column(db.String(10))
    ventana_horaria = db.Column(db.String(50)); modalidad_finde = db.Column(db.String(20), default='UNICO')
    rotacion_mensual_domingo = db.Column(db.String(20), default='NORMAL')
    semanas_libres_finde = db.Column(db.String(20))
    fecha_alta = db.Column(db.Date, nullable=False, default=datetime.date(1900, 1, 1))
    fecha_baja = db.Column(db.Date, nullable=True)

    def __repr__(self):
        return f'<Agent {self.nombre_completo} ({self.identificacion})>'

class SchedulingRule(db.Model):
    """Modelo para reglas de scheduling."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    country = db.Column(db.String(50), nullable=False)
    workday_rule = db.relationship('WorkdayRule', backref='scheduling_rule', uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<SchedulingRule {self.name}>'

class WorkdayRule(db.Model):
    """Modelo para reglas de jornada laboral asociadas a SchedulingRule."""
    id = db.Column(db.Integer, primary_key=True)
    weekly_hours = db.Column(db.Float, nullable=False)
    max_daily_hours = db.Column(db.Float, nullable=False); min_daily_hours = db.Column(db.Float, nullable=False)
    days_per_week = db.Column(db.Integer, nullable=False, default=5)
    max_consecutive_work_days = db.Column(db.Integer, nullable=False, default=7)
    min_hours_between_shifts = db.Column(db.Integer, nullable=False, default=12)
    allow_irregular_shifts = db.Column(db.Boolean, nullable=False, default=False)
    rule_id = db.Column(db.Integer, db.ForeignKey('scheduling_rule.id'), nullable=False)

    def __repr__(self):
        return f'<WorkdayRule for Rule {self.rule_id}>'

class Schedule(db.Model):
    """Modelo para los horarios asignados a los agentes."""
    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.Integer, db.ForeignKey('agent.id'), nullable=False)
    schedule_date = db.Column(db.Date, nullable=False)
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
    __table_args__ = (db.UniqueConstraint('agent_id', 'schedule_date', name='_agent_date_uc'),)

    def __repr__(self):
        return f'<Schedule {self.schedule_date} for Agent {self.agent_id}: {self.shift}>'

class BreakRule(db.Model):
    """Modelo para reglas de descanso."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    country = db.Column(db.String(50), nullable=False)
    min_shift_hours = db.Column(db.Float, nullable=False); max_shift_hours = db.Column(db.Float, nullable=False)
    break_duration_minutes = db.Column(db.Integer, default=0); pvd_minutes_per_hour = db.Column(db.Integer, default=0)
    number_of_pvds = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<BreakRule {self.name} ({self.country})>'
