"""
Configuración y fixtures comunes para pruebas del backend SIPO.
"""

import os
import tempfile
import pytest
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sipo.app import create_app
from sipo.models import db
from sipo.config import TestingConfig


@pytest.fixture(scope='session')
def app():
    """
    Fixture que proporciona una instancia de la aplicación Flask para pruebas.
    Utiliza la configuración de testing para asegurar aislamiento.
    """
    app = create_app('testing')
    app.config['TESTING'] = True
    
    with app.app_context():
        db.create_all()
        db.session.commit()
    
    yield app
    
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='session')
def client(app):
    """
    Fixture que proporciona un cliente de prueba para la aplicación Flask.
    Permite simular solicitudes HTTP sin necesidad de un servidor real.
    """
    return app.test_client()


@pytest.fixture(scope='function')
def session(app):
    """
    Fixture que proporciona una sesión de base de datos para pruebas.
    Utiliza la misma base de datos que se crea en el fixture app.
    """
    with app.app_context():
        connection = db.engine.connect()
        transaction = connection.begin()
        session = db.session(bind=connection)
        
        yield session
        
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope='function')
def sample_user():
    """
    Fixture que proporciona un usuario de ejemplo para pruebas.
    """
    from sipo.models import User
    
    user = User(
        username='testuser',
        email='test@example.com',
        password_hash='hashed_password'
    )
    
    yield user


@pytest.fixture(scope='function')
def sample_campaign():
    """
    Fixture que proporciona una campaña de ejemplo para pruebas.
    """
    from sipo.models import Campaign
    
    campaign = Campaign(
        code='TEST-CAMPAIGN',
        name='Test Campaign',
        description='Campaign for testing purposes'
    )
    
    yield campaign


@pytest.fixture(scope='function')
def sample_segment():
    """
    Fixture que proporciona un segmento de ejemplo para pruebas.
    """
    from sipo.models import Segment
    
    segment = Segment(
        campaign_id=None,
        name='Test Segment',
        start_time='09:00',
        end_time='18:00',
        days_of_week='mon,tue,wed,thu,fri',
        weekend_policy='ignore'
    )
    
    yield segment


@pytest.fixture(scope='function')
def sample_agent():
    """
    Fixture que proporciona un agente de ejemplo para pruebas.
    """
    from sipo.models import Agent
    
    agent = Agent(
        agent_id='TEST-AGENT-001',
        name='Test Agent',
        hire_date='2023-01-01',
        termination_date=None
    )
    
    yield agent


@pytest.fixture(scope='function')
def sample_staffing_result():
    """
    Fixture que proporciona un resultado de staffing de ejemplo para pruebas.
    """
    from sipo.models import StaffingResult
    import json
    from datetime import datetime
    
    staffing_result = StaffingResult(
        segment_id=None,
        date=datetime.now().date(),
        result_data=json.dumps({
            'agents': 10,
            'required_agents': 8,
            'service_level': 0.85,
            'occupancy': 0.8
        })
    )
    
    yield staffing_result


@pytest.fixture(scope='function')
def sample_actuals_data():
    """
    Fixture que proporciona datos actuales de ejemplo para pruebas.
    """
    from sipo.models import ActualsData
    import json
    from datetime import datetime
    
    actuals_data = ActualsData(
        segment_id=None,
        date=datetime.now().date(),
        actuals=json.dumps({
            'agents': 9,
            'calls_handled': 850,
            'aht': 180
        })
    )
    
    yield actuals_data


@pytest.fixture(scope='function')
def sample_schedule():
    """
    Fixture que proporciona un horario de ejemplo para pruebas.
    """
    from sipo.models import Schedule
    from datetime import datetime, time
    
    schedule = Schedule(
        agent_id=None,
        date=datetime.now().date(),
        start_time=time(9, 0),
        end_time=time(17, 30),
        break_start_time=time(13, 0),
        break_end_time=time(13, 30),
        shift_type='regular'
    )
    
    yield schedule


@pytest.fixture
def mock_excel_file():
    """
    Fixture que proporciona un archivo Excel de ejemplo para pruebas.
    Crea un archivo temporal con datos de prueba.
    """
    import pandas as pd
    from io import BytesIO
    
    data = {
        'Hora': [9, 10, 11, 12, 13, 14, 15, 16],
        'Llamadas Recibidas': [100, 120, 110, 130, 140, 150, 160, 170],
        'AHT Promedio': [180, 175, 190, 185, 195, 200, 205],
        'Agentes Requeridos': [8, 9, 10, 11, 12, 13, 14, 15, 16]
    }
    
    df = pd.DataFrame(data)
    
    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Datos', index=False)
    
    excel_buffer.seek(0)
    return excel_buffer.getvalue()


@pytest.fixture
def mock_invalid_excel_file():
    """
    Fixture que proporciona un archivo Excel inválido para pruebas de manejo de errores.
    """
    import pandas as pd
    from io import BytesIO
    
    data = {
        'Hora': ['texto', 'no_numérico'],
        'Llamadas Recibidas': ['no_numérico'],
        'AHT Promedio': ['negativo'],
        'Agentes Requeridos': ['texto']
    }
    
    df = pd.DataFrame(data)
    
    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Datos Inválidos', index=False)
    
    excel_buffer.seek(0)
    return excel_buffer.getvalue()


@pytest.fixture
def authenticated_client(client, sample_user):
    """
    Fixture que proporciona un cliente autenticado para pruebas.
    """
    with client.session_transaction() as sess:
        sess['user_id'] = sample_user.id
        sess['username'] = sample_user.username
    
    yield client


@pytest.fixture
def admin_client(client, sample_user):
    """
    Fixture que proporciona un cliente con privilegios de administrador para pruebas.
    """
    with client.session_transaction() as sess:
        sess['user_id'] = sample_user.id
        sess['username'] = sample_user.username
        sess['is_admin'] = True
    
    yield client