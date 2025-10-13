"""
Services pour le système de workflow de validation
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import and_, or_
from flask import current_app
from app.extensions import db
from app.models.workflow import (
    Workflow, ValidationRapport, HistoriqueValidation, ValidateurDesigne,
    TypeRapport, StatutWorkflow, TypeAction
)
from app.models.utilisateurs import User
from app.models.operateurs import Operateur


class WorkflowService:
    """Service pour la gestion du workflow de validation"""
    
    @staticmethod
    def creer_workflow_defaut():
        """Créer les workflows par défaut pour tous les types de rapports"""
        workflows_defaut = [
            {
                'type_rapport': TypeRapport.PRODUCTION,
                'nom': 'Validation Production',
                'description': 'Workflow pour les rapports de production électrique',
                'delai_validation': 48,
                'validateurs_requis': 1,
                'rappel_automatique': True
            },
            {
                'type_rapport': TypeRapport.TRANSPORT,
                'nom': 'Validation Transport',
                'description': 'Workflow pour les rapports de transport d\'électricité',
                'delai_validation': 72,
                'validateurs_requis': 1,
                'rappel_automatique': True
            },
            {
                'type_rapport': TypeRapport.DISTRIBUTION,
                'nom': 'Validation Distribution',
                'description': 'Workflow pour les rapports de distribution électrique',
                'delai_validation': 72,
                'validateurs_requis': 1,
                'rappel_automatique': True
            },
            {
                'type_rapport': TypeRapport.MAINTENANCE,
                'nom': 'Validation Maintenance',
                'description': 'Workflow pour les rapports de maintenance',
                'delai_validation': 24,
                'validateurs_requis': 1,
                'rappel_automatique': True
            },
            {
                'type_rapport': TypeRapport.INCIDENT,
                'nom': 'Validation Incident',
                'description': 'Workflow pour les rapports d\'incident',
                'delai_validation': 12,
                'validateurs_requis': 1,
                'rappel_automatique': True
            },
            {
                'type_rapport': TypeRapport.FINANCIER,
                'nom': 'Validation Financier',
                'description': 'Workflow pour les rapports financiers',
                'delai_validation': 120,
                'validateurs_requis': 2,
                'rappel_automatique': True
            },
            {
                'type_rapport': TypeRapport.TECHNIQUE,
                'nom': 'Validation Technique',
                'description': 'Workflow pour les rapports techniques',
                'delai_validation': 96,
                'validateurs_requis': 1,
                'rappel_automatique': True
            },
            {
                'type_rapport': TypeRapport.ENVIRONNEMENTAL,
                'nom': 'Validation Environnemental',
                'description': 'Workflow pour les rapports environnementaux',
                'delai_validation': 168,
                'validateurs_requis': 1,
                'rappel_automatique': True
            }
        ]
        
        created_count = 0
        try:
            for workflow_data in workflows_defaut:
                # Vérifier si le workflow existe déjà
                workflow_existant = Workflow.query.filter_by(
                    type_rapport=workflow_data['type_rapport']
                ).first()
                
                if not workflow_existant:
                    workflow = Workflow(**workflow_data)
                    workflow.save()
                    created_count += 1
                    current_app.logger.info(f"Workflow créé pour {workflow_data['type_rapport'].value}")
            
            return {
                'success': True,
                'created': created_count,
                'message': f'{created_count} workflows créés avec succès'
            }
            
        except Exception as e:
            current_app.logger.error(f"Erreur lors de la création des workflows: {str(e)}")
            return {
                'success': False,
                'created': created_count,
                'message': f'Erreur: {str(e)}'
            }
    
    @staticmethod
    def soumettre_rapport(rapport_id: int, type_rapport: TypeRapport, 
                         utilisateur_id: int, commentaires: str = None, 
                         priorite: int = 1) -> Optional[ValidationRapport]:
        """
        Soumettre un rapport pour validation
        
        Args:
            rapport_id: ID du rapport
            type_rapport: Type de rapport
            utilisateur_id: ID de l'utilisateur qui soumet
            commentaires: Commentaires de soumission
            priorite: Priorité (1=normale, 2=urgente, 3=critique)
        
        Returns:
            ValidationRapport créé ou None si erreur
        """
        try:
            # Récupérer le workflow
            workflow = Workflow.get_workflow_for_type(type_rapport)
            if not workflow:
                current_app.logger.error(f"Aucun workflow trouvé pour {type_rapport.value}")
                return None
            
            # Vérifier si une validation existe déjà
            validation_existante = ValidationRapport.query.filter_by(rapport_id=rapport_id).first()
            if validation_existante and validation_existante.statut != StatutWorkflow.BROUILLON:
                current_app.logger.warning(f"Rapport {rapport_id} déjà soumis")
                return None
            
            # Créer ou mettre à jour la validation
            if validation_existante:
                validation = validation_existante
            else:
                validation = ValidationRapport(
                    rapport_id=rapport_id,
                    type_rapport=type_rapport,
                    workflow_id=workflow.id,
                    etape='validation_initiale'
                )
            
            validation.priorite = priorite
            
            # Assigner un validateur
            validateur = WorkflowService.assigner_validateur(1, type_rapport)  # TODO: récupérer operateur_id
            if validateur:
                validation.validateur_id = validateur.id
            
            # Soumettre
            if validation.soumettre(utilisateur_id):
                # Ajouter commentaires
                if commentaires:
                    HistoriqueValidation.ajouter_action(
                        rapport_id=rapport_id,
                        action=TypeAction.MODIFICATION,
                        utilisateur_id=utilisateur_id,
                        details=f"Commentaires: {commentaires}",
                        validation_id=validation.id
                    )
                
                return validation
            
        except Exception as e:
            current_app.logger.error(f"Erreur soumission rapport {rapport_id}: {str(e)}")
            db.session.rollback()
        
        return None
    
    @staticmethod
    def assigner_validateur(operateur_id: int, type_rapport: TypeRapport) -> Optional[User]:
        """
        Assigner un validateur pour un rapport
        
        Args:
            operateur_id: ID de l'opérateur
            type_rapport: Type de rapport
        
        Returns:
            User validateur ou None
        """
        # Chercher un validateur désigné
        validateur_designe = ValidateurDesigne.query.filter_by(
            operateur_id=operateur_id,
            type_rapport=type_rapport,
            actif=True
        ).order_by(ValidateurDesigne.niveau_validation.asc()).first()
        
        if validateur_designe:
            return User.query.get(validateur_designe.validateur_id)
        
        # Si pas de validateur désigné, prendre un admin
        admin = User.query.filter_by(role='super_admin', actif=True).first()
        return admin
    
    @staticmethod
    def valider_rapport(validation_id: int, validateur_id: int, 
                       action: str, commentaires: str, 
                       signature: str = None) -> bool:
        """
        Valider, rejeter ou demander modification d'un rapport
        
        Args:
            validation_id: ID de la validation
            validateur_id: ID du validateur
            action: 'valider', 'rejeter', 'demander_modification'
            commentaires: Commentaires obligatoires
            signature: Signature électronique (optionnel)
        
        Returns:
            True si succès, False sinon
        """
        try:
            validation = ValidationRapport.query.get(validation_id)
            if not validation:
                return False
            
            if action == 'valider':
                return validation.valider(validateur_id, commentaires, signature)
            elif action == 'rejeter':
                return validation.rejeter(validateur_id, commentaires)
            elif action == 'demander_modification':
                validation.statut = StatutWorkflow.BROUILLON
                validation.save()
                
                HistoriqueValidation.ajouter_action(
                    rapport_id=validation.rapport_id,
                    action=TypeAction.MODIFICATION,
                    utilisateur_id=validateur_id,
                    details=f"Modifications demandées: {commentaires}",
                    validation_id=validation.id
                )
                return True
            
            return False
            
        except Exception as e:
            current_app.logger.error(f"Erreur validation {validation_id}: {str(e)}")
            db.session.rollback()
            return False
    
    @staticmethod
    def get_validations_en_attente(validateur_id: int = None) -> List[ValidationRapport]:
        """
        Récupérer les validations en attente
        
        Args:
            validateur_id: ID du validateur (optionnel)
        
        Returns:
            Liste des validations en attente
        """
        query = ValidationRapport.query.filter(
            ValidationRapport.statut.in_([StatutWorkflow.SOUMIS, StatutWorkflow.EN_VALIDATION])
        )
        
        if validateur_id:
            query = query.filter_by(validateur_id=validateur_id)
        
        return query.order_by(
            ValidationRapport.priorite.desc(),
            ValidationRapport.date_soumission.asc()
        ).all()
    
    @staticmethod
    def get_validations_expirees() -> List[ValidationRapport]:
        """Récupérer les validations expirées"""
        return ValidationRapport.query.filter(
            ValidationRapport.statut.in_([StatutWorkflow.SOUMIS, StatutWorkflow.EN_VALIDATION]),
            ValidationRapport.date_expiration < datetime.utcnow()
        ).all()
    
    @staticmethod
    def envoyer_relance(validation_id: int, utilisateur_id: int) -> bool:
        """
        Envoyer une relance pour une validation
        
        Args:
            validation_id: ID de la validation
            utilisateur_id: ID de l'utilisateur qui envoie la relance
        
        Returns:
            True si succès
        """
        try:
            validation = ValidationRapport.query.get(validation_id)
            if not validation:
                return False
            
            validation.rappels_envoyes += 1
            validation.save()
            
            HistoriqueValidation.ajouter_action(
                rapport_id=validation.rapport_id,
                action=TypeAction.RELANCE,
                utilisateur_id=utilisateur_id,
                details=f"Relance #{validation.rappels_envoyes} envoyée",
                validation_id=validation.id
            )
            
            # TODO: Envoyer notification email/système
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Erreur relance {validation_id}: {str(e)}")
            db.session.rollback()
            return False
    
    @staticmethod
    def get_statistiques_workflow(workflow_id: int = None) -> Dict[str, Any]:
        """
        Récupérer les statistiques du workflow
        
        Args:
            workflow_id: ID du workflow (optionnel)
        
        Returns:
            Dictionnaire des statistiques
        """
        query = ValidationRapport.query
        if workflow_id:
            query = query.filter_by(workflow_id=workflow_id)
        
        total = query.count()
        validees = query.filter_by(statut=StatutWorkflow.VALIDE).count()
        rejetees = query.filter_by(statut=StatutWorkflow.REJETE).count()
        en_attente = query.filter(
            ValidationRapport.statut.in_([StatutWorkflow.SOUMIS, StatutWorkflow.EN_VALIDATION])
        ).count()
        
        # Calcul du délai moyen (en heures)
        validations_terminees = query.filter(
            ValidationRapport.date_validation.isnot(None)
        ).all()
        
        delai_moyen = 0
        if validations_terminees:
            delais = []
            for v in validations_terminees:
                if v.date_soumission and v.date_validation:
                    delta = v.date_validation - v.date_soumission
                    delais.append(delta.total_seconds() / 3600)  # en heures
            
            if delais:
                delai_moyen = sum(delais) / len(delais)
        
        # Taux de validation
        taux_validation = 0
        if total > 0:
            taux_validation = (validees / total) * 100
        
        return {
            'total_validations': total,
            'validees': validees,
            'rejetees': rejetees,
            'en_attente': en_attente,
            'delai_moyen': f"{delai_moyen:.1f}h" if delai_moyen > 0 else "N/A",
            'taux_validation': f"{taux_validation:.1f}" if taux_validation > 0 else "0.0"
        }
    
    @staticmethod
    def nettoyer_validations_expirees():
        """
        Marquer les validations expirées comme expirées
        Fonction à exécuter périodiquement
        """
        try:
            validations_expirees = ValidationRapport.get_validations_expirees()
            
            for validation in validations_expirees:
                validation.statut = StatutWorkflow.EXPIRE
                validation.save()
                
                HistoriqueValidation.ajouter_action(
                    rapport_id=validation.rapport_id,
                    action=TypeAction.EXPIRATION,
                    utilisateur_id=1,  # Système
                    details="Validation expirée automatiquement",
                    validation_id=validation.id
                )
            
            current_app.logger.info(f"{len(validations_expirees)} validations marquées comme expirées")
            return len(validations_expirees)
            
        except Exception as e:
            current_app.logger.error(f"Erreur nettoyage validations: {str(e)}")
            db.session.rollback()
            return 0