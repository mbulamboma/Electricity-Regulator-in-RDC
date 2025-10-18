"""
Modèles pour les KPIs réglementaires basés sur la réglementation RDC
Ces KPIs représentent les seuils que les opérateurs ne doivent pas dépasser
selon les pénalités et la réglementation en vigueur en RDC
"""
from datetime import datetime
from enum import Enum
from app.extensions import db
from app.models.base import BaseModel


class TypeKPIReglementaire(Enum):
    """Types de KPIs réglementaires"""
    QUALITE_SERVICE = "qualite_service"  # Coupures, interruptions
    CONFORMITE_TECHNIQUE = "conformite_technique"  # Normes techniques
    DELAIS_RACCORDEMENT = "delais_raccordement"  # Temps de raccordement
    TARIFICATION = "tarification"  # Respect des tarifs
    FACTURATION = "facturation"  # Délais de facturation
    REPORTING = "reporting"  # Remise des rapports
    MAINTENANCE = "maintenance"  # Entretien des infrastructures
    ENVIRONNEMENT = "environnement"  # Conformité environnementale


class SeveriteViolation(Enum):
    """Sévérité des violations réglementaires"""
    MINEURE = "mineure"  # Avertissement
    MODEREE = "moderee"  # Amende mineure
    MAJEURE = "majeure"  # Amende importante
    CRITIQUE = "critique"  # Suspension possible


class KPIReglementaire(BaseModel):
    """
    KPI réglementaire avec seuils et pénalités selon la réglementation RDC
    """
    __tablename__ = 'kpis_reglementaires'
    
    # Identification
    code = db.Column(db.String(50), nullable=False, unique=True)
    nom = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    type_kpi = db.Column(db.Enum(TypeKPIReglementaire), nullable=False)
    
    # Seuils réglementaires
    seuil_excellent = db.Column(db.Float)  # Seuil d'excellence
    seuil_acceptable = db.Column(db.Float)  # Seuil acceptable
    seuil_limite = db.Column(db.Float)  # Seuil limite avant pénalité
    seuil_critique = db.Column(db.Float)  # Seuil critique (suspension possible)
    
    # Unité de mesure
    unite = db.Column(db.String(50))  # %, heures, jours, etc.
    sens_amelioration = db.Column(db.String(20), default='diminution')  # 'diminution' ou 'augmentation'
    
    # Pénalités associées (en USD)
    penalite_moderee = db.Column(db.Float)  # Amende pour violation modérée
    penalite_majeure = db.Column(db.Float)  # Amende pour violation majeure
    penalite_critique = db.Column(db.Float)  # Amende pour violation critique
    
    # Références réglementaires
    reference_legale = db.Column(db.String(500))  # Article de loi/décret
    autorite_controle = db.Column(db.String(200))  # ARE, Ministère, etc.
    
    def evaluer_performance(self, valeur):
        """Évaluer la performance par rapport aux seuils"""
        if self.sens_amelioration == 'diminution':
            # Plus la valeur est faible, mieux c'est (ex: taux de coupures)
            if valeur <= self.seuil_excellent:
                return 'excellent', None
            elif valeur <= self.seuil_acceptable:
                return 'acceptable', None
            elif valeur <= self.seuil_limite:
                return 'limite', self.penalite_moderee
            else:
                return 'critique', self.penalite_critique
        else:
            # Plus la valeur est élevée, mieux c'est (ex: taux de disponibilité)
            if valeur >= self.seuil_excellent:
                return 'excellent', None
            elif valeur >= self.seuil_acceptable:
                return 'acceptable', None
            elif valeur >= self.seuil_limite:
                return 'limite', self.penalite_moderee
            else:
                return 'critique', self.penalite_critique


class PerformanceOperateurKPI(BaseModel):
    """
    Performance d'un opérateur sur un KPI réglementaire
    """
    __tablename__ = 'performances_operateur_kpi'
    
    # Relations
    operateur_id = db.Column(db.Integer, db.ForeignKey('operateurs.id'), nullable=False)
    kpi_id = db.Column(db.Integer, db.ForeignKey('kpis_reglementaires.id'), nullable=False)
    
    # Période
    mois = db.Column(db.Integer, nullable=False)  # 1-12
    annee = db.Column(db.Integer, nullable=False)
    
    # Performance
    valeur_mesuree = db.Column(db.Float, nullable=False)
    evaluation = db.Column(db.String(50))  # excellent, acceptable, limite, critique
    penalite_appliquee = db.Column(db.Float, default=0)  # Montant de la pénalité en USD
    
    # Statut
    verifie = db.Column(db.Boolean, default=False)
    date_verification = db.Column(db.DateTime)
    verifiee_par = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relations
    operateur = db.relationship('Operateur', backref='performances_kpi')
    kpi = db.relationship('KPIReglementaire', backref='performances')
    # verificateur = db.relationship('User', foreign_keys=[verifiee_par])  # Temporairement commenté
    
    def calculer_evaluation(self):
        """Calculer automatiquement l'évaluation et la pénalité"""
        if self.kpi:
            evaluation, penalite = self.kpi.evaluer_performance(self.valeur_mesuree)
            self.evaluation = evaluation
            self.penalite_appliquee = penalite or 0
            return evaluation, penalite
        return None, None


class SanctionReglementaire(BaseModel):
    """
    Sanction appliquée à un opérateur pour non-conformité
    """
    __tablename__ = 'sanctions_reglementaires'
    
    # Relations
    operateur_id = db.Column(db.Integer, db.ForeignKey('operateurs.id'), nullable=False)
    performance_kpi_id = db.Column(db.Integer, db.ForeignKey('performances_operateur_kpi.id'))
    
    # Détails de la sanction
    type_sanction = db.Column(db.String(100))  # Avertissement, Amende, Suspension
    motif = db.Column(db.Text, nullable=False)
    montant_amende = db.Column(db.Float)  # En USD
    
    # Dates
    date_infraction = db.Column(db.Date, nullable=False)
    date_notification = db.Column(db.Date)
    date_paiement = db.Column(db.Date)
    date_echeance = db.Column(db.Date)
    
    # Statut
    statut = db.Column(db.String(50), default='notifiee')  # notifiee, payee, en_cours, contestee
    
    # Autorité
    emise_par = db.Column(db.String(200), default='ARE')
    numero_decision = db.Column(db.String(100))
    
    # Relations
    operateur = db.relationship('Operateur', backref='sanctions')
    performance_kpi = db.relationship('PerformanceOperateurKPI', backref='sanctions')
    
    @property
    def est_payee(self):
        return self.date_paiement is not None
    
    @property
    def est_en_retard(self):
        return (self.date_echeance and 
                self.date_echeance < datetime.now().date() and 
                not self.est_payee)