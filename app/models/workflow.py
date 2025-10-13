"""
Modèles pour le système de workflow de validation des rapports
"""
from datetime import datetime, timedelta
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
from app.extensions import db


class TypeRapport(Enum):
    """Types de rapports disponibles"""
    PRODUCTION = "production"
    TRANSPORT = "transport"
    DISTRIBUTION = "distribution"
    MAINTENANCE = "maintenance"
    INCIDENT = "incident"
    FINANCIER = "financier"
    TECHNIQUE = "technique"
    ENVIRONNEMENTAL = "environnemental"


class StatutWorkflow(Enum):
    """Statuts possibles dans le workflow"""
    BROUILLON = "brouillon"
    SOUMIS = "soumis"
    EN_VALIDATION = "en_validation"
    VALIDE = "valide"
    REJETE = "rejete"
    EXPIRE = "expire"


class TypeAction(Enum):
    """Types d'actions dans l'historique"""
    CREATION = "creation"
    SOUMISSION = "soumission"
    VALIDATION = "validation"
    REJET = "rejet"
    MODIFICATION = "modification"
    EXPIRATION = "expiration"
    RELANCE = "relance"


class Workflow(BaseModel):
    """
    Configuration du workflow pour chaque type de rapport
    """
    __tablename__ = 'workflows'
    
    type_rapport = Column(SQLEnum(TypeRapport), nullable=False, unique=True)
    nom = Column(String(100), nullable=False)
    description = Column(Text)
    etapes = Column(Text)  # JSON string avec les étapes
    delai_validation = Column(Integer, default=72)  # en heures
    validateurs_requis = Column(Integer, default=1)
    rappel_automatique = Column(Boolean, default=True)
    
    # Relations
    validations = relationship('ValidationRapport', backref='workflow_config', lazy='dynamic')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def to_dict(self):
        """Conversion en dictionnaire"""
        data = super().to_dict()
        data.update({
            'type_rapport': self.type_rapport.value if self.type_rapport else None,
            'etapes': self.etapes,
            'delai_validation': self.delai_validation,
            'validateurs_requis': self.validateurs_requis,
            'rappel_automatique': self.rappel_automatique
        })
        return data
    
    @staticmethod
    def get_workflow_for_type(type_rapport):
        """Récupère le workflow pour un type de rapport"""
        return Workflow.query.filter_by(type_rapport=type_rapport).first()
    
    def is_delai_expire(self, date_soumission):
        """Vérifie si le délai de validation est dépassé"""
        if not date_soumission:
            return False
        delai_max = date_soumission + timedelta(hours=self.delai_validation)
        return datetime.utcnow() > delai_max


class ValidationRapport(BaseModel):
    """
    Validation d'un rapport dans le workflow
    """
    __tablename__ = 'validations_rapport'
    
    # Clés étrangères
    rapport_id = Column(Integer, nullable=False, index=True)  # Référence générique
    type_rapport = Column(SQLEnum(TypeRapport), nullable=False)
    workflow_id = Column(Integer, ForeignKey('workflows.id'), nullable=False)
    validateur_id = Column(Integer, nullable=True)  # Référence vers users.id
    
    # Informations de validation
    etape = Column(String(50), nullable=False)
    statut = Column(SQLEnum(StatutWorkflow), nullable=False, default=StatutWorkflow.BROUILLON)
    
    # Données de validation
    date_soumission = Column(DateTime)
    date_validation = Column(DateTime)
    date_expiration = Column(DateTime)
    
    commentaires = Column(Text)
    signature_electronique = Column(String(255))
    donnees_originales = Column(Text)  # JSON des données avant modification
    
    # Métadonnées
    priorite = Column(Integer, default=1)  # 1=normale, 2=urgente, 3=critique
    rappels_envoyes = Column(Integer, default=0)
    
    # Relations (définies manuellement)
    # validateur = relationship('User', foreign_keys=[validateur_id])
    historique = relationship('HistoriqueValidation', back_populates='validation', lazy='dynamic', 
                            cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.date_soumission and not self.date_expiration:
            workflow = Workflow.get_workflow_for_type(self.type_rapport)
            if workflow:
                self.date_expiration = self.date_soumission + timedelta(hours=workflow.delai_validation)
    
    def to_dict(self):
        """Conversion en dictionnaire"""
        data = super().to_dict()
        data.update({
            'rapport_id': self.rapport_id,
            'type_rapport': self.type_rapport.value if self.type_rapport else None,
            'validateur_id': self.validateur_id,
            'validateur_nom': self.validateur.nom_complet if self.validateur else None,
            'etape': self.etape,
            'statut': self.statut.value if self.statut else None,
            'date_soumission': self.date_soumission.isoformat() if self.date_soumission else None,
            'date_validation': self.date_validation.isoformat() if self.date_validation else None,
            'date_expiration': self.date_expiration.isoformat() if self.date_expiration else None,
            'commentaires': self.commentaires,
            'priorite': self.priorite,
            'rappels_envoyes': self.rappels_envoyes,
            'est_expire': self.est_expire(),
            'temps_restant': self.temps_restant()
        })
        return data
    
    def soumettre(self, utilisateur_id):
        """Soumet le rapport pour validation"""
        if self.statut == StatutWorkflow.BROUILLON:
            self.statut = StatutWorkflow.SOUMIS
            self.date_soumission = datetime.utcnow()
            
            # Calcul de la date d'expiration
            workflow = Workflow.get_workflow_for_type(self.type_rapport)
            if workflow:
                self.date_expiration = self.date_soumission + timedelta(hours=workflow.delai_validation)
            
            # Enregistrement dans l'historique
            historique = HistoriqueValidation(
                rapport_id=self.rapport_id,
                validation_id=self.id,
                action=TypeAction.SOUMISSION,
                utilisateur_id=utilisateur_id,
                details=f"Rapport soumis pour validation - Type: {self.type_rapport.value}"
            )
            db.session.add(historique)
            self.save()
            return True
        return False
    
    def valider(self, validateur_id, commentaires=None, signature=None):
        """Valide le rapport"""
        if self.statut in [StatutWorkflow.SOUMIS, StatutWorkflow.EN_VALIDATION]:
            self.statut = StatutWorkflow.VALIDE
            self.validateur_id = validateur_id
            self.date_validation = datetime.utcnow()
            self.commentaires = commentaires
            self.signature_electronique = signature
            
            # Enregistrement dans l'historique
            historique = HistoriqueValidation(
                rapport_id=self.rapport_id,
                validation_id=self.id,
                action=TypeAction.VALIDATION,
                utilisateur_id=validateur_id,
                details=f"Rapport validé - Commentaires: {commentaires or 'Aucun'}"
            )
            db.session.add(historique)
            self.save()
            return True
        return False
    
    def rejeter(self, validateur_id, commentaires):
        """Rejette le rapport"""
        if self.statut in [StatutWorkflow.SOUMIS, StatutWorkflow.EN_VALIDATION]:
            self.statut = StatutWorkflow.REJETE
            self.validateur_id = validateur_id
            self.date_validation = datetime.utcnow()
            self.commentaires = commentaires
            
            # Enregistrement dans l'historique
            historique = HistoriqueValidation(
                rapport_id=self.rapport_id,
                validation_id=self.id,
                action=TypeAction.REJET,
                utilisateur_id=validateur_id,
                details=f"Rapport rejeté - Motif: {commentaires}"
            )
            db.session.add(historique)
            self.save()
            return True
        return False
    
    def est_expire(self):
        """Vérifie si la validation est expirée"""
        if not self.date_expiration:
            return False
        return datetime.utcnow() > self.date_expiration
    
    def temps_restant(self):
        """Calcule le temps restant avant expiration"""
        if not self.date_expiration:
            return None
        delta = self.date_expiration - datetime.utcnow()
        if delta.total_seconds() <= 0:
            return "Expiré"
        
        jours = delta.days
        heures = delta.seconds // 3600
        
        if jours > 0:
            return f"{jours}j {heures}h"
        else:
            return f"{heures}h"
    
    @staticmethod
    def get_validations_en_attente(validateur_id=None):
        """Récupère les validations en attente"""
        query = ValidationRapport.query.filter(
            ValidationRapport.statut.in_([StatutWorkflow.SOUMIS, StatutWorkflow.EN_VALIDATION])
        )
        if validateur_id:
            query = query.filter_by(validateur_id=validateur_id)
        return query.order_by(ValidationRapport.date_soumission.asc()).all()
    
    @staticmethod
    def get_validations_expirees():
        """Récupère les validations expirées"""
        return ValidationRapport.query.filter(
            ValidationRapport.statut.in_([StatutWorkflow.SOUMIS, StatutWorkflow.EN_VALIDATION]),
            ValidationRapport.date_expiration < datetime.utcnow()
        ).all()


class HistoriqueValidation(BaseModel):
    """
    Historique des actions dans le workflow de validation
    """
    __tablename__ = 'historique_validation'
    
    # Clés étrangères
    rapport_id = Column(Integer, nullable=False, index=True)  # Référence générique
    validation_id = Column(Integer, ForeignKey('validations_rapport.id'), nullable=True)
    utilisateur_id = Column(Integer, nullable=False)  # Référence vers users.id
    
    # Informations de l'action
    action = Column(SQLEnum(TypeAction), nullable=False)
    details = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Données additionnelles
    donnees_avant = Column(Text)  # JSON des données avant l'action
    donnees_apres = Column(Text)  # JSON des données après l'action
    adresse_ip = Column(String(45))
    user_agent = Column(Text)
    
    # Relations (définies manuellement)
    validation = relationship('ValidationRapport', back_populates='historique')
    # utilisateur = relationship('User', foreign_keys=[utilisateur_id])
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def to_dict(self):
        """Conversion en dictionnaire"""
        data = super().to_dict()
        data.update({
            'rapport_id': self.rapport_id,
            'validation_id': self.validation_id,
            'utilisateur_id': self.utilisateur_id,
            'utilisateur_nom': self.utilisateur.nom_complet if self.utilisateur else None,
            'action': self.action.value if self.action else None,
            'details': self.details,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'adresse_ip': self.adresse_ip,
            'user_agent': self.user_agent
        })
        return data
    
    @staticmethod
    def ajouter_action(rapport_id, action, utilisateur_id, details=None, 
                      donnees_avant=None, donnees_apres=None, validation_id=None):
        """Ajoute une action à l'historique"""
        historique = HistoriqueValidation(
            rapport_id=rapport_id,
            validation_id=validation_id,
            utilisateur_id=utilisateur_id,
            action=action,
            details=details,
            donnees_avant=donnees_avant,
            donnees_apres=donnees_apres
        )
        historique.save()
        return historique
    
    @staticmethod
    def get_historique_rapport(rapport_id):
        """Récupère l'historique complet d'un rapport"""
        return HistoriqueValidation.query.filter_by(rapport_id=rapport_id)\
                                        .order_by(HistoriqueValidation.timestamp.desc()).all()


class ValidateurDesigne(BaseModel):
    """
    Validateurs désignés pour chaque opérateur et type de rapport
    """
    __tablename__ = 'validateurs_designes'
    
    # Clés étrangères
    operateur_id = Column(Integer, nullable=False)  # Référence vers operateurs.id
    validateur_id = Column(Integer, nullable=False)  # Référence vers users.id
    type_rapport = Column(SQLEnum(TypeRapport), nullable=False)
    
    # Configuration
    niveau_validation = Column(Integer, default=1)  # Niveau dans la hiérarchie
    peut_valider_urgent = Column(Boolean, default=False)
    delai_max_validation = Column(Integer)  # en heures, override du workflow
    actif = Column(Boolean, default=True)
    
    # Relations (définies manuellement)
    # operateur = relationship('Operateur', foreign_keys=[operateur_id])
    # validateur = relationship('User', foreign_keys=[validateur_id])
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def to_dict(self):
        """Conversion en dictionnaire"""
        data = super().to_dict()
        data.update({
            'operateur_id': self.operateur_id,
            'operateur_nom': self.operateur.nom if self.operateur else None,
            'validateur_id': self.validateur_id,
            'validateur_nom': self.validateur.nom_complet if self.validateur else None,
            'type_rapport': self.type_rapport.value if self.type_rapport else None,
            'niveau_validation': self.niveau_validation,
            'peut_valider_urgent': self.peut_valider_urgent,
            'delai_max_validation': self.delai_max_validation,
            'actif': self.actif
        })
        return data
    
    @staticmethod
    def get_validateurs_pour_rapport(operateur_id, type_rapport):
        """Récupère les validateurs pour un opérateur et type de rapport"""
        return ValidateurDesigne.query.filter_by(
            operateur_id=operateur_id,
            type_rapport=type_rapport,
            actif=True
        ).order_by(ValidateurDesigne.niveau_validation.asc()).all()