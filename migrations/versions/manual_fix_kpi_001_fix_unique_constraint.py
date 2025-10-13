"""Manually fix KPI table to remove old unique constraint

Revision ID: manual_fix_kpi_001
Revises: 606408eb352b
Create Date: 2025-10-12 20:27:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'manual_fix_kpi_001'
down_revision = '606408eb352b'
branch_labels = None
depends_on = None


def upgrade():
    # Create new table without the old unique constraint
    op.create_table('kpi_strategic_new',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date_creation', sa.DateTime(), nullable=False),
        sa.Column('date_modification', sa.DateTime(), nullable=False),
        sa.Column('actif', sa.Boolean(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('nom', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('valeur', sa.Float(), nullable=False),
        sa.Column('unite', sa.String(length=50), nullable=False),
        sa.Column('periode', sa.String(length=20), nullable=False),
        sa.Column('annee', sa.Integer(), nullable=False),
        sa.Column('tendance', sa.Enum('HAUSSE', 'BAISSE', 'STABLE', name='tendancekpi'), nullable=False),
        sa.Column('evolution_pourcentage', sa.Float(), nullable=True),
        sa.Column('objectif', sa.Float(), nullable=True),
        sa.Column('seuil_alerte', sa.Float(), nullable=True),
        sa.Column('source_donnees', sa.String(length=200), nullable=True),
        sa.Column('operateur_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['operateur_id'], ['operateurs.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', 'annee', 'operateur_id', name='uq_kpi_code_annee_operateur')
    )
    
    # Copy data from old table to new table
    op.execute("""
        INSERT INTO kpi_strategic_new 
        (id, date_creation, date_modification, actif, code, nom, description, valeur, 
         unite, periode, annee, tendance, evolution_pourcentage, objectif, seuil_alerte, 
         source_donnees, operateur_id)
        SELECT id, date_creation, date_modification, actif, code, nom, description, valeur, 
               unite, periode, annee, tendance, evolution_pourcentage, objectif, seuil_alerte, 
               source_donnees, operateur_id
        FROM kpi_strategic
    """)
    
    # Drop old table and rename new table
    op.drop_table('kpi_strategic')
    op.rename_table('kpi_strategic_new', 'kpi_strategic')


def downgrade():
    # Revert back to old structure
    op.create_table('kpi_strategic_old',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date_creation', sa.DateTime(), nullable=False),
        sa.Column('date_modification', sa.DateTime(), nullable=False),
        sa.Column('actif', sa.Boolean(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('nom', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('valeur', sa.Float(), nullable=False),
        sa.Column('unite', sa.String(length=50), nullable=False),
        sa.Column('periode', sa.String(length=20), nullable=False),
        sa.Column('annee', sa.Integer(), nullable=False),
        sa.Column('tendance', sa.Enum('HAUSSE', 'BAISSE', 'STABLE', name='tendancekpi'), nullable=False),
        sa.Column('evolution_pourcentage', sa.Float(), nullable=True),
        sa.Column('objectif', sa.Float(), nullable=True),
        sa.Column('seuil_alerte', sa.Float(), nullable=True),
        sa.Column('source_donnees', sa.String(length=200), nullable=True),
        sa.Column('operateur_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['operateur_id'], ['operateurs.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    
    op.execute("""
        INSERT INTO kpi_strategic_old 
        (id, date_creation, date_modification, actif, code, nom, description, valeur, 
         unite, periode, annee, tendance, evolution_pourcentage, objectif, seuil_alerte, 
         source_donnees, operateur_id)
        SELECT id, date_creation, date_modification, actif, code, nom, description, valeur, 
               unite, periode, annee, tendance, evolution_pourcentage, objectif, seuil_alerte, 
               source_donnees, operateur_id
        FROM kpi_strategic
    """)
    
    op.drop_table('kpi_strategic')
    op.rename_table('kpi_strategic_old', 'kpi_strategic')