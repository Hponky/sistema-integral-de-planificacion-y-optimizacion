"""Agregar escenarios

Revision ID: 509621d2b6df
Revises: e8f336afada9
Create Date: 2025-11-27 16:33:23.708017

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '509621d2b6df'
down_revision = 'e8f336afada9'
branch_labels = None
depends_on = None


def upgrade():
    # --- TABLA SCENARIOS (COMENTADA PORQUE YA EXISTE) ---
    # op.create_table('scenarios',
    #     sa.Column('id', sa.Integer(), nullable=False),
    #     sa.Column('name', sa.String(length=100), nullable=False),
    #     sa.Column('segment_id', sa.Integer(), nullable=False),
    #     sa.Column('description', sa.String(length=255), nullable=True),
    #     sa.Column('is_official', sa.Boolean(), nullable=True),
    #     sa.Column('created_at', sa.DateTime(), nullable=True),
    #     sa.ForeignKeyConstraint(['segment_id'], ['segments.id'], name='fk_scenarios_segment_id'),
    #     sa.PrimaryKeyConstraint('id')
    # )
    # ----------------------------------------------------

    # 1. AGENTS: Clave foránea única
    with op.batch_alter_table('agents', schema=None) as batch_op:
        batch_op.add_column(sa.Column('scenario_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('is_simulated', sa.Boolean(), nullable=True))
        # Nombre único: fk_agents_scenario_id
        batch_op.create_foreign_key('fk_agents_scenario_id', 'scenarios', ['scenario_id'], ['id'])

    # 2. SCHEDULES: Clave foránea única
    with op.batch_alter_table('schedules', schema=None) as batch_op:
        batch_op.add_column(sa.Column('scenario_id', sa.Integer(), nullable=True))
        # Nombre único: fk_schedules_scenario_id
        batch_op.create_foreign_key('fk_schedules_scenario_id', 'scenarios', ['scenario_id'], ['id'])

    # 3. STAFFING_RESULTS: Clave foránea única y Unique Constraint
    with op.batch_alter_table('staffing_results', schema=None) as batch_op:
        batch_op.add_column(sa.Column('scenario_id', sa.Integer(), nullable=True))
        
        # Intentamos borrar la restricción vieja por nombre. 
        # Nota: En SQLite a veces los nombres se pierden. Si esto falla, comenta la línea 'drop_constraint'.
        try:
            batch_op.drop_constraint('_date_segment_uc', type_='unique')
        except ValueError:
            pass # Si no la encuentra por nombre, continuamos
            
        # Crear nueva restricción única que incluye el escenario
        batch_op.create_unique_constraint('_date_seg_scen_uc', ['result_date', 'segment_id', 'scenario_id'])
        
        # Nombre único: fk_staffing_results_scenario_id
        batch_op.create_foreign_key('fk_staffing_results_scenario_id', 'scenarios', ['scenario_id'], ['id'])


def downgrade():
    # Revertir cambios con nombres explícitos
    with op.batch_alter_table('staffing_results', schema=None) as batch_op:
        batch_op.drop_constraint('fk_staffing_results_scenario_id', type_='foreignkey')
        batch_op.drop_constraint('_date_seg_scen_uc', type_='unique')
        batch_op.create_unique_constraint('_date_segment_uc', ['result_date', 'segment_id'])
        batch_op.drop_column('scenario_id')

    with op.batch_alter_table('schedules', schema=None) as batch_op:
        batch_op.drop_constraint('fk_schedules_scenario_id', type_='foreignkey')
        batch_op.drop_column('scenario_id')

    with op.batch_alter_table('agents', schema=None) as batch_op:
        batch_op.drop_constraint('fk_agents_scenario_id', type_='foreignkey')
        batch_op.drop_column('is_simulated')
        batch_op.drop_column('scenario_id')

    # op.drop_table('scenarios') # Comentado porque arriba no la creamos