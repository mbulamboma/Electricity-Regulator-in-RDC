"""
Service de notifications - Utilitaires pour créer et gérer les notifications
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import and_, or_

from app.extensions import db
from app.models.notifications import (
    Notification, MessageInterne, TemplateNotification, PreferenceNotification,
    TypeNotification
)
from app.models.utilisateurs import User


class NotificationService:
    """Service pour gérer les notifications"""
    
    @staticmethod
    def creer_notification(
        user_id: int,
        type_notification: TypeNotification,
        titre: str,
        message: str,
        priorite: int = 1,
        url_action: Optional[str] = None,
        **kwargs
    ) -> Notification:
        """Créer une nouvelle notification"""
        
        # Vérifier les préférences de l'utilisateur
        prefs = PreferenceNotification.query.filter_by(user_id=user_id).first()
        if prefs and not prefs.accepte_type(type_notification):
            return None
        
        notification = Notification(
            user_id=user_id,
            type=type_notification,
            titre=titre,
            message=message,
            priorite=priorite,
            url_action=url_action,
            **kwargs
        )
        
        notification.save()
        return notification
    
    @staticmethod
    def creer_notification_template(
        user_id: int,
        code_template: str,
        variables: Dict[str, Any] = None
    ) -> Optional[Notification]:
        """Créer une notification à partir d'un template"""
        
        template = TemplateNotification.query.filter_by(
            code=code_template, actif=True
        ).first()
        
        if not template:
            return None
        
        notification = template.generer_notification(user_id, variables or {})
        notification.save()
        return notification
    
    @staticmethod
    def notifier_plusieurs_utilisateurs(
        user_ids: List[int],
        type_notification: TypeNotification,
        titre: str,
        message: str,
        priorite: int = 1,
        url_action: Optional[str] = None
    ) -> List[Notification]:
        """Créer une notification pour plusieurs utilisateurs"""
        
        notifications = []
        for user_id in user_ids:
            notif = NotificationService.creer_notification(
                user_id, type_notification, titre, message, priorite, url_action
            )
            if notif:
                notifications.append(notif)
        
        return notifications
    
    @staticmethod
    def notifier_role(
        role: str,
        type_notification: TypeNotification,
        titre: str,
        message: str,
        priorite: int = 1,
        url_action: Optional[str] = None
    ) -> List[Notification]:
        """Notifier tous les utilisateurs d'un rôle"""
        
        users = User.query.filter_by(role=role, actif=True).all()
        user_ids = [user.id for user in users]
        
        return NotificationService.notifier_plusieurs_utilisateurs(
            user_ids, type_notification, titre, message, priorite, url_action
        )
    
    @staticmethod
    def notifier_operateur(
        operateur_id: int,
        type_notification: TypeNotification,
        titre: str,
        message: str,
        priorite: int = 1,
        url_action: Optional[str] = None
    ) -> List[Notification]:
        """Notifier tous les utilisateurs d'un opérateur"""
        
        users = User.query.filter_by(operateur_id=operateur_id, actif=True).all()
        user_ids = [user.id for user in users]
        
        return NotificationService.notifier_plusieurs_utilisateurs(
            user_ids, type_notification, titre, message, priorite, url_action
        )
    
    @staticmethod
    def marquer_anciennes_comme_lues(user_id: int, jours: int = 30) -> int:
        """Marquer automatiquement les anciennes notifications comme lues"""
        
        date_limite = datetime.now() - timedelta(days=jours)
        
        notifications = Notification.query.filter(
            and_(
                Notification.user_id == user_id,
                Notification.lue == False,
                Notification.date_creation < date_limite,
                Notification.actif == True
            )
        ).all()
        
        count = 0
        for notification in notifications:
            notification.marquer_comme_lue()
            count += 1
        
        return count
    
    @staticmethod
    def nettoyer_notifications_archivees(jours: int = 90) -> int:
        """Supprimer définitivement les notifications archivées anciennes"""
        
        date_limite = datetime.now() - timedelta(days=jours)
        
        notifications = Notification.query.filter(
            and_(
                Notification.archivee == True,
                Notification.date_modification < date_limite
            )
        ).all()
        
        count = 0
        for notification in notifications:
            notification.delete()
            count += 1
        
        return count


class MessageService:
    """Service pour gérer la messagerie interne"""
    
    @staticmethod
    def envoyer_message(
        expediteur_id: int,
        destinataire_id: int,
        sujet: str,
        contenu: str,
        priorite: int = 1,
        message_parent_id: Optional[int] = None
    ) -> MessageInterne:
        """Envoyer un message interne"""
        
        message = MessageInterne(
            expediteur_id=expediteur_id,
            destinataire_id=destinataire_id,
            sujet=sujet,
            contenu=contenu,
            priorite=priorite,
            message_parent_id=message_parent_id
        )
        
        message.save()
        
        # Créer une notification pour le destinataire
        NotificationService.creer_notification(
            destinataire_id,
            TypeNotification.MESSAGE_SYSTEME,
            f"Nouveau message: {sujet}",
            f"Vous avez reçu un nouveau message de {message.expediteur.prenom or message.expediteur.username}",
            priorite=priorite,
            url_action=f"/notifications/messages/{message.id}"
        )
        
        return message
    
    @staticmethod
    def diffuser_message(
        expediteur_id: int,
        destinataire_ids: List[int],
        sujet: str,
        contenu: str,
        priorite: int = 1
    ) -> List[MessageInterne]:
        """Diffuser un message à plusieurs destinataires"""
        
        messages = []
        for destinataire_id in destinataire_ids:
            message = MessageService.envoyer_message(
                expediteur_id, destinataire_id, sujet, contenu, priorite
            )
            messages.append(message)
        
        return messages
    
    @staticmethod
    def nettoyer_messages_archives(jours: int = 180) -> int:
        """Supprimer définitivement les messages archivés anciens"""
        
        date_limite = datetime.now() - timedelta(days=jours)
        
        messages = MessageInterne.query.filter(
            and_(
                or_(
                    MessageInterne.archive_expediteur == True,
                    MessageInterne.archive_destinataire == True
                ),
                MessageInterne.date_modification < date_limite
            )
        ).all()
        
        count = 0
        for message in messages:
            message.delete()
            count += 1
        
        return count


class TemplateService:
    """Service pour gérer les templates de notifications"""
    
    @staticmethod
    def creer_templates_defaut():
        """Créer les templates de notifications par défaut"""
        
        templates_defaut = [
            {
                'code': 'rappel_rapport_mensuel',
                'nom': 'Rappel rapport mensuel',
                'type_notification': TypeNotification.RAPPEL_RAPPORT,
                'titre_template': 'Rappel: Rapport {type_rapport} pour {mois}',
                'message_template': 'Votre rapport {type_rapport} pour {operateur} du mois de {mois} doit être soumis avant le {date_limite}.',
                'priorite_defaut': 2,
                'url_template': '/rapports/nouveau?type={type_rapport}'
            },
            {
                'code': 'validation_rapport',
                'nom': 'Validation de rapport',
                'type_notification': TypeNotification.VALIDATION_RAPPORT,
                'titre_template': 'Rapport validé: {type_rapport}',
                'message_template': 'Votre rapport {type_rapport} du {periode} a été validé par {validateur}.',
                'priorite_defaut': 1,
                'url_template': '/rapports/{rapport_id}'
            },
            {
                'code': 'rejet_rapport',
                'nom': 'Rejet de rapport',
                'type_notification': TypeNotification.REJET_RAPPORT,
                'titre_template': 'Rapport rejeté: {type_rapport}',
                'message_template': 'Votre rapport {type_rapport} du {periode} a été rejeté. Motif: {motif}',
                'priorite_defaut': 3,
                'url_template': '/rapports/{rapport_id}/modifier'
            },
            {
                'code': 'alerte_donnee_anormale',
                'nom': 'Alerte données anormales',
                'type_notification': TypeNotification.ALERTE_DONNEES,
                'titre_template': 'Alerte: Données anormales détectées',
                'message_template': 'Des valeurs anormales ont été détectées dans vos données {type_donnee}: {details}',
                'priorite_defaut': 2,
                'url_template': '/rapports/{rapport_id}#donnees'
            },
            {
                'code': 'maintenance_planifiee',
                'nom': 'Maintenance programmée',
                'type_notification': TypeNotification.MAINTENANCE_PLANIFIEE,
                'titre_template': 'Maintenance programmée le {date}',
                'message_template': 'Une maintenance du système est programmée le {date} de {heure_debut} à {heure_fin}. Certaines fonctionnalités seront indisponibles.',
                'priorite_defaut': 2
            },
            {
                'code': 'incident_technique',
                'nom': 'Incident technique',
                'type_notification': TypeNotification.INCIDENT_TECHNIQUE,
                'titre_template': 'Incident technique: {type_incident}',
                'message_template': 'Un incident technique a été détecté: {description}. Notre équipe travaille à la résolution.',
                'priorite_defaut': 3
            },
            {
                'code': 'nouvelle_reglementation',
                'nom': 'Nouvelle réglementation',
                'type_notification': TypeNotification.NOUVELLE_REGLEMENTATION,
                'titre_template': 'Nouvelle réglementation: {titre}',
                'message_template': 'Une nouvelle réglementation a été publiée: {description}. Date d\'entrée en vigueur: {date_vigueur}',
                'priorite_defaut': 2,
                'url_template': '/reglementations/{regulation_id}'
            }
        ]
        
        for template_data in templates_defaut:
            # Vérifier si le template existe déjà
            existing = TemplateNotification.query.filter_by(
                code=template_data['code']
            ).first()
            
            if not existing:
                template = TemplateNotification(**template_data)
                template.save()
    
    @staticmethod
    def utiliser_template(code: str, user_id: int, variables: Dict[str, Any]) -> Optional[Notification]:
        """Utiliser un template pour créer une notification"""
        return NotificationService.creer_notification_template(code, user_id, variables)


# Raccourcis pour les notifications fréquentes
def notifier_rappel_rapport(user_id: int, type_rapport: str, operateur: str, mois: str, date_limite: str):
    """Notifier un rappel de rapport"""
    return NotificationService.creer_notification_template(
        user_id,
        'rappel_rapport_mensuel',
        {
            'type_rapport': type_rapport,
            'operateur': operateur,
            'mois': mois,
            'date_limite': date_limite
        }
    )

def notifier_validation_rapport(user_id: int, type_rapport: str, periode: str, validateur: str, rapport_id: int):
    """Notifier la validation d'un rapport"""
    return NotificationService.creer_notification_template(
        user_id,
        'validation_rapport',
        {
            'type_rapport': type_rapport,
            'periode': periode,
            'validateur': validateur,
            'rapport_id': rapport_id
        }
    )

def notifier_rejet_rapport(user_id: int, type_rapport: str, periode: str, motif: str, rapport_id: int):
    """Notifier le rejet d'un rapport"""
    return NotificationService.creer_notification_template(
        user_id,
        'rejet_rapport',
        {
            'type_rapport': type_rapport,
            'periode': periode,
            'motif': motif,
            'rapport_id': rapport_id
        }
    )

def notifier_alerte_donnees(user_id: int, type_donnee: str, details: str, rapport_id: int):
    """Notifier une alerte sur des données anormales"""
    return NotificationService.creer_notification_template(
        user_id,
        'alerte_donnee_anormale',
        {
            'type_donnee': type_donnee,
            'details': details,
            'rapport_id': rapport_id
        }
    )