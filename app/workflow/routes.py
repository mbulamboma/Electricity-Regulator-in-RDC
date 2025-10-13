"""
Routes pour le système de workflow de validation des rapports
"""
from datetime import datetime, timedelta
from flask import render_template, request, flash, redirect, url_for, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy import or_, and_
from app.workflow import bp
from app.workflow.forms import (
    SoumissionRapportForm, ValidationRapportForm, RechercheValidationsForm,
    ConfigurationWorkflowForm, ValidateurDesigneForm, CommentaireValidationForm,
    RelanceValidationForm
)
from app.models.workflow import (
    Workflow, ValidationRapport, HistoriqueValidation, ValidateurDesigne,
    TypeRapport, StatutWorkflow, TypeAction
)
from app.models.utilisateurs import User
from app.models.operateurs import Operateur
from app.extensions import db
from app.utils.helpers import admin_required
import json


@bp.route('/')
@login_required
def index():
    """Page d'accueil du workflow"""
    # Statistiques pour l'utilisateur
    stats = {
        'en_attente': 0,
        'validees': 0,
        'rejetees': 0,
        'expirees': 0
    }
    
    # Si c'est un validateur, compter ses validations
    if current_user.is_admin() or hasattr(current_user, 'designations_validateur'):
        validations = ValidationRapport.query.filter_by(validateur_id=current_user.id).all()
        for validation in validations:
            if validation.statut in [StatutWorkflow.SOUMIS, StatutWorkflow.EN_VALIDATION]:
                if validation.est_expire():
                    stats['expirees'] += 1
                else:
                    stats['en_attente'] += 1
            elif validation.statut == StatutWorkflow.VALIDE:
                stats['validees'] += 1
            elif validation.statut == StatutWorkflow.REJETE:
                stats['rejetees'] += 1
    
    # Validations urgentes
    validations_urgentes = ValidationRapport.query.filter(
        ValidationRapport.statut.in_([StatutWorkflow.SOUMIS, StatutWorkflow.EN_VALIDATION]),
        ValidationRapport.priorite >= 2
    ).order_by(ValidationRapport.date_soumission.asc()).limit(5).all()
    
    # Historique récent
    historique_recent = HistoriqueValidation.query.order_by(
        HistoriqueValidation.timestamp.desc()
    ).limit(10).all()
    
    return render_template('workflow/index.html',
                         stats=stats,
                         validations_urgentes=validations_urgentes,
                         historique_recent=historique_recent)


@bp.route('/soumettre/<int:rapport_id>', methods=['GET', 'POST'])
@login_required
def soumettre_rapport(rapport_id):
    """Soumettre un rapport pour validation"""
    form = SoumissionRapportForm()
    
    if form.validate_on_submit():
        try:
            # Vérifier si une validation existe déjà
            validation_existante = ValidationRapport.query.filter_by(rapport_id=rapport_id).first()
            
            if validation_existante and validation_existante.statut != StatutWorkflow.BROUILLON:
                flash('Ce rapport a déjà été soumis pour validation.', 'warning')
                return redirect(url_for('workflow.index'))
            
            # Récupérer le workflow pour ce type de rapport
            type_rapport = TypeRapport(form.type_rapport.data)
            workflow = Workflow.get_workflow_for_type(type_rapport)
            
            if not workflow:
                flash('Aucun workflow configuré pour ce type de rapport.', 'error')
                return redirect(url_for('workflow.index'))
            
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
            
            validation.priorite = form.priorite.data
            
            # Assigner un validateur (le premier disponible pour ce type)
            operateur_id = 1  # TODO: Récupérer l'opérateur du rapport
            validateurs = ValidateurDesigne.get_validateurs_pour_rapport(operateur_id, type_rapport)
            if validateurs:
                validation.validateur_id = validateurs[0].validateur_id
            
            # Soumettre
            if validation.soumettre(current_user.id):
                # Ajouter commentaires s'il y en a
                if form.commentaires.data:
                    HistoriqueValidation.ajouter_action(
                        rapport_id=rapport_id,
                        action=TypeAction.MODIFICATION,
                        utilisateur_id=current_user.id,
                        details=f"Commentaires de soumission: {form.commentaires.data}",
                        validation_id=validation.id
                    )
                
                flash('Rapport soumis avec succès pour validation.', 'success')
                
                # TODO: Envoyer notification au validateur
                
                return redirect(url_for('workflow.detail_validation', id=validation.id))
            else:
                flash('Erreur lors de la soumission du rapport.', 'error')
                
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la soumission: {str(e)}', 'error')
    
    form.rapport_id.data = rapport_id
    return render_template('workflow/soumettre.html', form=form, rapport_id=rapport_id)


@bp.route('/valider/<int:validation_id>', methods=['GET', 'POST'])
@login_required
def valider_rapport(validation_id):
    """Valider ou rejeter un rapport"""
    validation = ValidationRapport.query.get_or_404(validation_id)
    
    # Vérifier les permissions
    if not (current_user.is_admin() or validation.validateur_id == current_user.id):
        flash('Vous n\'êtes pas autorisé à valider ce rapport.', 'error')
        return redirect(url_for('workflow.index'))
    
    form = ValidationRapportForm()
    
    if form.validate_on_submit():
        try:
            action = form.action.data
            commentaires = form.commentaires.data
            signature = form.signature_electronique.data
            
            if action == 'valider':
                if validation.valider(current_user.id, commentaires, signature):
                    flash('Rapport validé avec succès.', 'success')
                    # TODO: Envoyer notification de validation
                else:
                    flash('Erreur lors de la validation.', 'error')
                    
            elif action == 'rejeter':
                if validation.rejeter(current_user.id, commentaires):
                    flash('Rapport rejeté.', 'info')
                    # TODO: Envoyer notification de rejet
                else:
                    flash('Erreur lors du rejet.', 'error')
                    
            elif action == 'demander_modification':
                # Remettre en brouillon et ajouter commentaires
                validation.statut = StatutWorkflow.BROUILLON
                validation.save()
                
                HistoriqueValidation.ajouter_action(
                    rapport_id=validation.rapport_id,
                    action=TypeAction.MODIFICATION,
                    utilisateur_id=current_user.id,
                    details=f"Modifications demandées: {commentaires}",
                    validation_id=validation.id
                )
                
                flash('Modifications demandées. Le rapport est remis en brouillon.', 'info')
                # TODO: Envoyer notification de demande de modification
            
            return redirect(url_for('workflow.detail_validation', id=validation.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la validation: {str(e)}', 'error')
    
    return render_template('workflow/valider.html', 
                         form=form, 
                         validation=validation)


@bp.route('/validation/<int:id>')
@login_required
def detail_validation(id):
    """Détail d'une validation"""
    validation = ValidationRapport.query.get_or_404(id)
    
    # Vérifier les permissions
    if not (current_user.is_admin() or 
            validation.validateur_id == current_user.id or
            # TODO: Vérifier si l'utilisateur est propriétaire du rapport
            True):
        flash('Accès non autorisé.', 'error')
        return redirect(url_for('workflow.index'))
    
    # Récupérer l'historique
    historique = HistoriqueValidation.get_historique_rapport(validation.rapport_id)
    
    # TODO: Récupérer les données du rapport original
    donnees_rapport = {
        'id': validation.rapport_id,
        'titre': f'Rapport #{validation.rapport_id}',
        'type': validation.type_rapport.value
    }
    
    return render_template('workflow/detail_validation.html',
                         validation=validation,
                         historique=historique,
                         donnees_rapport=donnees_rapport)


@bp.route('/historique/<int:rapport_id>')
@login_required
def historique_rapport(rapport_id):
    """Historique complet d'un rapport"""
    historique = HistoriqueValidation.get_historique_rapport(rapport_id)
    validations = ValidationRapport.query.filter_by(rapport_id=rapport_id).all()
    
    return render_template('workflow/historique.html',
                         rapport_id=rapport_id,
                         historique=historique,
                         validations=validations)


@bp.route('/liste')
@login_required
def liste_validations():
    """Liste des validations avec filtres"""
    form = RechercheValidationsForm()
    
    # Remplir les choix dynamiques
    validateurs = User.query.filter_by(actif=True).all()
    form.validateur.choices = [('', 'Tous les validateurs')] + \
                              [(str(u.id), u.nom_complet) for u in validateurs]
    
    # Construire la requête
    query = ValidationRapport.query
    
    # Filtrer selon les permissions
    if not current_user.is_admin():
        query = query.filter_by(validateur_id=current_user.id)
    
    # Appliquer les filtres
    if request.args.get('type_rapport'):
        query = query.filter_by(type_rapport=TypeRapport(request.args.get('type_rapport')))
    
    if request.args.get('statut'):
        query = query.filter_by(statut=StatutWorkflow(request.args.get('statut')))
    
    if request.args.get('validateur'):
        query = query.filter_by(validateur_id=int(request.args.get('validateur')))
    
    if request.args.get('priorite'):
        query = query.filter_by(priorite=int(request.args.get('priorite')))
    
    if request.args.get('expiration'):
        exp_filter = request.args.get('expiration')
        now = datetime.utcnow()
        
        if exp_filter == 'expire':
            query = query.filter(ValidationRapport.date_expiration < now)
        elif exp_filter == 'bientot_expire':
            dans_24h = now + timedelta(hours=24)
            query = query.filter(
                and_(
                    ValidationRapport.date_expiration > now,
                    ValidationRapport.date_expiration < dans_24h
                )
            )
        elif exp_filter == 'en_cours':
            query = query.filter(ValidationRapport.date_expiration > now)
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    validations = query.order_by(ValidationRapport.date_soumission.desc())\
                      .paginate(page=page, per_page=20, error_out=False)
    
    return render_template('workflow/liste.html',
                         form=form,
                         validations=validations)


@bp.route('/en-attente')
@login_required
def validations_en_attente():
    """Validations en attente pour l'utilisateur connecté"""
    validations = ValidationRapport.get_validations_en_attente(
        current_user.id if not current_user.is_admin() else None
    )
    
    return render_template('workflow/en_attente.html', validations=validations)


@bp.route('/relancer/<int:validation_id>', methods=['POST'])
@login_required
def relancer_validation(validation_id):
    """Envoyer une relance pour une validation"""
    validation = ValidationRapport.query.get_or_404(validation_id)
    
    if not current_user.is_admin():
        flash('Action non autorisée.', 'error')
        return redirect(url_for('workflow.index'))
    
    try:
        # Incrémenter le compteur de relances
        validation.rappels_envoyes += 1
        validation.save()
        
        # Ajouter à l'historique
        HistoriqueValidation.ajouter_action(
            rapport_id=validation.rapport_id,
            action=TypeAction.RELANCE,
            utilisateur_id=current_user.id,
            details=f"Relance #{validation.rappels_envoyes} envoyée",
            validation_id=validation.id
        )
        
        # TODO: Envoyer la notification de relance
        
        flash('Relance envoyée avec succès.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de l\'envoi de la relance: {str(e)}', 'error')
    
    return redirect(url_for('workflow.detail_validation', id=validation_id))


# Routes d'administration

@bp.route('/admin')
@login_required
@admin_required
def admin_index():
    """Tableau de bord administrateur du workflow"""
    # Statistiques globales
    stats = {
        'total_validations': ValidationRapport.query.count(),
        'en_attente': ValidationRapport.query.filter(
            ValidationRapport.statut.in_([StatutWorkflow.SOUMIS, StatutWorkflow.EN_VALIDATION])
        ).count(),
        'expirees': len(ValidationRapport.get_validations_expirees()),
        'workflows_configures': Workflow.query.count()
    }
    
    # Validations par statut
    validations_par_statut = {}
    for statut in StatutWorkflow:
        validations_par_statut[statut.value] = ValidationRapport.query.filter_by(statut=statut).count()
    
    # Validations par type
    validations_par_type = {}
    for type_rapport in TypeRapport:
        validations_par_type[type_rapport.value] = ValidationRapport.query.filter_by(type_rapport=type_rapport).count()
    
    return render_template('workflow/admin/index.html',
                         stats=stats,
                         validations_par_statut=validations_par_statut,
                         validations_par_type=validations_par_type)


@bp.route('/admin/workflows')
@login_required
@admin_required
def admin_workflows():
    """Gestion des workflows"""
    workflows = Workflow.query.all()
    return render_template('workflow/admin/workflows.html', workflows=workflows)


@bp.route('/admin/workflow/nouveau', methods=['GET', 'POST'])
@login_required
@admin_required
def nouveau_workflow():
    """Créer un nouveau workflow"""
    form = ConfigurationWorkflowForm()
    
    if form.validate_on_submit():
        try:
            workflow = Workflow(
                type_rapport=TypeRapport(form.type_rapport.data),
                nom=form.nom.data,
                description=form.description.data,
                delai_validation=form.delai_validation.data,
                validateurs_requis=form.validateurs_requis.data,
                rappel_automatique=form.rappel_automatique.data
            )
            workflow.save()
            
            flash('Workflow créé avec succès.', 'success')
            return redirect(url_for('workflow.admin_workflows'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la création: {str(e)}', 'error')
    
    return render_template('workflow/admin/nouveau_workflow.html', form=form)


@bp.route('/admin/validateurs')
@login_required
@admin_required
def admin_validateurs():
    """Gestion des validateurs désignés"""
    validateurs = ValidateurDesigne.query.filter_by(actif=True).all()
    return render_template('workflow/admin/validateurs.html', validateurs=validateurs)


@bp.route('/admin/validateur/nouveau', methods=['GET', 'POST'])
@login_required
@admin_required
def nouveau_validateur():
    """Désigner un nouveau validateur"""
    form = ValidateurDesigneForm()
    
    # Remplir les choix
    operateurs = Operateur.query.filter_by(actif=True).all()
    form.operateur_id.choices = [(o.id, o.nom) for o in operateurs]
    
    validateurs = User.query.filter_by(actif=True).all()
    form.validateur_id.choices = [(u.id, u.nom_complet) for u in validateurs]
    
    if form.validate_on_submit():
        try:
            validateur = ValidateurDesigne(
                operateur_id=form.operateur_id.data,
                validateur_id=form.validateur_id.data,
                type_rapport=TypeRapport(form.type_rapport.data),
                niveau_validation=form.niveau_validation.data,
                peut_valider_urgent=form.peut_valider_urgent.data,
                delai_max_validation=form.delai_max_validation.data
            )
            validateur.save()
            
            flash('Validateur désigné avec succès.', 'success')
            return redirect(url_for('workflow.admin_validateurs'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la désignation: {str(e)}', 'error')
    
    return render_template('workflow/admin/nouveau_validateur.html', form=form)


# API Routes

@bp.route('/api/validation/<int:id>')
@login_required
def api_validation_detail(id):
    """API pour récupérer les détails d'une validation"""
    validation = ValidationRapport.query.get_or_404(id)
    
    # Vérifier les permissions
    if not (current_user.is_admin() or validation.validateur_id == current_user.id):
        return jsonify({'error': 'Accès non autorisé'}), 403
    
    return jsonify(validation.to_dict())


@bp.route('/api/validations/en-attente')
@login_required
def api_validations_en_attente():
    """API pour récupérer les validations en attente"""
    validations = ValidationRapport.get_validations_en_attente(
        current_user.id if not current_user.is_admin() else None
    )
    
    return jsonify([v.to_dict() for v in validations])


@bp.route('/api/historique/<int:rapport_id>')
@login_required
def api_historique_rapport(rapport_id):
    """API pour récupérer l'historique d'un rapport"""
    historique = HistoriqueValidation.get_historique_rapport(rapport_id)
    return jsonify([h.to_dict() for h in historique])


@bp.route('/api/statistiques')
@login_required
@admin_required
def api_statistiques():
    """API pour les statistiques du workflow"""
    # Statistiques par période
    from datetime import datetime, timedelta
    
    maintenant = datetime.utcnow()
    il_y_a_30j = maintenant - timedelta(days=30)
    
    stats = {
        'validations_30j': ValidationRapport.query.filter(
            ValidationRapport.date_creation >= il_y_a_30j
        ).count(),
        'validees_30j': ValidationRapport.query.filter(
            ValidationRapport.date_validation >= il_y_a_30j,
            ValidationRapport.statut == StatutWorkflow.VALIDE
        ).count(),
        'delai_moyen': 0,  # TODO: Calculer le délai moyen de validation
        'taux_validation': 0  # TODO: Calculer le taux de validation
    }
    
    return jsonify(stats)