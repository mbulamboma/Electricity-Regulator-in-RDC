"""Correction transformateurs distribution poste_id vers poste_distribution_id

Revision ID: fix_transformateurs_001
Revises: fad89811421e
Create Date: 2025-10-13 19:20:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'fix_transformateurs_001'
down_revision = 'fad89811421e'
branch_labels = None
depends_on = None

def upgrade():
    # Ajouter les nouveaux champs au modèle TransformateurDistribution
    with op.batch_alter_table('transformateurs_distribution') as batch_op:
        # Renommer poste_id vers poste_distribution_id s'il existe
        try:
            batch_op.alter_column('poste_id', new_column_name='poste_distribution_id')
        except:
            # Si la colonne n'existe pas ou renommage échoue, créer la nouvelle colonne
            batch_op.add_column(sa.Column('poste_distribution_id', sa.Integer(), nullable=True))
        
        # Ajouter les nouveaux champs manquants s'ils n'existent pas
        try:
            batch_op.add_column(sa.Column('type_transformateur', sa.String(50), nullable=True))
        except:
            pass
        
        try:
            batch_op.add_column(sa.Column('modele', sa.String(100), nullable=True))
        except:
            pass
        
        try:
            batch_op.add_column(sa.Column('date_installation', sa.DateTime(), nullable=True))
        except:
            pass
        
        try:
            batch_op.add_column(sa.Column('latitude', sa.Float(), nullable=True))
        except:
            pass
        
        try:
            batch_op.add_column(sa.Column('longitude', sa.Float(), nullable=True))
        except:
            pass

    # Mettre à jour les données si nécessaire
    connection = op.get_bind()
    
    # Si poste_distribution_id est NULL mais poste_id existe, copier les valeurs
    try:
        connection.execute("""
            UPDATE transformateurs_distribution 
            SET poste_distribution_id = poste_id 
            WHERE poste_distribution_id IS NULL AND poste_id IS NOT NULL
        """)
    except:
        pass

def downgrade():
    with op.batch_alter_table('transformateurs_distribution') as batch_op:
        # Renommer back
        try:
            batch_op.alter_column('poste_distribution_id', new_column_name='poste_id')
        except:
            pass
        
        # Supprimer les nouveaux champs
        try:
            batch_op.drop_column('type_transformateur')
        except:
            pass
        try:
            batch_op.drop_column('modele')
        except:
            pass
        try:
            batch_op.drop_column('date_installation')
        except:
            pass
        try:
            batch_op.drop_column('latitude')
        except:
            pass
        try:
            batch_op.drop_column('longitude')
        except:
            pass