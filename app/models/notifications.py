"""
Modèles pour le système de notifications et messagerie interne
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.models.base import BaseModel
from app.extensions import db


class TypeNotification(enum.Enum):
    """Types de notifications disponibles"""
    RAPPEL_RAPPORT = "rappel_rapport"
    VALIDATION_RAPPORT = "validation_rapport"
    REJET_RAPPORT = "rejet_rapport"
    ALERTE_DONNEES = "alerte_donnees"
    MESSAGE_SYSTEME = "message_systeme"
    MAINTENANCE_PLANIFIEE = "maintenance_planifiee"
    INCIDENT_TECHNIQUE = "incident_technique"
    NOUVELLE_REGLEMENTATION = "nouvelle_reglementation"


class Notification(BaseModel):
    """Modèle pour les notifications utilisateur"""
    __tablename__ = 'notifications'
    
    # Relations
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    user = relationship('User', backref='notifications')
    
    # Informations de base
    type = Column(Enum(TypeNotification), nullable=False)
    titre = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    
    # Statut
    lue = Column(Boolean, default=False, nullable=False)
    archivee = Column(Boolean, default=False, nullable=False)
    
    # Métadonnées
    url_action = Column(String(500))  # URL vers laquelle rediriger lors du clic
    donnees_json = Column(Text)  # Données supplémentaires en JSON
    priorite = Column(Integer, default=1)  # 1=normale, 2=importante, 3=urgente
    
    # Références optionnelles - utilisons une approche générique
    rapport_type = Column(String(50))  # Type de rapport (hydro, thermique, solaire, transport, distribution)
    rapport_id = Column(Integer)  # ID du rapport - pas de FK pour permettre flexibilité
    operateur_id = Column(Integer, ForeignKey('operateurs.id'), nullable=True)
    
    def __repr__(self):
        return f'<Notification {self.id}: {self.titre}>'
    
    def marquer_comme_lue(self):
        """Marquer la notification comme lue"""
        self.lue = True
        self.save()
    
    def archiver(self):
        """Archiver la notification"""
        self.archivee = True
        self.save()
    
    @property
    def css_class(self):
        """Classe CSS selon la priorité"""
        if self.priorite == 3:
            return 'notification-urgent'
        elif self.priorite == 2:
            return 'notification-important'
        return 'notification-normal'
    
    @property
    def icon_class(self):
        """Icône selon le type de notification"""
        icons = {
            TypeNotification.RAPPEL_RAPPORT: 'fas fa-clock',
            TypeNotification.VALIDATION_RAPPORT: 'fas fa-check-circle',
            TypeNotification.REJET_RAPPORT: 'fas fa-times-circle',
            TypeNotification.ALERTE_DONNEES: 'fas fa-exclamation-triangle',
            TypeNotification.MESSAGE_SYSTEME: 'fas fa-info-circle',
            TypeNotification.MAINTENANCE_PLANIFIEE: 'fas fa-tools',
            TypeNotification.INCIDENT_TECHNIQUE: 'fas fa-bolt',
            TypeNotification.NOUVELLE_REGLEMENTATION: 'fas fa-gavel'
        }
        return icons.get(self.type, 'fas fa-bell')
    
    def to_dict(self):
        """Conversion en dictionnaire pour JSON"""
        return {
            'id': self.id,
            'type': self.type.value if self.type else None,
            'titre': self.titre,
            'message': self.message,
            'lue': self.lue,
            'priorite': self.priorite,
            'url_action': self.url_action,
            'icon_class': self.icon_class,
            'css_class': self.css_class,
            'date_creation': self.date_creation.isoformat() if self.date_creation else None
        }


class MessageInterne(BaseModel):
    """Modèle pour la messagerie interne"""
    __tablename__ = 'messages_internes'
    
    # Relations
    expediteur_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    expediteur = relationship('User', foreign_keys=[expediteur_id], backref='messages_envoyes')
    
    destinataire_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    destinataire = relationship('User', foreign_keys=[destinataire_id], backref='messages_recus')
    
    # Contenu
    sujet = Column(String(300), nullable=False)
    contenu = Column(Text, nullable=False)
    
    # Statut
    lu = Column(Boolean, default=False, nullable=False)
    archive_expediteur = Column(Boolean, default=False, nullable=False)
    archive_destinataire = Column(Boolean, default=False, nullable=False)
    
    # Réponse
    message_parent_id = Column(Integer, ForeignKey('messages_internes.id'), nullable=True)
    message_parent = relationship('MessageInterne', remote_side='MessageInterne.id', backref='reponses')
    
    # Métadonnées
    priorite = Column(Integer, default=1)  # 1=normale, 2=importante, 3=urgente
    
    def __repr__(self):
        return f'<Message {self.id}: {self.sujet}>'
    
    def marquer_comme_lu(self):
        """Marquer le message comme lu"""
        self.lu = True
        self.save()
    
    def archiver_pour_expediteur(self):
        """Archiver le message pour l'expéditeur"""
        self.archive_expediteur = True
        self.save()
    
    def archiver_pour_destinataire(self):
        """Archiver le message pour le destinataire"""
        self.archive_destinataire = True
        self.save()
    
    @property
    def css_class(self):
        """Classe CSS selon la priorité"""
        if self.priorite == 3:
            return 'message-urgent'
        elif self.priorite == 2:
            return 'message-important'
        return 'message-normal'
    
    @property
    def est_reponse(self):
        """Vérifie si c'est une réponse à un autre message"""
        return self.message_parent_id is not None
    
    def to_dict(self):
        """Conversion en dictionnaire pour JSON"""
        return {
            'id': self.id,
            'expediteur': {
                'id': self.expediteur.id,
                'nom': f"{self.expediteur.prenom} {self.expediteur.nom}" if self.expediteur.prenom else self.expediteur.username
            },
            'destinataire': {
                'id': self.destinataire.id,
                'nom': f"{self.destinataire.prenom} {self.destinataire.nom}" if self.destinataire.prenom else self.destinataire.username
            },
            'sujet': self.sujet,
            'contenu': self.contenu,
            'lu': self.lu,
            'priorite': self.priorite,
            'css_class': self.css_class,
            'est_reponse': self.est_reponse,
            'date_creation': self.date_creation.isoformat() if self.date_creation else None
        }


class TemplateNotification(BaseModel):
    """Modèle pour les templates de notifications"""
    __tablename__ = 'templates_notifications'
    
    # Identification
    code = Column(String(100), unique=True, nullable=False)
    nom = Column(String(200), nullable=False)
    
    # Templates
    titre_template = Column(String(300), nullable=False)
    message_template = Column(Text, nullable=False)
    
    # Configuration
    type_notification = Column(Enum(TypeNotification), nullable=False)
    priorite_defaut = Column(Integer, default=1)
    url_template = Column(String(500))  # Template d'URL avec variables
    
    # Activation
    actif = Column(Boolean, default=True, nullable=False)
    
    def __repr__(self):
        return f'<TemplateNotification {self.code}: {self.nom}>'
    
    def generer_notification(self, user_id, variables=None):
        """Générer une notification à partir de ce template"""
        if not variables:
            variables = {}
        
        # Remplacer les variables dans le titre et le message
        titre = self.titre_template.format(**variables)
        message = self.message_template.format(**variables)
        url_action = self.url_template.format(**variables) if self.url_template else None
        
        notification = Notification(
            user_id=user_id,
            type=self.type_notification,
            titre=titre,
            message=message,
            priorite=self.priorite_defaut,
            url_action=url_action
        )
        
        return notification
    
    def to_dict(self):
        """Conversion en dictionnaire pour JSON"""
        return {
            'id': self.id,
            'code': self.code,
            'nom': self.nom,
            'titre_template': self.titre_template,
            'message_template': self.message_template,
            'type_notification': self.type_notification.value if self.type_notification else None,
            'priorite_defaut': self.priorite_defaut,
            'actif': self.actif
        }


class PreferenceNotification(BaseModel):
    """Modèle pour les préférences de notification des utilisateurs"""
    __tablename__ = 'preferences_notifications'
    
    # Relations
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    user = relationship('User', backref='preferences_notifications')
    
    # Préférences par type
    rappel_rapport = Column(Boolean, default=True)
    validation_rapport = Column(Boolean, default=True)
    rejet_rapport = Column(Boolean, default=True)
    alerte_donnees = Column(Boolean, default=True)
    message_systeme = Column(Boolean, default=True)
    maintenance_planifiee = Column(Boolean, default=True)
    incident_technique = Column(Boolean, default=True)
    nouvelle_reglementation = Column(Boolean, default=True)
    
    # Préférences globales
    notifications_email = Column(Boolean, default=False)
    notifications_browser = Column(Boolean, default=True)
    digest_quotidien = Column(Boolean, default=False)
    digest_hebdomadaire = Column(Boolean, default=False)
    
    def __repr__(self):
        return f'<PreferenceNotification user_id={self.user_id}>'
    
    def accepte_type(self, type_notification):
        """Vérifie si l'utilisateur accepte ce type de notification"""
        if isinstance(type_notification, str):
            type_notification = TypeNotification(type_notification)
        
        mapping = {
            TypeNotification.RAPPEL_RAPPORT: self.rappel_rapport,
            TypeNotification.VALIDATION_RAPPORT: self.validation_rapport,
            TypeNotification.REJET_RAPPORT: self.rejet_rapport,
            TypeNotification.ALERTE_DONNEES: self.alerte_donnees,
            TypeNotification.MESSAGE_SYSTEME: self.message_systeme,
            TypeNotification.MAINTENANCE_PLANIFIEE: self.maintenance_planifiee,
            TypeNotification.INCIDENT_TECHNIQUE: self.incident_technique,
            TypeNotification.NOUVELLE_REGLEMENTATION: self.nouvelle_reglementation
        }
        
        return mapping.get(type_notification, True)
    
    def to_dict(self):
        """Conversion en dictionnaire pour JSON"""
        return {
            'user_id': self.user_id,
            'rappel_rapport': self.rappel_rapport,
            'validation_rapport': self.validation_rapport,
            'rejet_rapport': self.rejet_rapport,
            'alerte_donnees': self.alerte_donnees,
            'message_systeme': self.message_systeme,
            'maintenance_planifiee': self.maintenance_planifiee,
            'incident_technique': self.incident_technique,
            'nouvelle_reglementation': self.nouvelle_reglementation,
            'notifications_email': self.notifications_email,
            'notifications_browser': self.notifications_browser,
            'digest_quotidien': self.digest_quotidien,
            'digest_hebdomadaire': self.digest_hebdomadaire
        }