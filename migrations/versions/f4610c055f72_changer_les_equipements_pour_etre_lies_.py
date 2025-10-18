"""Changer les equipements pour etre lies aux centrales au lieu des rapports

Revision ID: f4610c055f72
Revises: 4aa9995541d7
Create Date: 2025-10-18 14:05:25.940475

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f4610c055f72'
down_revision = '4aa9995541d7'
branch_labels = None
depends_on = None


def upgrade():
    # Migration pour changer les équipements pour être liés aux centrales au lieu des rapports
    # La colonne centrale_id existe déjà, il faut juste mettre à jour les données et supprimer rapport_id

    # Étape 1: Peupler centrale_id depuis rapport_id via rapports_hydro.centrale_id
    op.execute('''
        UPDATE groupes_production
        SET centrale_id = (
            SELECT rapports_hydro.centrale_id
            FROM rapports_hydro
            WHERE rapports_hydro.id = groupes_production.rapport_id
        )
        WHERE centrale_id IS NULL
    ''')

    op.execute('''
        UPDATE transformateurs_rapport
        SET centrale_id = (
            SELECT rapports_hydro.centrale_id
            FROM rapports_hydro
            WHERE rapports_hydro.id = transformateurs_rapport.rapport_id
        )
        WHERE centrale_id IS NULL
    ''')

    # Étape 2: Recréer les tables sans rapport_id pour supprimer la contrainte FK
    # Groupes production
    op.execute('''
        CREATE TABLE groupes_production_new (
            id INTEGER NOT NULL,
            date_creation DATETIME,
            date_modification DATETIME,
            actif BOOLEAN,
            centrale_id INTEGER NOT NULL,
            numero_groupe VARCHAR(10) NOT NULL,
            nom_groupe VARCHAR(100),
            puissance_nominale FLOAT,
            tension_nominale FLOAT,
            vitesse_rotation FLOAT,
            type_turbine VARCHAR(50),
            heures_fonctionnement FLOAT,
            energie_produite FLOAT,
            puissance_moyenne FLOAT,
            puissance_max FLOAT,
            nombre_arrets_programme INTEGER,
            nombre_arrets_force INTEGER,
            duree_arrets_programme FLOAT,
            duree_arrets_force FLOAT,
            rendement_moyen FLOAT,
            facteur_charge FLOAT,
            disponibilite FLOAT,
            date_derniere_revision DATETIME,
            type_derniere_revision VARCHAR(100),
            prochaine_revision DATETIME,
            incidents TEXT,
            travaux_realises TEXT,
            observations TEXT,
            PRIMARY KEY (id),
            FOREIGN KEY(centrale_id) REFERENCES centrales_hydro (id)
        )
    ''')

    # Copier toutes les données
    op.execute('''
        INSERT INTO groupes_production_new
        SELECT id, date_creation, date_modification, actif, centrale_id, numero_groupe, nom_groupe,
               puissance_nominale, tension_nominale, vitesse_rotation, type_turbine, heures_fonctionnement,
               energie_produite, puissance_moyenne, puissance_max, nombre_arrets_programme, nombre_arrets_force,
               duree_arrets_programme, duree_arrets_force, rendement_moyen, facteur_charge, disponibilite,
               date_derniere_revision, type_derniere_revision, prochaine_revision, incidents,
               travaux_realises, observations
        FROM groupes_production
    ''')

    # Remplacer la table
    op.execute('DROP TABLE groupes_production')
    op.execute('ALTER TABLE groupes_production_new RENAME TO groupes_production')

    # Transformateurs
    op.execute('''
        CREATE TABLE transformateurs_rapport_new (
            id INTEGER NOT NULL,
            date_creation DATETIME,
            date_modification DATETIME,
            actif BOOLEAN,
            centrale_id INTEGER NOT NULL,
            numero_transformateur VARCHAR(10) NOT NULL,
            nom_transformateur VARCHAR(100),
            puissance_nominale FLOAT,
            tension_primaire FLOAT,
            tension_secondaire FLOAT,
            type_refroidissement VARCHAR(50),
            energie_transferee FLOAT,
            heures_service FLOAT,
            charge_moyenne FLOAT,
            charge_max FLOAT,
            temperature_huile_moyenne FLOAT,
            temperature_huile_max FLOAT,
            temperature_enroulements_max FLOAT,
            etat_general VARCHAR(50),
            date_derniere_maintenance DATETIME,
            type_maintenance VARCHAR(100),
            prochaine_maintenance DATETIME,
            incidents TEXT,
            travaux_realises TEXT,
            observations TEXT,
            PRIMARY KEY (id),
            FOREIGN KEY(centrale_id) REFERENCES centrales_hydro (id)
        )
    ''')

    # Copier toutes les données
    op.execute('''
        INSERT INTO transformateurs_rapport_new
        SELECT id, date_creation, date_modification, actif, centrale_id, numero_transformateur, nom_transformateur,
               puissance_nominale, tension_primaire, tension_secondaire, type_refroidissement, energie_transferee,
               heures_service, charge_moyenne, charge_max, temperature_huile_moyenne, temperature_huile_max,
               temperature_enroulements_max, etat_general, date_derniere_maintenance, type_maintenance,
               prochaine_maintenance, incidents, travaux_realises, observations
        FROM transformateurs_rapport
    ''')

    # Remplacer la table
    op.execute('DROP TABLE transformateurs_rapport')
    op.execute('ALTER TABLE transformateurs_rapport_new RENAME TO transformateurs_rapport')

    # Créer les index
    op.execute('CREATE INDEX ix_groupes_production_centrale_id ON groupes_production(centrale_id)')
    op.execute('CREATE INDEX ix_transformateurs_rapport_centrale_id ON transformateurs_rapport(centrale_id)')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('transformateurs_rapport', schema=None) as batch_op:
        batch_op.add_column(sa.Column('rapport_id', sa.INTEGER(), nullable=False))
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key(None, 'rapports_hydro', ['rapport_id'], ['id'])
        batch_op.drop_column('centrale_id')

    with op.batch_alter_table('groupes_production', schema=None) as batch_op:
        batch_op.add_column(sa.Column('rapport_id', sa.INTEGER(), nullable=False))
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key(None, 'rapports_hydro', ['rapport_id'], ['id'])
        batch_op.drop_column('centrale_id')

    op.create_table('sqlite_sequence',
    sa.Column('name', sa.NullType(), nullable=True),
    sa.Column('seq', sa.NullType(), nullable=True)
    )
    # ### end Alembic commands ###
