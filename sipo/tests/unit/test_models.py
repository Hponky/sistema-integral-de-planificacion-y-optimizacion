"""
Pruebas unitarias para los modelos de datos de la aplicación 
"""

import pytest
import datetime
from unittest.mock import patch
from models import (
    Campaign, Segment, StaffingResult, ActualsData,
    Agent, SchedulingRule, WorkdayRule, Schedule, BreakRule
)


class TestCampaign:
    """Pruebas para el modelo Campaign."""
    
    def test_campaign_creation(self, session):
        """Prueba la creación de una campaña."""
        campaign = Campaign(
            code="TEST001",
            name="Campaña de Prueba",
            country="CO"
        )
        session.add(campaign)
        session.commit()
        
        retrieved_campaign = Campaign.query.filter_by(code="TEST001").first()
        assert retrieved_campaign is not None
        assert retrieved_campaign.name == "Campaña de Prueba"
        assert retrieved_campaign.country == "CO"
    
    def test_campaign_repr(self, session):
        """Prueba la representación string de la campaña."""
        campaign = Campaign(
            code="TEST002",
            name="TEST002",
            country="MX"
        )
        session.add(campaign)
        session.commit()
        
        assert str(campaign) == "<Campaign TEST002>"
    
    def test_campaign_unique_code(self, session):
        """Prueba que los códigos de campaña deben ser únicos."""
        campaign1 = Campaign(
            code="DUPLICATE",
            name="Campaña 1",
            country="CO"
        )
        session.add(campaign1)
        session.commit()
        
        campaign2 = Campaign(
            code="DUPLICATE",
            name="Campaña 2",
            country="MX"
        )
        session.add(campaign2)
        
        with pytest.raises(Exception):  # SQLAlchemy lanzará una excepción por constraint
            session.commit()
    
    def test_campaign_segment_relationship(self, session):
        """Prueba la relación con segmentos."""
        campaign = Campaign(
            code="TEST003",
            name="Campaña con Segmentos",
            country="CO"
        )
        session.add(campaign)
        session.commit()
        
        segment = Segment(
            name="Segmento de Prueba",
            campaign_id=campaign.id,
            lunes_apertura="08:00",
            lunes_cierre="18:00"
        )
        session.add(segment)
        session.commit()
        
        retrieved_campaign = Campaign.query.filter_by(code="TEST003").first()
        assert len(retrieved_campaign.segments) == 1
        assert retrieved_campaign.segments[0].name == "Segmento de Prueba"


class TestSegment:
    """Pruebas para el modelo Segment."""
    
    def test_segment_creation(self, session):
        """Prueba la creación de un segmento."""
        campaign = Campaign(
            code="TEST_SEGMENT_CREATION",
            name="Campaña para Segmento Creación",
            country="CO"
        )
        session.add(campaign)
        session.commit()
        
        segment = Segment(
            name="Segmento de Prueba Creación",
            campaign_id=campaign.id,
            lunes_apertura="08:00",
            lunes_cierre="18:00",
            martes_apertura="08:00",
            martes_cierre="18:00",
            miercoles_apertura="08:00",
            miercoles_cierre="18:00",
            jueves_apertura="08:00",
            jueves_cierre="18:00",
            viernes_apertura="08:00",
            viernes_cierre="18:00",
            sabado_apertura="CERRADO",
            sabado_cierre="CERRADO",
            domingo_apertura="CERRADO",
            domingo_cierre="CERRADO",
            weekend_policy="REQUIRE_ONE_DAY_OFF",
            min_full_weekends_off_per_month=2
        )
        session.add(segment)
        session.commit()
        
        retrieved_segment = Segment.query.filter_by(name="Segmento de Prueba Creación").first()
        assert retrieved_segment is not None
        # Verificar que el segmento está asociado a la campaña correcta
        assert retrieved_segment.campaign.name == "Campaña para Segmento Creación"
        assert retrieved_segment.weekend_policy == "REQUIRE_ONE_DAY_OFF"
        assert retrieved_segment.min_full_weekends_off_per_month == 2
    
    def test_segment_repr(self, session):
        """Prueba la representación string del segmento."""
        campaign = Campaign(
            code="TEST005",
            name="Campaña para Repr",
            country="CO"
        )
        session.add(campaign)
        session.commit()
        
        segment = Segment(
            name="Segmento de Repr",
            campaign_id=campaign.id,
            lunes_apertura="08:00",
            lunes_cierre="18:00"
        )
        session.add(segment)
        session.commit()
        
        assert str(segment) == f"<Segment Segmento de Repr (Campaign: {campaign.id})>"
    
    def test_segment_unique_name_per_campaign(self, session):
        """Prueba que los nombres de segmento deben ser únicos por campaña."""
        campaign = Campaign(
            code="TEST006",
            name="Campaña para Segmento Único",
            country="CO"
        )
        session.add(campaign)
        session.commit()
        
        segment1 = Segment(
            name="Segmento Duplicado",
            campaign_id=campaign.id,
            lunes_apertura="08:00",
            lunes_cierre="18:00"
        )
        session.add(segment1)
        session.commit()
        
        segment2 = Segment(
            name="Segmento Duplicado",
            campaign_id=campaign.id,
            martes_apertura="08:00",
            martes_cierre="18:00"
        )
        session.add(segment2)
        
        with pytest.raises(Exception):  # SQLAlchemy lanzará una excepción por constraint
            session.commit()
    
    def test_segment_staffing_results_relationship(self, session):
        """Prueba la relación con resultados de staffing."""
        campaign = Campaign(
            code="TEST007",
            name="Campaña con Resultados",
            country="CO"
        )
        session.add(campaign)
        session.commit()
        
        segment = Segment(
            name="Segmento con Resultados",
            campaign_id=campaign.id,
            lunes_apertura="08:00",
            lunes_cierre="18:00"
        )
        session.add(segment)
        session.commit()
        
        staffing_result = StaffingResult(
            result_date=datetime.date(2023, 1, 1),
            segment_id=segment.id,
            agents_online='{"interval1": 10, "interval2": 12}',
            agents_total='{"interval1": 15, "interval2": 18}',
            calls_forecast='{"interval1": 100, "interval2": 120}',
            aht_forecast='{"interval1": 300, "interval2": 360}',
            reducers_forecast='{"interval1": 2, "interval2": 3}'
        )
        session.add(staffing_result)
        session.commit()
        
        retrieved_segment = Segment.query.filter_by(name="Segmento con Resultados").first()
        assert len(retrieved_segment.staffing_results) == 1
        assert retrieved_segment.staffing_results[0].result_date == datetime.date(2023, 1, 1)


class TestStaffingResult:
    """Pruebas para el modelo StaffingResult."""
    
    def test_staffing_result_creation(self, session):
        """Prueba la creación de un resultado de staffing."""
        campaign = Campaign(
            code="TEST008",
            name="Campaña para Staffing",
            country="CO"
        )
        session.add(campaign)
        session.commit()
        
        segment = Segment(
            name="Segmento para Staffing",
            campaign_id=campaign.id,
            lunes_apertura="08:00",
            lunes_cierre="18:00"
        )
        session.add(segment)
        session.commit()
        
        staffing_result = StaffingResult(
            result_date=datetime.date(2023, 1, 1),
            segment_id=segment.id,
            agents_online='{"interval1": 10, "interval2": 12}',
            agents_total='{"interval1": 15, "interval2": 18}',
            calls_forecast='{"interval1": 100, "interval2": 120}',
            aht_forecast='{"interval1": 300, "interval2": 360}',
            reducers_forecast='{"interval1": 2, "interval2": 3}',
            sla_target_percentage=85.0,
            sla_target_time=20
        )
        session.add(staffing_result)
        session.commit()
        
        retrieved_result = StaffingResult.query.filter_by(
            result_date=datetime.date(2023, 1, 1),
            segment_id=segment.id
        ).first()
        assert retrieved_result is not None
        assert retrieved_result.agents_online == '{"interval1": 10, "interval2": 12}'
        assert retrieved_result.sla_target_percentage == 85.0
        assert retrieved_result.sla_target_time == 20
    
    def test_staffing_result_unique_date_segment(self, session):
        """Prueba que las combinaciones de fecha y segmento deben ser únicas."""
        campaign = Campaign(
            code="TEST009",
            name="Campaña para Staffing Único",
            country="CO"
        )
        session.add(campaign)
        session.commit()
        
        segment = Segment(
            name="Segmento para Staffing Único",
            campaign_id=campaign.id,
            lunes_apertura="08:00",
            lunes_cierre="18:00"
        )
        session.add(segment)
        session.commit()
        
        staffing_result1 = StaffingResult(
            result_date=datetime.date(2023, 1, 1),
            segment_id=segment.id,
            agents_online='{"interval1": 10}',
            agents_total='{"interval1": 15}'
        )
        session.add(staffing_result1)
        session.commit()
        
        staffing_result2 = StaffingResult(
            result_date=datetime.date(2023, 1, 1),
            segment_id=segment.id,
            agents_online='{"interval2": 12}',
            agents_total='{"interval2": 18}'
        )
        session.add(staffing_result2)
        
        with pytest.raises(Exception):  # SQLAlchemy lanzará una excepción por constraint
            session.commit()
    
    def test_staffing_result_json_fields(self, session):
        """Prueba que los campos JSON se almacenan correctamente."""
        campaign = Campaign(
            code="TEST010",
            name="Campaña para JSON",
            country="CO"
        )
        session.add(campaign)
        session.commit()
        
        segment = Segment(
            name="Segmento para JSON",
            campaign_id=campaign.id,
            lunes_apertura="08:00",
            lunes_cierre="18:00"
        )
        session.add(segment)
        session.commit()
        
        test_json = '{"interval1": 10, "interval2": 12, "interval3": 15}'
        staffing_result = StaffingResult(
            result_date=datetime.date(2023, 1, 1),
            segment_id=segment.id,
            agents_online=test_json,
            agents_total=test_json,
            calls_forecast=test_json,
            aht_forecast=test_json,
            reducers_forecast=test_json
        )
        session.add(staffing_result)
        session.commit()
        
        retrieved_result = StaffingResult.query.filter_by(
            result_date=datetime.date(2023, 1, 1),
            segment_id=segment.id
        ).first()
        assert retrieved_result.agents_online == test_json
        assert retrieved_result.agents_total == test_json
        assert retrieved_result.calls_forecast == test_json
        assert retrieved_result.aht_forecast == test_json
        assert retrieved_result.reducers_forecast == test_json
    
    def test_staffing_result_repr(self, session):
        """Prueba la representación string del resultado de staffing."""
        campaign = Campaign(
            code="TEST011",
            name="Campaña para Repr Staffing",
            country="CO"
        )
        session.add(campaign)
        session.commit()
        
        segment = Segment(
            name="Segmento para Repr Staffing",
            campaign_id=campaign.id,
            lunes_apertura="08:00",
            lunes_cierre="18:00"
        )
        session.add(segment)
        session.commit()
        
        staffing_result = StaffingResult(
            result_date=datetime.date(2023, 1, 1),
            segment_id=segment.id,
            agents_online='{"interval1": 10}',
            agents_total='{"interval1": 15}'
        )
        session.add(staffing_result)
        session.commit()
        
        assert str(staffing_result) == f"<StaffingResult 2023-01-01 for Segment {segment.id}>"


class TestActualsData:
    """Pruebas para el modelo ActualsData."""
    
    def test_actuals_data_creation(self, session):
        """Prueba la creación de datos reales."""
        campaign = Campaign(
            code="TEST012",
            name="Campaña para Actuals",
            country="CO"
        )
        session.add(campaign)
        session.commit()
        
        segment = Segment(
            name="Segmento para Actuals",
            campaign_id=campaign.id,
            lunes_apertura="08:00",
            lunes_cierre="18:00"
        )
        session.add(segment)
        session.commit()
        
        actuals_data = ActualsData(
            result_date=datetime.date(2023, 1, 1),
            segment_id=segment.id,
            actuals_data='{"interval1": 8, "interval2": 14}'
        )
        session.add(actuals_data)
        session.commit()
        
        retrieved_data = ActualsData.query.filter_by(
            result_date=datetime.date(2023, 1, 1),
            segment_id=segment.id
        ).first()
        assert retrieved_data is not None
        assert retrieved_data.actuals_data == '{"interval1": 8, "interval2": 14}'
    
    def test_actuals_data_unique_date_segment(self, session):
        """Prueba que las combinaciones de fecha y segmento deben ser únicas."""
        campaign = Campaign(
            code="TEST013",
            name="Campaña para Actuals Único",
            country="CO"
        )
        session.add(campaign)
        session.commit()
        
        segment = Segment(
            name="Segmento para Actuals Único",
            campaign_id=campaign.id,
            lunes_apertura="08:00",
            lunes_cierre="18:00"
        )
        session.add(segment)
        session.commit()
        
        actuals_data1 = ActualsData(
            result_date=datetime.date(2023, 1, 1),
            segment_id=segment.id,
            actuals_data='{"interval1": 8}'
        )
        session.add(actuals_data1)
        session.commit()
        
        actuals_data2 = ActualsData(
            result_date=datetime.date(2023, 1, 1),
            segment_id=segment.id,
            actuals_data='{"interval2": 14}'
        )
        session.add(actuals_data2)
        
        with pytest.raises(Exception):  # SQLAlchemy lanzará una excepción por constraint
            session.commit()
    
    def test_actuals_data_repr(self, session):
        """Prueba la representación string de los datos reales."""
        campaign = Campaign(
            code="TEST014",
            name="Campaña para Repr Actuals",
            country="CO"
        )
        session.add(campaign)
        session.commit()
        
        segment = Segment(
            name="Segmento para Repr Actuals",
            campaign_id=campaign.id,
            lunes_apertura="08:00",
            lunes_cierre="18:00"
        )
        session.add(segment)
        session.commit()
        
        actuals_data = ActualsData(
            result_date=datetime.date(2023, 1, 1),
            segment_id=segment.id,
            actuals_data='{"interval1": 8}'
        )
        session.add(actuals_data)
        session.commit()
        
        assert str(actuals_data) == f"<ActualsData 2023-01-01 for Segment {segment.id}>"


class TestAgent:
    """Pruebas para el modelo Agent."""
    
    def test_agent_creation(self, session):
        """Prueba la creación de un agente."""
        campaign = Campaign(
            code="TEST015",
            name="Campaña para Agente",
            country="CO"
        )
        session.add(campaign)
        session.commit()
        
        segment = Segment(
            name="Segmento para Agente",
            campaign_id=campaign.id,
            lunes_apertura="08:00",
            lunes_cierre="18:00"
        )
        session.add(segment)
        session.commit()
        
        agent = Agent(
            identificacion="123456789",
            nombre_completo="Juan Pérez",
            segment_id=segment.id,
            centro="Centro de Llamada",
            contrato="Contrato123",
            turno_sugerido="Mañana",
            jornada="Completa",
            concrecion="2023-12-31",
            rotacion_finde="FINO",
            ventana_horaria="08:00-18:00",
            modalidad_finde="UNICO",
            rotacion_mensual_domingo="NORMAL",
            semanas_libres_finde="2",
            fecha_alta=datetime.date(2023, 1, 1)
        )
        session.add(agent)
        session.commit()
        
        retrieved_agent = Agent.query.filter_by(identificacion="123456789").first()
        assert retrieved_agent is not None
        assert retrieved_agent.nombre_completo == "Juan Pérez"
        assert retrieved_agent.centro == "Centro de Llamada"
        assert retrieved_agent.contrato == "Contrato123"
        assert retrieved_agent.turno_sugerido == "Mañana"
        assert retrieved_agent.jornada == "Completa"
        assert retrieved_agent.concrecion == "2023-12-31"
        assert retrieved_agent.rotacion_finde == "FINO"
        assert retrieved_agent.ventana_horaria == "08:00-18:00"
        assert retrieved_agent.modalidad_finde == "UNICO"
        assert retrieved_agent.rotacion_mensual_domingo == "NORMAL"
        assert retrieved_agent.semanas_libres_finde == "2"
        assert retrieved_agent.fecha_alta == datetime.date(2023, 1, 1)
        assert retrieved_agent.fecha_baja is None
    
    def test_agent_unique_identificacion(self, session):
        """Prueba que las identificaciones deben ser únicas."""
        agent1 = Agent(
            identificacion="DUPLICATE",
            nombre_completo="Agente 1",
            segment_id=1,
            fecha_alta=datetime.date(2023, 1, 1)
        )
        session.add(agent1)
        session.commit()
        
        agent2 = Agent(
            identificacion="DUPLICATE",
            nombre_completo="Agente 2",
            segment_id=2,
            fecha_alta=datetime.date(2023, 1, 1)
        )
        session.add(agent2)
        
        with pytest.raises(Exception):  # SQLAlchemy lanzará una excepción por constraint
            session.commit()
    
    def test_agent_repr(self, session):
        """Prueba la representación string del agente."""
        agent = Agent(
            identificacion="987654321",
            nombre_completo="María García",
            segment_id=1,
            fecha_alta=datetime.date(2023, 1, 1)
        )
        session.add(agent)
        session.commit()
        
        assert str(agent) == "<Agent María García (987654321)>"
    
    def test_agent_segment_relationship(self, session):
        """Prueba la relación con segmentos."""
        campaign = Campaign(
            code="TEST016",
            name="Campaña para Relación",
            country="CO"
        )
        session.add(campaign)
        session.commit()
        
        segment = Segment(
            name="Segmento para Relación",
            campaign_id=campaign.id,
            lunes_apertura="08:00",
            lunes_cierre="18:00"
        )
        session.add(segment)
        session.commit()
        
        agent = Agent(
            identificacion="55566777",
            nombre_completo="Carlos López",
            segment_id=segment.id,
            fecha_alta=datetime.date(2023, 1, 1)
        )
        session.add(agent)
        session.commit()
        
        retrieved_agent = Agent.query.filter_by(identificacion="55566777").first()
        assert retrieved_agent.segment.name == "Segmento para Relación"


class TestSchedulingRule:
    """Pruebas para el modelo SchedulingRule."""
    
    def test_scheduling_rule_creation(self, session):
        """Prueba la creación de una regla de scheduling."""
        rule = SchedulingRule(
            name="Regla de Prueba",
            country="CO"
        )
        session.add(rule)
        session.commit()
        
        retrieved_rule = SchedulingRule.query.filter_by(name="Regla de Prueba").first()
        assert retrieved_rule is not None
        assert retrieved_rule.name == "Regla de Prueba"
        assert retrieved_rule.country == "CO"
    
    def test_scheduling_rule_repr(self, session):
        """Prueba la representación string de la regla."""
        rule = SchedulingRule(
            name="Regla de Repr",
            country="MX"
        )
        session.add(rule)
        session.commit()
        
        assert str(rule) == "<SchedulingRule Regla de Repr>"
    
    def test_scheduling_rule_unique_name(self, session):
        """Prueba que los nombres de reglas deben ser únicos."""
        rule1 = SchedulingRule(
            name="Regla Duplicada",
            country="CO"
        )
        session.add(rule1)
        session.commit()
        
        rule2 = SchedulingRule(
            name="Regla Duplicada",
            country="MX"
        )
        session.add(rule2)
        
        with pytest.raises(Exception):  # SQLAlchemy lanzará una excepción por constraint
            session.commit()
    
    def test_scheduling_rule_workday_rules_relationship(self, session):
        """Prueba la relación con reglas de jornada."""
        rule = SchedulingRule(
            name="Regla con Workday",
            country="CO"
        )
        session.add(rule)
        session.commit()
        
        workday_rule = WorkdayRule(
            weekly_hours=40.0,
            max_daily_hours=8.0,
            min_daily_hours=4.0,
            days_per_week=5,
            max_consecutive_work_days=6,
            min_hours_between_shifts=12,
            allow_irregular_shifts=True,
            rule_id=rule.id
        )
        session.add(workday_rule)
        session.commit()
        
        retrieved_rule = SchedulingRule.query.filter_by(name="Regla con Workday").first()
        assert retrieved_rule.workday_rule is not None
        assert retrieved_rule.workday_rule.weekly_hours == 40.0


class TestWorkdayRule:
    """Pruebas para el modelo WorkdayRule."""
    
    def test_workday_rule_creation(self, session):
        """Prueba la creación de una regla de jornada."""
        rule = SchedulingRule(
            name="Regla para Workday",
            country="CO"
        )
        session.add(rule)
        session.commit()
        
        workday_rule = WorkdayRule(
            weekly_hours=40.0,
            max_daily_hours=8.0,
            min_daily_hours=4.0,
            days_per_week=5,
            max_consecutive_work_days=6,
            min_hours_between_shifts=12,
            allow_irregular_shifts=True,
            rule_id=rule.id
        )
        session.add(workday_rule)
        session.commit()
        
        retrieved_rule = WorkdayRule.query.filter_by(rule_id=rule.id).first()
        assert retrieved_rule is not None
        assert retrieved_rule.weekly_hours == 40.0
        assert retrieved_rule.max_daily_hours == 8.0
        assert retrieved_rule.min_daily_hours == 4.0
        assert retrieved_rule.days_per_week == 5
        assert retrieved_rule.max_consecutive_work_days == 6
        assert retrieved_rule.min_hours_between_shifts == 12
        assert retrieved_rule.allow_irregular_shifts is True
    
    def test_workday_rule_defaults(self, session):
        """Prueba los valores por defecto de la regla de jornada."""
        rule = SchedulingRule(
            name="Regla con Defaults",
            country="CO"
        )
        session.add(rule)
        session.commit()
        
        workday_rule = WorkdayRule(
            weekly_hours=40.0,
            max_daily_hours=8.0,
            min_daily_hours=4.0,
            rule_id=rule.id
        )
        session.add(workday_rule)
        session.commit()
        
        retrieved_rule = WorkdayRule.query.filter_by(rule_id=rule.id).first()
        assert retrieved_rule.days_per_week == 5  # Valor por defecto
        assert retrieved_rule.max_consecutive_work_days == 7  # Valor por defecto
        assert retrieved_rule.min_hours_between_shifts == 12  # Valor por defecto
        assert retrieved_rule.allow_irregular_shifts is False  # Valor por defecto
    
    def test_workday_rule_repr(self, session):
        """Prueba la representación string de la regla de jornada."""
        rule = SchedulingRule(
            name="Regla para Repr Workday",
            country="CO"
        )
        session.add(rule)
        session.commit()
        
        workday_rule = WorkdayRule(
            weekly_hours=40.0,
            max_daily_hours=8.0,
            min_daily_hours=4.0,
            rule_id=rule.id
        )
        session.add(workday_rule)
        session.commit()
        
        assert str(workday_rule) == f"<WorkdayRule for Rule {rule.id}>"


class TestSchedule:
    """Pruebas para el modelo Schedule."""
    
    def test_schedule_creation(self, session):
        """Prueba la creación de un horario."""
        campaign = Campaign(
            code="TEST017",
            name="Campaña para Horario",
            country="CO"
        )
        session.add(campaign)
        session.commit()
        
        segment = Segment(
            name="Segmento para Horario",
            campaign_id=campaign.id,
            lunes_apertura="08:00",
            lunes_cierre="18:00"
        )
        session.add(segment)
        session.commit()
        
        agent = Agent(
            identificacion="111222333",
            nombre_completo="Ana Martínez",
            segment_id=segment.id,
            fecha_alta=datetime.date(2023, 1, 1)
        )
        session.add(agent)
        session.commit()
        
        schedule = Schedule(
            agent_id=agent.id,
            schedule_date=datetime.date(2023, 1, 1),
            shift="MAÑANA",
            hours=8.0,
            descanso1_he="12:00",
            descanso1_hs="01:00",
            descanso2_he="14:00",
            descanso2_hs="01:00",
            pvd1="08:00",
            pvd2="12:00",
            pvd3="14:00",
            pvd4="16:00",
            pvd5="18:00"
        )
        session.add(schedule)
        session.commit()
        
        retrieved_schedule = Schedule.query.filter_by(
            agent_id=agent.id,
            schedule_date=datetime.date(2023, 1, 1)
        ).first()
        assert retrieved_schedule is not None
        assert retrieved_schedule.shift == "MAÑANA"
        assert retrieved_schedule.hours == 8.0
        assert retrieved_schedule.descanso1_he == "12:00"
        assert retrieved_schedule.descanso1_hs == "01:00"
        assert retrieved_schedule.pvd1 == "08:00"
    
    def test_schedule_unique_agent_date(self, session):
        """Prueba que las combinaciones de agente y fecha deben ser únicas."""
        campaign = Campaign(
            code="TEST018",
            name="Campaña para Horario Único",
            country="CO"
        )
        session.add(campaign)
        session.commit()
        
        segment = Segment(
            name="Segmento para Horario Único",
            campaign_id=campaign.id,
            lunes_apertura="08:00",
            lunes_cierre="18:00"
        )
        session.add(segment)
        session.commit()
        
        agent = Agent(
            identificacion="999888777",
            nombre_completo="Roberto Díaz",
            segment_id=segment.id,
            fecha_alta=datetime.date(2023, 1, 1)
        )
        session.add(agent)
        session.commit()
        
        schedule1 = Schedule(
            agent_id=agent.id,
            schedule_date=datetime.date(2023, 1, 1),
            shift="MAÑANA",
            hours=8.0
        )
        session.add(schedule1)
        session.commit()
        
        schedule2 = Schedule(
            agent_id=agent.id,
            schedule_date=datetime.date(2023, 1, 1),
            shift="TARDE",
            hours=8.0
        )
        session.add(schedule2)
        
        with pytest.raises(Exception):  # SQLAlchemy lanzará una excepción por constraint
            session.commit()
    
    def test_schedule_defaults(self, session):
        """Prueba los valores por defecto del horario."""
        campaign = Campaign(
            code="TEST019",
            name="Campaña para Horario con Defaults",
            country="CO"
        )
        session.add(campaign)
        session.commit()
        
        segment = Segment(
            name="Segmento para Horario con Defaults",
            campaign_id=campaign.id,
            lunes_apertura="08:00",
            lunes_cierre="18:00"
        )
        session.add(segment)
        session.commit()
        
        agent = Agent(
            identificacion="66655443",
            nombre_completo="Laura Sánchez",
            segment_id=segment.id,
            fecha_alta=datetime.date(2023, 1, 1)
        )
        session.add(agent)
        session.commit()
        
        schedule = Schedule(
            agent_id=agent.id,
            schedule_date=datetime.date(2023, 1, 1)
        )
        session.add(schedule)
        session.commit()
        
        retrieved_schedule = Schedule.query.filter_by(
            agent_id=agent.id,
            schedule_date=datetime.date(2023, 1, 1)
        ).first()
        assert retrieved_schedule.shift == "LIBRE"  # Valor por defecto
        assert retrieved_schedule.hours == 0.0  # Valor por defecto
        assert retrieved_schedule.is_manual_edit is False  # Valor por defecto
    
    def test_schedule_repr(self, session):
        """Prueba la representación string del horario."""
        campaign = Campaign(
            code="TEST020",
            name="Campaña para Repr Horario",
            country="CO"
        )
        session.add(campaign)
        session.commit()
        
        segment = Segment(
            name="Segmento para Repr Horario",
            campaign_id=campaign.id,
            lunes_apertura="08:00",
            lunes_cierre="18:00"
        )
        session.add(segment)
        session.commit()
        
        agent = Agent(
            identificacion="55544433",
            nombre_completo="Pedro Ramírez",
            segment_id=segment.id,
            fecha_alta=datetime.date(2023, 1, 1)
        )
        session.add(agent)
        session.commit()
        
        schedule = Schedule(
            agent_id=agent.id,
            schedule_date=datetime.date(2023, 1, 1),
            shift="MAÑANA",
            hours=8.0
        )
        session.add(schedule)
        session.commit()
        
        assert str(schedule) == f"<Schedule 2023-01-01 for Agent {agent.id}: MAÑANA>"
    
    def test_schedule_agent_relationship(self, session):
        """Prueba la relación con agentes."""
        campaign = Campaign(
            code="TEST021",
            name="Campaña para Relación Horario",
            country="CO"
        )
        session.add(campaign)
        session.commit()
        
        segment = Segment(
            name="Segmento para Relación Horario",
            campaign_id=campaign.id,
            lunes_apertura="08:00",
            lunes_cierre="18:00"
        )
        session.add(segment)
        session.commit()
        
        agent = Agent(
            identificacion="332211445",
            nombre_completo="Sofía Castro",
            segment_id=segment.id,
            fecha_alta=datetime.date(2023, 1, 1)
        )
        session.add(agent)
        session.commit()
        
        schedule = Schedule(
            agent_id=agent.id,
            schedule_date=datetime.date(2023, 1, 1),
            shift="MAÑANA",
            hours=8.0
        )
        session.add(schedule)
        session.commit()
        
        retrieved_schedule = Schedule.query.filter_by(
            agent_id=agent.id,
            schedule_date=datetime.date(2023, 1, 1)
        ).first()
        assert retrieved_schedule.agent.nombre_completo == "Sofía Castro"


class TestBreakRule:
    """Pruebas para el modelo BreakRule."""
    
    def test_break_rule_creation(self, session):
        """Prueba la creación de una regla de descanso."""
        rule = BreakRule(
            name="Regla de Descanso",
            country="CO",
            min_shift_hours=4.0,
            max_shift_hours=8.0
        )
        session.add(rule)
        session.commit()
        
        retrieved_rule = BreakRule.query.filter_by(name="Regla de Descanso").first()
        assert retrieved_rule is not None
        assert retrieved_rule.name == "Regla de Descanso"
        assert retrieved_rule.country == "CO"
        assert retrieved_rule.min_shift_hours == 4.0
        assert retrieved_rule.max_shift_hours == 8.0
    
    def test_break_rule_repr(self, session):
        """Prueba la representación string de la regla de descanso."""
        rule = BreakRule(
            name="Regla de Repr Descanso",
            country="MX",
            min_shift_hours=4.0,
            max_shift_hours=8.0
        )
        session.add(rule)
        session.commit()
        
        assert str(rule) == "<BreakRule Regla de Repr Descanso (MX)>"
    
    def test_break_rule_defaults(self, session):
        """Prueba los valores por defecto de la regla de descanso."""
        rule = BreakRule(
            name="Regla con Defaults",
            country="CO",
            min_shift_hours=4.0,
            max_shift_hours=8.0
        )
        session.add(rule)
        session.commit()
        
        retrieved_rule = BreakRule.query.filter_by(name="Regla con Defaults").first()
        assert retrieved_rule.min_shift_hours == 4.0
        assert retrieved_rule.max_shift_hours == 8.0
        assert retrieved_rule.break_duration_minutes == 0  # Valor por defecto
        assert retrieved_rule.pvd_minutes_per_hour == 0  # Valor por defecto
        assert retrieved_rule.number_of_pvds == 0  # Valor por defecto
    
    def test_break_rule_unique_name_country(self, session):
        """Prueba que los nombres de reglas deben ser únicos por país."""
        rule1 = BreakRule(
            name="Regla Duplicada",
            country="CO",
            min_shift_hours=4.0,
            max_shift_hours=8.0
        )
        session.add(rule1)
        session.commit()
        
        rule2 = BreakRule(
            name="Regla Duplicada",
            country="CO",
            min_shift_hours=4.0,
            max_shift_hours=8.0
        )
        session.add(rule2)
        
        with pytest.raises(Exception):  # SQLAlchemy lanzará una excepción por constraint
            session.commit()