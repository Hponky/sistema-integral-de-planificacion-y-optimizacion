"""
Definiciones de modelos de base de datos para la aplicación 
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

# --- MODELOS DE BASE DE DATOS ---
class Campaign(db.Model):
    """Modelo para campañas."""
    id = db.Column(db.Integer, db.Sequence('campaign_id_seq'), primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    country = db.Column(db.String(50), nullable=False)
    segments = db.relationship('Segment', backref='campaign', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Campaign {self.name}>'

class Segment(db.Model):
    """Modelo para segmentos dentro de una campaña."""
    id = db.Column(db.Integer, db.Sequence('segment_id_seq'), primary_key=True)
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
    __table_args__ = (db.UniqueConstraint('name', 'campaign_id', name='_name_campaign_uc'),)

    def __repr__(self):
        return f'<Segment {self.name} (Campaign: {self.campaign_id})>'

class DimensioningScenario(db.Model):
    """Modelo para agrupar un cálculo de dimensionamiento completo."""
    id = db.Column(db.Integer, db.Sequence('dim_scenario_id_seq'), primary_key=True)
    segment_id = db.Column(db.Integer, db.ForeignKey('segment.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    parameters = db.Column(db.Text, nullable=False) # JSON con parámetros (SLA, fechas, etc.)
    
    # Información del usuario de Active Directory que creó este escenario
    id_legal = db.Column(db.String(50), nullable=True, index=True)  # IdLegal del usuario en AD
    username = db.Column(db.String(100), nullable=True)  # Nombre de usuario para referencia
    
    # Datos de resultados (Las 4 tablas principales + KPIs)
    agents_online = db.Column(db.Text, nullable=True)   # JSON con agentes efectivos (CLOB en Oracle)
    agents_total = db.Column(db.Text, nullable=True)    # JSON con agentes dimensionados (CLOB en Oracle)
    agents_present = db.Column(db.Text, nullable=True)  # JSON con agentes presentes (CLOB en Oracle)
    agents_logged = db.Column(db.Text, nullable=True)   # JSON con agentes logados (CLOB en Oracle)
    calls_forecast = db.Column(db.Text, nullable=True)  # New: Persist original calls volume
    aht_forecast = db.Column(db.Text, nullable=True)    # New: Persist original AHT
    kpis_data = db.Column(db.Text, nullable=True)       # JSON con resumen de KPIs (CLOB en Oracle)

    segment = db.relationship('Segment', backref='dimensioning_scenarios', lazy=True)

    def __repr__(self):
        return f'<DimensioningScenario {self.id} - Segment {self.segment_id} - {self.created_at}>'

class PlanningScenario(db.Model):
    """Modelo para guardar escenarios de planificacion generados (historial)."""
    id = db.Column(db.Integer, db.Sequence('plan_scenario_id_seq'), primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    name = db.Column(db.String(200), nullable=True) 
    
    # User info
    id_legal = db.Column(db.String(50), nullable=True, index=True)
    username = db.Column(db.String(100), nullable=True)

    # Context
    start_date = db.Column(db.Date, nullable=False)
    days_count = db.Column(db.Integer, default=30)
    
    # Data blobs (Store as JSON strings)
    schedule_data = db.Column(db.Text, nullable=False) # The full schedule JSON
    metrics_data = db.Column(db.Text, nullable=True) 
    kpis_data = db.Column(db.Text, nullable=True) 

    # Temporary / Simulation Support
    is_temporary = db.Column(db.Boolean, default=False)
    expires_at = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<PlanningScenario {self.id} - {self.name}>'
    
    def to_dict(self):
        dim_id = None
        if self.metrics_data:
            try:
                # Basic check to avoid parsing huge JSON if not needed, but here we need it.
                # Since metrics_data is usually not huge compared to schedule_data, it's acceptable.
                m = json.loads(self.metrics_data)
                if isinstance(m, dict):
                    dim_id = m.get('dimensioning_scenario_id')
            except: 
                pass

        return {
            'id': self.id,
            'name': self.name,
            'isTemporary': self.is_temporary,
            'dimensioningScenarioId': dim_id,
            'expiresAt': self.expires_at.isoformat() if self.expires_at else None,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'startDate': self.start_date.strftime('%Y-%m-%d') if self.start_date else None,
            'daysCount': self.days_count,
            'username': self.username,
            'idLegal': self.id_legal
        }

class ForecastingCurve(db.Model):
    """Modelo para almacenar curvas de forecasting intradía por segmento."""
    id = db.Column(db.Integer, db.Sequence('forecasting_curve_id_seq'), primary_key=True)
    segment_id = db.Column(db.Integer, db.ForeignKey('segment.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    name = db.Column(db.String(200), nullable=False)  # Nombre descriptivo del forecast
    
    # Información del usuario de Active Directory que creó este forecast
    id_legal = db.Column(db.String(50), nullable=True, index=True)
    username = db.Column(db.String(100), nullable=True)
    
    # Curvas por día de la semana (0=Lunes, 6=Domingo)
    # Cada curva es un JSON con formato: {"HH:MM": peso_porcentual, ...}
    monday_curve = db.Column(db.Text, nullable=True)
    tuesday_curve = db.Column(db.Text, nullable=True)
    wednesday_curve = db.Column(db.Text, nullable=True)
    thursday_curve = db.Column(db.Text, nullable=True)
    friday_curve = db.Column(db.Text, nullable=True)
    saturday_curve = db.Column(db.Text, nullable=True)
    sunday_curve = db.Column(db.Text, nullable=True)
    
    # Etiquetas de tiempo (intervalos) usadas en las curvas
    time_labels = db.Column(db.Text, nullable=False)  # JSON array: ["08:00", "08:30", ...]
    
    # Metadata adicional
    weeks_analyzed = db.Column(db.Integer, nullable=True)  # Número de semanas analizadas
    analysis_date_range = db.Column(db.String(100), nullable=True)  # Rango de fechas analizadas
    
    # Relación con segmento
    segment = db.relationship('Segment', backref='forecasting_curves', lazy=True)
    
    # Índice único para evitar duplicados por nombre y segmento
    __table_args__ = (db.UniqueConstraint('name', 'segment_id', name='_name_segment_forecast_uc'),)

    def __repr__(self):
        return f'<ForecastingCurve {self.name} - Segment {self.segment_id}>'
    
    def get_curve_for_day(self, day_of_week):
        """Obtiene la curva para un día específico (0=Lunes, 6=Domingo)."""
        curve_columns = [
            self.monday_curve, self.tuesday_curve, self.wednesday_curve,
            self.thursday_curve, self.friday_curve, self.saturday_curve, self.sunday_curve
        ]
        
        if 0 <= day_of_week <= 6:
            curve_json = curve_columns[day_of_week]
            return json.loads(curve_json) if curve_json else {}
        return {}
    
    def set_curve_for_day(self, day_of_week, curve_dict):
        """Establece la curva para un día específico."""
        curve_json = json.dumps(curve_dict)
        
        if day_of_week == 0:
            self.monday_curve = curve_json
        elif day_of_week == 1:
            self.tuesday_curve = curve_json
        elif day_of_week == 2:
            self.wednesday_curve = curve_json
        elif day_of_week == 3:
            self.thursday_curve = curve_json
        elif day_of_week == 4:
            self.friday_curve = curve_json
        elif day_of_week == 5:
            self.saturday_curve = curve_json
        elif day_of_week == 6:
            self.sunday_curve = curve_json
    
    def to_dict(self):
        """Convierte el modelo a diccionario para API responses."""
        return {
            'id': self.id,
            'segment_id': self.segment_id,
            'name': self.name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'id_legal': self.id_legal,
            'username': self.username,
            'curves': {
                '0': json.loads(self.monday_curve) if self.monday_curve else {},
                '1': json.loads(self.tuesday_curve) if self.tuesday_curve else {},
                '2': json.loads(self.wednesday_curve) if self.wednesday_curve else {},
                '3': json.loads(self.thursday_curve) if self.thursday_curve else {},
                '4': json.loads(self.friday_curve) if self.friday_curve else {},
                '5': json.loads(self.saturday_curve) if self.saturday_curve else {},
                '6': json.loads(self.sunday_curve) if self.sunday_curve else {}
            },
            'time_labels': json.loads(self.time_labels) if self.time_labels else [],
            'weeks_analyzed': self.weeks_analyzed,
            'analysis_date_range': self.analysis_date_range
        }

class ForecastedDistribution(db.Model):
    """Modelo para almacenar el RESULTADO final de la distribución (Llamadas Esperadas)."""
    id = db.Column(db.Integer, db.Sequence('forecast_dist_id_seq'), primary_key=True)
    segment_id = db.Column(db.Integer, db.ForeignKey('segment.id'), nullable=False)
    curve_id = db.Column(db.Integer, db.ForeignKey('forecasting_curve.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    # Metadata para matching
    id_legal = db.Column(db.String(50), nullable=True, index=True)
    username = db.Column(db.String(100), nullable=True)
    campaign_code = db.Column(db.String(50), nullable=True)
    
    # Rango de fechas que cubre esta distribución
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    
    # Datos
    distribution_data = db.Column(db.Text, nullable=False) # JSON: {date: {time: volume}}
    time_labels = db.Column(db.Text, nullable=False) # JSON: ["00:00", "00:30" ...]
    
    # Campo para selección explícita
    is_selected = db.Column(db.Boolean, default=False)

    segment = db.relationship('Segment', backref='forecast_distributions', lazy=True)
    
    def __repr__(self):
        return f'<ForecastedDistribution {self.id} - Segment {self.segment_id} ({self.start_date} to {self.end_date})>'

class ActualsData(db.Model):
    """Modelo para almacenar datos reales (actuals) por intervalo."""
    id = db.Column(db.Integer, db.Sequence('actuals_data_id_seq'), primary_key=True)
    result_date = db.Column(db.Date, nullable=False)
    actuals_data = db.Column(db.Text, nullable=False) # JSON con datos reales por intervalo
    segment_id = db.Column(db.Integer, db.ForeignKey('segment.id'), nullable=False)
    __table_args__ = (db.UniqueConstraint('result_date', 'segment_id', name='_date_segment_actuals_uc'),)

    def __repr__(self):
        return f'<ActualsData {self.result_date} for Segment {self.segment_id}>'

class Agent(db.Model):
    """Modelo para agentes."""
    id = db.Column(db.Integer, db.Sequence('agent_id_seq'), primary_key=True)
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
    id = db.Column(db.Integer, db.Sequence('scheduling_rule_id_seq'), primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    country = db.Column(db.String(50), nullable=False)
    workday_rule = db.relationship('WorkdayRule', backref='scheduling_rule', uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<SchedulingRule {self.name}>'

class WorkdayRule(db.Model):
    """Modelo para reglas de jornada laboral asociadas a SchedulingRule."""
    id = db.Column(db.Integer, db.Sequence('workday_rule_id_seq'), primary_key=True)
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
    id = db.Column(db.Integer, db.Sequence('schedule_id_seq'), primary_key=True)
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
    id = db.Column(db.Integer, db.Sequence('break_rule_id_seq'), primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    country = db.Column(db.String(50), nullable=False)
    min_shift_hours = db.Column(db.Float, nullable=False); max_shift_hours = db.Column(db.Float, nullable=False)
    break_duration_minutes = db.Column(db.Integer, default=0); pvd_minutes_per_hour = db.Column(db.Integer, default=0)
    number_of_pvds = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<BreakRule {self.name} ({self.country})>'
