"""
Modèles pour le dashboard stratégique de l'ARE
"""
from datetime import datetime
from enum import Enum
from app.extensions import db
from app.models.base import BaseModel


class TypeAlerte(Enum):
    """Types d'alertes réglementaires"""
    CONFORMITE = "conformite"
    FINANCIER = "financier"
    TECHNIQUE = "technique"
    ADMINISTRATIF = "administratif"
    SECURITE = "securite"


class SeveriteAlerte(Enum):
    """Niveaux de sévérité des alertes"""
    FAIBLE = "faible"
    MOYENNE = "moyenne"
    ELEVEE = "elevee"
    CRITIQUE = "critique"


class TendanceKPI(Enum):
    """Tendances des KPIs"""
    HAUSSE = "hausse"
    BAISSE = "baisse"
    STABLE = "stable"


class CategorieIndicateur(Enum):
    """Catégories d'indicateurs sectoriels"""
    PRODUCTION = "production"
    TRANSPORT = "transport"
    DISTRIBUTION = "distribution"
    ACCES = "acces"
    QUALITE = "qualite"
    FINANCIER = "financier"
    ENVIRONNEMENTAL = "environnemental"


class KPIStrategic(BaseModel):
    """Indicateurs clés de performance stratégiques"""
    __tablename__ = 'kpi_strategic'
    
    code = db.Column(db.String(50), nullable=False)
    nom = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    valeur = db.Column(db.Float, nullable=False)
    unite = db.Column(db.String(50), nullable=False)
    periode = db.Column(db.String(20), nullable=False)  # 2024-Q1, 2024-01, 2024
    annee = db.Column(db.Integer, nullable=False)
    tendance = db.Column(db.Enum(TendanceKPI), nullable=False, default=TendanceKPI.STABLE)
    evolution_pourcentage = db.Column(db.Float)  # % d'évolution par rapport à la période précédente
    objectif = db.Column(db.Float)  # Valeur objectif
    atteint = db.Column(db.Boolean, default=False)  # Indicateur si l'objectif est atteint
    seuil_alerte = db.Column(db.Float)  # Seuil déclenchant une alerte
    source_donnees = db.Column(db.String(200))
    
    # Relations
    operateur_id = db.Column(db.Integer, db.ForeignKey('operateurs.id'), nullable=True)
    operateur = db.relationship('Operateur', backref='kpis_strategiques', lazy=True)
    
    # Contrainte unique sur la combinaison code + annee + operateur_id
    __table_args__ = (
        db.UniqueConstraint('code', 'annee', 'operateur_id', name='uq_kpi_code_annee_operateur'),
    )
    
    def __repr__(self):
        return f'<KPIStrategic {self.code}: {self.valeur} {self.unite}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'nom': self.nom,
            'description': self.description,
            'valeur': self.valeur,
            'unite': self.unite,
            'periode': self.periode,
            'annee': self.annee,
            'tendance': self.tendance.value if self.tendance else None,
            'evolution_pourcentage': self.evolution_pourcentage,
            'objectif': self.objectif,
            'atteint': self.atteint,
            'seuil_alerte': self.seuil_alerte,
            'operateur': self.operateur.nom if self.operateur else 'National',
            'date_modification': self.date_modification.isoformat() if self.date_modification else None
        }


class IndicateurSectoriel(BaseModel):
    """Indicateurs sectoriels détaillés"""
    __tablename__ = 'indicateur_sectoriel'
    
    categorie = db.Column(db.Enum(CategorieIndicateur), nullable=False)
    sous_categorie = db.Column(db.String(100), nullable=False)
    nom = db.Column(db.String(200), nullable=False)
    valeur = db.Column(db.Float, nullable=False)
    unite = db.Column(db.String(50), nullable=False)
    periode = db.Column(db.String(20), nullable=False)
    annee = db.Column(db.Integer, nullable=False)
    evolution = db.Column(db.Float)  # Évolution par rapport à la période précédente
    province = db.Column(db.String(50))  # Province concernée si applicable
    
    # Relations
    operateur_id = db.Column(db.Integer, db.ForeignKey('operateurs.id'), nullable=True)
    operateur = db.relationship('Operateur', backref='indicateurs_sectoriels', lazy=True)
    
    def __repr__(self):
        return f'<IndicateurSectoriel {self.categorie.value}: {self.nom}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'categorie': self.categorie.value,
            'sous_categorie': self.sous_categorie,
            'nom': self.nom,
            'valeur': self.valeur,
            'unite': self.unite,
            'periode': self.periode,
            'annee': self.annee,
            'evolution': self.evolution,
            'province': self.province,
            'operateur': self.operateur.nom if self.operateur else 'National'
        }


class AlerteRegulateur(BaseModel):
    """Alertes pour le régulateur"""
    __tablename__ = 'alerte_regulateur'
    
    type = db.Column(db.Enum(TypeAlerte), nullable=False)
    severite = db.Column(db.Enum(SeveriteAlerte), nullable=False)
    entite_concernee = db.Column(db.String(200), nullable=False)
    titre = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date_echeance = db.Column(db.Date)
    date_resolution = db.Column(db.Date)
    statut = db.Column(db.String(50), default='active')  # active, en_cours, resolue
    actions_recommandees = db.Column(db.Text)
    priorite = db.Column(db.Integer, default=3)  # 1=haute, 2=moyenne, 3=basse
    
    # Relations
    operateur_id = db.Column(db.Integer, db.ForeignKey('operateurs.id'), nullable=True)
    operateur = db.relationship('Operateur', backref='alertes_regulateur', lazy=True)
    
    # Utilisateur qui a créé l'alerte
    createur_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    createur = db.relationship('User', backref='alertes_creees', lazy=True)
    
    def __repr__(self):
        return f'<AlerteRegulateur {self.type.value}: {self.titre}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type.value,
            'severite': self.severite.value,
            'entite_concernee': self.entite_concernee,
            'titre': self.titre,
            'description': self.description,
            'date_echeance': self.date_echeance.isoformat() if self.date_echeance else None,
            'date_resolution': self.date_resolution.isoformat() if self.date_resolution else None,
            'statut': self.statut,
            'priorite': self.priorite,
            'operateur': self.operateur.nom if self.operateur else None,
            'createur': self.createur.username if self.createur else None,
            'date_creation': self.date_creation.isoformat() if self.date_creation else None
        }
    
    @property
    def is_expired(self):
        """Vérifie si l'alerte a dépassé sa date d'échéance"""
        if self.date_echeance and self.statut == 'active':
            return datetime.now().date() > self.date_echeance
        return False
    
    @property
    def jours_restants(self):
        """Calcule le nombre de jours restants avant l'échéance"""
        if self.date_echeance and self.statut == 'active':
            delta = self.date_echeance - datetime.now().date()
            return delta.days
        return None


class DonneesProvince(BaseModel):
    """Données par province pour la carte interactive"""
    __tablename__ = 'donnees_province'
    
    province = db.Column(db.String(50), nullable=False)
    population = db.Column(db.Integer)
    taux_acces_electricite = db.Column(db.Float)  # Pourcentage
    puissance_installee = db.Column(db.Float)  # MW
    production_annuelle = db.Column(db.Float)  # GWh
    nombre_operateurs = db.Column(db.Integer, default=0)
    investissements = db.Column(db.Float)  # Millions USD
    annee = db.Column(db.Integer, nullable=False)
    
    def __repr__(self):
        return f'<DonneesProvince {self.province} - {self.annee}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'province': self.province,
            'population': self.population,
            'taux_acces_electricite': self.taux_acces_electricite,
            'puissance_installee': self.puissance_installee,
            'production_annuelle': self.production_annuelle,
            'nombre_operateurs': self.nombre_operateurs,
            'investissements': self.investissements,
            'annee': self.annee
        }


class RapportAnnuel(BaseModel):
    """Rapports annuels générés automatiquement"""
    __tablename__ = 'rapport_annuel'
    
    annee = db.Column(db.Integer, nullable=False)
    titre = db.Column(db.String(200), nullable=False)
    statut = db.Column(db.String(50), default='brouillon')  # brouillon, en_cours, finalise
    contenu_json = db.Column(db.JSON)  # Structure du rapport
    date_generation = db.Column(db.DateTime, default=datetime.utcnow)
    date_finalisation = db.Column(db.DateTime)
    
    # Métadonnées
    nombre_operateurs = db.Column(db.Integer)
    periode_debut = db.Column(db.Date)
    periode_fin = db.Column(db.Date)
    
    # Relations
    auteur_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    auteur = db.relationship('User', backref='rapports_annuels', lazy=True)
    
    def __repr__(self):
        return f'<RapportAnnuel {self.annee}: {self.titre}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'annee': self.annee,
            'titre': self.titre,
            'statut': self.statut,
            'date_generation': self.date_generation.isoformat() if self.date_generation else None,
            'date_finalisation': self.date_finalisation.isoformat() if self.date_finalisation else None,
            'nombre_operateurs': self.nombre_operateurs,
            'auteur': self.auteur.username if self.auteur else None
        }