"""
Routes pour le module Distribution
Gestion des réseaux de distribution, postes et feeders
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
import json

from app.extensions import db
from app.models.distribution import (
    ReseauDistribution, PosteDistribution, TransformateurDistribution, 
    FeederDistribution, RapportDistribution
)
from app.models.operateurs import Operateur
from app.distribution.forms import (
    ReseauDistributionForm, PosteDistributionForm, TransformateurDistributionForm,
    FeederDistributionForm, RapportDistributionForm, FiltreDistributionForm
)
from app.utils.decorators import admin_required, role_required
from app.utils.permissions import (
    get_accessible_operateurs, can_access_operateur, 
    filter_query_by_operateur, get_default_operateur_id,
    can_access_poste, can_access_reseau, can_access_feeder
)

bp = Blueprint('distribution', __name__, url_prefix='/distribution')

# Remplacer par les utilitaires de permissions
verifier_permission_operateur = can_access_operateur

@bp.route('/')
@login_required
def index():
    """Page d'accueil du module distribution"""
    
    # Filtres
    operateur_id = request.args.get('operateur_id', type=int)
    zone = request.args.get('zone')
    statut = request.args.get('statut')
    
    # Requête de base selon les permissions
    operateurs = get_accessible_operateurs()
    
    if current_user.is_admin():
        query_reseaux = ReseauDistribution.query
        # Les postes et feeders n'ont pas d'operateur_id direct, ils sont liés via le réseau
        query_postes = PosteDistribution.query
        query_feeders = FeederDistribution.query
    else:
        query_reseaux = ReseauDistribution.query.filter_by(operateur_id=current_user.operateur_id)
        # Pour les postes et feeders, filtrer via le réseau
        query_postes = PosteDistribution.query.join(ReseauDistribution).filter(
            ReseauDistribution.operateur_id == current_user.operateur_id
        )
        query_feeders = FeederDistribution.query.join(PosteDistribution).join(ReseauDistribution).filter(
            ReseauDistribution.operateur_id == current_user.operateur_id
        )
    
    # Application des filtres
    if operateur_id:
        query_reseaux = query_reseaux.filter_by(operateur_id=operateur_id)
        query_postes = query_postes.join(ReseauDistribution).filter(
            ReseauDistribution.operateur_id == operateur_id
        )
        query_feeders = query_feeders.join(PosteDistribution).join(ReseauDistribution).filter(
            ReseauDistribution.operateur_id == operateur_id
        )
    
    if zone:
        query_reseaux = query_reseaux.filter_by(zone_desserte=zone)
        query_postes = query_postes.filter_by(zone_desserte=zone)
    
    if statut:
        query_reseaux = query_reseaux.filter_by(statut=statut)
        query_postes = query_postes.filter_by(statut=statut)
        query_feeders = query_feeders.filter(FeederDistribution.statut == statut)
    
    # Récupération des données
    reseaux = query_reseaux.filter_by(actif=True).all()
    postes = query_postes.filter_by(actif=True).all()
    feeders = query_feeders.filter(FeederDistribution.actif == True).all()
    
    # Statistiques globales
    stats = calculer_statistiques_distribution(reseaux, postes, feeders)
    
    # Données pour les graphiques
    donnees_graphiques = generer_donnees_graphiques_distribution(reseaux, postes, feeders)
    
    # Zones géographiques pour les filtres
    zones = db.session.query(ReseauDistribution.zone_desserte.distinct()).filter(
        ReseauDistribution.actif == True
    ).all()
    zones = [zone[0] for zone in zones if zone[0]]
    
    # Créer le formulaire de filtre
    filtre_form = FiltreDistributionForm()
    # Remplir les choix d'opérateurs
    filtre_form.operateur.choices = [('', 'Tous les opérateurs')] + [
        (str(op.id), op.nom) for op in operateurs
    ]
    
    return render_template('distribution/index.html',
                         reseaux=reseaux,
                         postes=postes,
                         feeders=feeders,
                         operateurs=operateurs,
                         zones=zones,
                         stats=stats,
                         donnees_graphiques=donnees_graphiques,
                         filtre_form=filtre_form,
                         filtres=request.args)

@bp.route('/reseaux')
@login_required
def liste_reseaux():
    """Liste des réseaux de distribution"""
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)
    
    # Formulaire de filtre
    filtre_form = FiltreDistributionForm(request.args)
    
    # Requête de base
    if current_user.is_admin():
        query = ReseauDistribution.query
        operateurs = Operateur.query.filter_by(actif=True, type_operateur='Distribution').all()
    else:
        query = ReseauDistribution.query.filter_by(operateur_id=current_user.operateur_id)
        operateurs = [current_user.operateur] if current_user.operateur else []
    
    # Filtres
    operateur_id = request.args.get('operateur_id', type=int)
    if operateur_id:
        query = query.filter_by(operateur_id=operateur_id)
    
    zone = request.args.get('zone')
    if zone:
        query = query.filter_by(zone_desserte=zone)
    
    type_reseau = request.args.get('type_reseau')
    if type_reseau:
        query = query.filter_by(type_reseau=type_reseau)
    
    # Tri
    sort_by = request.args.get('sort', 'nom')
    sort_order = request.args.get('order', 'asc')
    
    if hasattr(ReseauDistribution, sort_by):
        column = getattr(ReseauDistribution, sort_by)
        if sort_order == 'desc':
            query = query.order_by(column.desc())
        else:
            query = query.order_by(column.asc())
    
    # Pagination
    reseaux_paginated = query.filter_by(actif=True).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('distribution/reseaux/liste.html',
                         reseaux=reseaux_paginated,
                         operateurs=operateurs,
                         filtre_form=filtre_form)

@bp.route('/reseaux/nouveau', methods=['GET', 'POST'])
@login_required
def nouveau_reseau():
    """Créer un nouveau réseau de distribution"""
    
    # Vérifier les permissions
    if not current_user.is_admin() and not current_user.operateur_id:
        flash('Vous n\'avez pas l\'autorisation de créer un réseau de distribution.', 'error')
        return redirect(url_for('distribution.index'))
    
    form = ReseauDistributionForm()
    # Les choix d'opérateurs sont configurés automatiquement dans le constructeur du formulaire
    
    if form.validate_on_submit():
        try:
            reseau = ReseauDistribution()
            form.populate_obj(reseau)
            reseau.save()
            
            flash(f'Réseau de distribution "{reseau.nom}" créé avec succès.', 'success')
            return redirect(url_for('distribution.detail_reseau', id=reseau.id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la création du réseau : {str(e)}', 'error')
    
    return render_template('distribution/reseaux/formulaire.html', form=form, mode='creation')

@bp.route('/reseaux/<int:id>')
@login_required
def detail_reseau(id):
    """Détail d'un réseau de distribution"""
    
    reseau = ReseauDistribution.query.get_or_404(id)
    
    if not verifier_permission_operateur(reseau.operateur_id):
        abort(403)
    
    # Postes du réseau
    postes = PosteDistribution.query.filter_by(
        reseau_id=reseau.id,
        actif=True
    ).all()
    
    # Statistiques du réseau
    stats_reseau = {
        'nombre_postes': len(postes),
        'nombre_clients': sum([p.nombre_clients_raccordes for p in postes if p.nombre_clients_raccordes]),
        'puissance_totale': sum([p.puissance_installee for p in postes if p.puissance_installee]),
        'longueur_lignes': reseau.longueur_reseau_mt or 0  # Utiliser le champ du réseau
    }
    
    # Données pour les graphiques
    donnees_performance = generer_donnees_performance_reseau(reseau)
    
    return render_template('distribution/reseaux/detail.html',
                         reseau=reseau,
                         postes=postes,
                         stats_reseau=stats_reseau,
                         donnees_performance=donnees_performance)

@bp.route('/reseaux/<int:id>/modifier', methods=['GET', 'POST'])
@login_required
def modifier_reseau(id):
    """Modifier un réseau de distribution"""
    
    reseau = ReseauDistribution.query.get_or_404(id)
    
    if not verifier_permission_operateur(reseau.operateur_id):
        abort(403)
    
    form = ReseauDistributionForm(obj=reseau)
    
    # Configuration des choix selon les permissions
    if current_user.is_admin():
        form.operateur_id.choices = [
            (op.id, op.nom) for op in 
            Operateur.query.filter_by(actif=True, type_operateur='Distribution').all()
        ]
    else:
        form.operateur_id.choices = [(reseau.operateur_id, reseau.operateur.nom)]
    
    if form.validate_on_submit():
        try:
            form.populate_obj(reseau)
            reseau.update()
            
            flash(f'Réseau de distribution "{reseau.nom}" modifié avec succès.', 'success')
            return redirect(url_for('distribution.detail_reseau', id=reseau.id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la modification : {str(e)}', 'error')
    
    return render_template('distribution/reseaux/formulaire.html',
                         form=form, reseau=reseau, mode='modification')

@bp.route('/reseaux/<int:id>/supprimer', methods=['POST'])
@login_required
@role_required('admin_operateur', 'super_admin')
def supprimer_reseau(id):
    """Supprimer un réseau de distribution"""
    from app.models.distribution import ReseauDistribution
    
    reseau = ReseauDistribution.query.get_or_404(id)
    
    # Vérifier les permissions
    if not can_access_operateur(reseau.operateur_id):
        abort(403)
    
    try:
        # Vérifier s'il y a des postes associés
        if reseau.postes and len(reseau.postes) > 0:
            flash('Impossible de supprimer le réseau : des postes y sont encore associés.', 'error')
            return redirect(url_for('distribution.detail_reseau', id=id))
        
        # Soft delete
        reseau.soft_delete()
        flash(f'Réseau "{reseau.nom}" supprimé avec succès.', 'success')
        return redirect(url_for('distribution.liste_reseaux'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression : {str(e)}', 'error')
        return redirect(url_for('distribution.detail_reseau', id=id))

@bp.route('/postes')
@login_required
def liste_postes():
    """Liste des postes de distribution"""
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)
    
    # Requête de base
    if current_user.is_admin():
        query = PosteDistribution.query
    else:
        # Filtrer via le réseau auquel appartient le poste
        query = PosteDistribution.query.join(ReseauDistribution).filter(
            ReseauDistribution.operateur_id == current_user.operateur_id
        )
    
    # Filtres
    reseau_id = request.args.get('reseau_id', type=int)
    if reseau_id:
        query = query.filter_by(reseau_id=reseau_id)
    
    type_poste = request.args.get('type_poste')
    if type_poste:
        query = query.filter_by(type_poste=type_poste)
    
    statut = request.args.get('statut')
    if statut:
        query = query.filter_by(statut=statut)
    
    # Pagination
    postes_paginated = query.filter_by(actif=True).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Réseaux pour le filtre
    if current_user.is_admin():
        reseaux = ReseauDistribution.query.filter_by(actif=True).all()
    else:
        reseaux = ReseauDistribution.query.filter_by(
            operateur_id=current_user.operateur_id,
            actif=True
        ).all()
    
    return render_template('distribution/postes/liste.html',
                         postes=postes_paginated,
                         reseaux=reseaux)

@bp.route('/postes/nouveau', methods=['GET', 'POST'])
@login_required
def nouveau_poste():
    """Créer un nouveau poste de distribution"""
    
    form = PosteDistributionForm()
    
    if form.validate_on_submit():
        try:
            # Vérifier que l'utilisateur peut accéder au réseau sélectionné
            reseau = ReseauDistribution.query.get_or_404(form.reseau_id.data)
            if not current_user.is_admin() and reseau.operateur_id != current_user.operateur_id:
                flash('Vous n\'avez pas l\'autorisation d\'ajouter un poste à ce réseau.', 'error')
                return redirect(url_for('distribution.liste_postes'))
            
            poste = PosteDistribution()
            form.populate_obj(poste)
            
            if poste.reseau_id == 0:
                poste.reseau_id = None
            
            poste.save()
            
            flash(f'Poste de distribution "{poste.nom}" créé avec succès.', 'success')
            return redirect(url_for('distribution.detail_poste', id=poste.id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la création du poste : {str(e)}', 'error')
    
    return render_template('distribution/postes/formulaire.html', form=form, mode='creation')

@bp.route('/postes/<int:id>')
@login_required
def detail_poste(id):
    """Détail d'un poste de distribution"""
    
    poste = PosteDistribution.query.get_or_404(id)
    
    if not verifier_permission_operateur(poste.reseau.operateur_id):
        abort(403)
    
    # Feeders du poste
    feeders = FeederDistribution.query.filter_by(
        poste_source_id=poste.id,
        actif=True
    ).all()
    
    # Transformateurs du poste
    transformateurs = TransformateurDistribution.query.filter_by(
        poste_distribution_id=poste.id,
        actif=True
    ).all()
    
    # Statistiques du poste
    stats_poste = {
        'nombre_feeders': len(feeders),
        'nombre_transformateurs': len(transformateurs),
        'clients_total': sum([f.nombre_clients for f in feeders if f.nombre_clients]),
        'charge_totale': sum([f.charge_actuelle for f in feeders if f.charge_actuelle])
    }
    
    # Données pour les graphiques
    donnees_charge = generer_donnees_charge_poste_distribution(poste, feeders)
    
    return render_template('distribution/postes/detail.html',
                         poste=poste,
                         feeders=feeders,
                         transformateurs=transformateurs,
                         stats_poste=stats_poste,
                         donnees_charge=donnees_charge)

@bp.route('/feeders')
@login_required
def liste_feeders():
    """Liste des feeders de distribution"""
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)
    
    # Requête de base
    if current_user.is_admin():
        query = FeederDistribution.query.join(PosteDistribution)
    else:
        query = FeederDistribution.query.join(PosteDistribution).join(ReseauDistribution).filter(
            ReseauDistribution.operateur_id == current_user.operateur_id
        )
    
    # Filtres
    poste_id = request.args.get('poste_id', type=int)
    if poste_id:
        query = query.filter_by(poste_source_id=poste_id)
    
    type_alimentation = request.args.get('type_alimentation')
    if type_alimentation:
        query = query.filter(FeederDistribution.type_alimentation == type_alimentation)
    
    statut = request.args.get('statut')
    if statut:
        query = query.filter(FeederDistribution.statut == statut)
    
    # Pagination
    feeders_paginated = query.filter(
        FeederDistribution.actif == True
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    # Postes pour le filtre
    if current_user.is_admin():
        postes = PosteDistribution.query.filter_by(actif=True).all()
    else:
        postes = PosteDistribution.query.join(ReseauDistribution).filter(
            ReseauDistribution.operateur_id == current_user.operateur_id,
            PosteDistribution.actif == True
        ).all()
    
    return render_template('distribution/feeders/liste.html',
                         feeders=feeders_paginated,
                         postes=postes)

@bp.route('/feeders/nouveau', methods=['GET', 'POST'])
@login_required
def nouveau_feeder():
    """Créer un nouveau feeder"""
    
    form = FeederDistributionForm()
    
    # Configuration des choix de postes selon les permissions
    if current_user.is_admin():
        postes = PosteDistribution.query.filter_by(actif=True).all()
    else:
        postes = PosteDistribution.query.join(ReseauDistribution).filter(
            ReseauDistribution.operateur_id == current_user.operateur_id,
            PosteDistribution.actif == True
        ).all()
    
    form.poste_source_id.choices = [(p.id, f"{p.nom} - {p.reseau.operateur.nom}") for p in postes]
    
    if not postes:
        flash('Aucun poste disponible. Créez d\'abord un poste de distribution.', 'error')
        return redirect(url_for('distribution.liste_postes'))
    
    if form.validate_on_submit():
        try:
            # Vérifier les permissions sur le poste sélectionné (si spécifié)
            if form.poste_source_id.data:
                poste_selectionne = PosteDistribution.query.get(form.poste_source_id.data)
                if not can_access_poste(poste_selectionne):
                    flash('Vous n\'avez pas l\'autorisation d\'ajouter un feeder à ce poste.', 'error')
                    return render_template('distribution/feeders/formulaire.html', 
                                         form=form, mode='creation')
            
            feeder = FeederDistribution()
            form.populate_obj(feeder)
            feeder.save()
            
            flash(f'Feeder "{feeder.nom}" créé avec succès.', 'success')
            return redirect(url_for('distribution.detail_feeder', id=feeder.id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la création du feeder : {str(e)}', 'error')
    
    return render_template('distribution/feeders/formulaire.html', form=form, mode='creation')

@bp.route('/feeders/<int:id>')
@login_required
def detail_feeder(id):
    """Détail d'un feeder de distribution"""
    
    feeder = FeederDistribution.query.get_or_404(id)
    
    if not verifier_permission_operateur(feeder.reseau.operateur_id):
        abort(403)
    
    # Données de performance du feeder
    donnees_performance = generer_donnees_performance_feeder(feeder)
    
    # Historique des rapports du réseau
    rapports_reseau = RapportDistribution.query.filter_by(
        reseau_id=feeder.reseau_id,
        actif=True
    ).order_by(RapportDistribution.periode_debut.desc()).limit(10).all()
    
    return render_template('distribution/feeders/detail.html',
                         feeder=feeder,
                         donnees_performance=donnees_performance,
                         rapports_reseau=rapports_reseau)

@bp.route('/feeders/<int:id>/modifier', methods=['GET', 'POST'])
@login_required
def modifier_feeder(id):
    """Modifier un feeder de distribution"""
    
    feeder = FeederDistribution.query.get_or_404(id)
    
    if not verifier_permission_operateur(feeder.reseau.operateur_id):
        abort(403)
    
    form = FeederDistributionForm(obj=feeder)
    form.feeder_id = feeder.id
    
    # Configuration des choix selon les permissions
    accessible_operateurs = get_accessible_operateurs()
    reseaux = ReseauDistribution.query.filter(
        ReseauDistribution.operateur_id.in_([op.id for op in accessible_operateurs]),
        ReseauDistribution.actif == True
    ).all()
    
    form.reseau_id.choices = [(r.id, f"{r.nom} - {r.operateur.nom}") for r in reseaux]
    
    # Postes source pour le réseau sélectionné
    if feeder.reseau_id:
        postes = PosteDistribution.query.filter_by(
            reseau_id=feeder.reseau_id,
            actif=True
        ).all()
        form.poste_source_id.choices = [('', 'Aucun')] + [(p.id, p.nom) for p in postes]
    else:
        form.poste_source_id.choices = [('', 'Aucun')]
    
    if form.validate_on_submit():
        try:
            form.populate_obj(feeder)
            feeder.update()
            
            flash('Feeder modifié avec succès!', 'success')
            return redirect(url_for('distribution.detail_feeder', id=feeder.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la modification : {str(e)}', 'error')
    
    return render_template('distribution/feeders/modifier.html',
                         form=form,
                         feeder=feeder,
                         title="Modifier Feeder")

@bp.route('/feeders/<int:id>/supprimer', methods=['POST'])
@login_required
def supprimer_feeder(id):
    """Supprimer un feeder de distribution"""
    
    feeder = FeederDistribution.query.get_or_404(id)
    
    if not verifier_permission_operateur(feeder.reseau.operateur_id):
        abort(403)
    
    try:
        # Suppression soft
        feeder.soft_delete()
        
        flash('Feeder supprimé avec succès!', 'success')
        return redirect(url_for('distribution.liste_feeders'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression : {str(e)}', 'error')
        return redirect(url_for('distribution.detail_feeder', id=id))

@bp.route('/rapports')
@login_required
def liste_rapports():
    """Liste des rapports de distribution"""
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)
    
    # Requête de base selon les permissions
    if current_user.is_admin():
        query = RapportDistribution.query.join(PosteDistribution)
    else:
        query = RapportDistribution.query.join(PosteDistribution).join(ReseauDistribution).filter(
            ReseauDistribution.operateur_id == current_user.operateur_id
        )
    
    # Filtres par date
    date_debut = request.args.get('date_debut')
    date_fin = request.args.get('date_fin')
    
    if date_debut:
        try:
            date_debut = datetime.strptime(date_debut, '%Y-%m-%d').date()
            query = query.filter(RapportDistribution.periode_debut >= date_debut)
        except ValueError:
            flash('Format de date de début invalide.', 'error')
    
    if date_fin:
        try:
            date_fin = datetime.strptime(date_fin, '%Y-%m-%d').date()
            query = query.filter(RapportDistribution.periode_fin <= date_fin)
        except ValueError:
            flash('Format de date de fin invalide.', 'error')
    
    # Type de rapport
    type_rapport = request.args.get('type_rapport')
    if type_rapport:
        query = query.filter_by(type_rapport=type_rapport)
    
    # Pagination
    rapports_paginated = query.filter_by(actif=True).order_by(
        RapportDistribution.periode_debut.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('distribution/rapports/liste.html',
                         rapports=rapports_paginated)

# API Routes
@bp.route('/api/statistiques')
@login_required
def api_statistiques():
    """API pour récupérer les statistiques de distribution"""
    
    # Période (défaut: 30 derniers jours)
    periode = request.args.get('periode', '30j')
    
    if periode == '7j':
        date_debut = datetime.now() - timedelta(days=7)
    elif periode == '30j':
        date_debut = datetime.now() - timedelta(days=30)
    elif periode == '1an':
        date_debut = datetime.now() - timedelta(days=365)
    else:
        date_debut = datetime.now() - timedelta(days=30)
    
    # Statistiques selon les permissions
    if current_user.is_admin():
        total_reseaux = ReseauDistribution.query.filter_by(actif=True).count()
        total_postes = PosteDistribution.query.filter_by(actif=True).count()
        total_feeders = FeederDistribution.query.filter_by(actif=True).count()
        
        # Nombre total de clients
        total_clients = db.session.query(func.sum(PosteDistribution.nombre_clients_raccordes)).scalar() or 0
        
    else:
        total_reseaux = ReseauDistribution.query.filter_by(
            operateur_id=current_user.operateur_id,
            actif=True
        ).count()
        total_postes = PosteDistribution.query.join(ReseauDistribution).filter(
            ReseauDistribution.operateur_id == current_user.operateur_id,
            PosteDistribution.actif == True
        ).count()
        total_feeders = FeederDistribution.query.join(PosteDistribution).join(ReseauDistribution).filter(
            ReseauDistribution.operateur_id == current_user.operateur_id,
            FeederDistribution.actif == True
        ).count()
        
        # Nombre de clients pour cet opérateur (via les réseaux)
        total_clients = db.session.query(func.sum(ReseauDistribution.nombre_clients_total)).filter_by(
            operateur_id=current_user.operateur_id
        ).scalar() or 0
    
    # Indicateurs de qualité
    rapports_periode = RapportDistribution.query.filter(
        RapportDistribution.periode_debut >= date_debut.date(),
        RapportDistribution.actif == True
    )
    
    if not current_user.is_admin():
        rapports_periode = rapports_periode.join(PosteDistribution).join(ReseauDistribution).filter(
            ReseauDistribution.operateur_id == current_user.operateur_id
        )
    
    rapports = rapports_periode.all()
    
    if rapports:
        saidi_moyen = sum([r.saidi_realise for r in rapports if r.saidi_realise]) / len(rapports)
        saifi_moyen = sum([r.saifi_realise for r in rapports if r.saifi_realise]) / len(rapports)
        disponibilite_moyenne = sum([r.taux_disponibilite for r in rapports if r.taux_disponibilite]) / len(rapports)
    else:
        saidi_moyen = 0
        saifi_moyen = 0
        disponibilite_moyenne = 0
    
    return jsonify({
        'total_reseaux': total_reseaux,
        'total_postes': total_postes,
        'total_feeders': total_feeders,
        'total_clients': total_clients,
        'saidi_moyen': round(saidi_moyen, 2),
        'saifi_moyen': round(saifi_moyen, 2),
        'disponibilite_moyenne': round(disponibilite_moyenne, 2),
        'periode': periode
    })

# Fonctions utilitaires
def calculer_statistiques_distribution(reseaux, postes, feeders):
    """Calculer les statistiques globales de distribution à partir des données mensuelles réelles"""
    
    from app.models.distribution import DonneesDistributionMensuelles
    from datetime import datetime
    from sqlalchemy import func
    from flask_login import current_user
    
    # Statistiques de base sur l'infrastructure
    stats = {
        'total_reseaux': len(reseaux),
        'nb_reseaux': len(reseaux),  # Alias pour compatibilité
        'nb_feeders': len(feeders),
        'puissance_totale': sum([p.puissance_installee for p in postes if p.puissance_installee]),
        'longueur_lignes_mt': sum([r.longueur_reseau_mt for r in reseaux if r.longueur_reseau_mt]),
        'longueur_lignes_bt': sum([r.longueur_reseau_bt for r in reseaux if r.longueur_reseau_bt]),
        'postes_en_service': len([p for p in postes if p.statut == 'en_service']),
        'feeders_en_service': len([f for f in feeders if f.statut == 'en_service'])
    }
    
    # Calculer les statistiques opérationnelles à partir des données mensuelles
    annee_courante = datetime.now().year
    
    if current_user.is_admin():
        # Super admin voit toutes les données
        base_query = DonneesDistributionMensuelles.query
    else:
        # Opérateur ne voit que ses données
        if current_user.operateur:
            base_query = DonneesDistributionMensuelles.query.filter_by(
                operateur_id=current_user.operateur.id
            )
        else:
            base_query = DonneesDistributionMensuelles.query.filter(False)  # Aucune donnée
    
    # Données de l'année courante
    donnees_annee = base_query.filter_by(annee=annee_courante).all()
    
    if donnees_annee:
        # Dernière saisie pour avoir le nombre de clients le plus récent
        derniere_saisie = base_query.filter_by(annee=annee_courante).order_by(
            DonneesDistributionMensuelles.mois.desc()
        ).first()
        
        if derniere_saisie:
            stats['nb_clients'] = (
                (derniere_saisie.clients_ht_fin_mois or 0) +
                (derniere_saisie.clients_mt_fin_mois or 0) +
                (derniere_saisie.clients_bt_fin_mois or 0)
            )
        else:
            stats['nb_clients'] = 0
        
        # Énergie distribuée totale sur l'année (en GWh)
        energie_totale_mwh = sum([
            (donnee.energie_distribuee_ht_mwh or 0) +
            (donnee.energie_distribuee_mt_mwh or 0) +
            (donnee.energie_distribuee_bt_mwh or 0)
            for donnee in donnees_annee
        ])
        stats['energie_distribuee'] = round(energie_totale_mwh / 1000, 2)  # Conversion MWh -> GWh
        
        # Revenus totaux sur l'année (USD)
        stats['revenus_totaux'] = sum([
            (donnee.revenus_ht_usd or 0) +
            (donnee.revenus_mt_usd or 0) +
            (donnee.revenus_bt_usd or 0)
            for donnee in donnees_annee
        ])
        
        # Taux de recouvrement moyen (revenus - impayés)
        revenus_total = sum([
            (donnee.revenus_ht_usd or 0) +
            (donnee.revenus_mt_usd or 0) +
            (donnee.revenus_bt_usd or 0)
            for donnee in donnees_annee
        ])
        
        impayes_total = sum([
            (donnee.impayes_usd or 0)
            for donnee in donnees_annee
        ])
        
        if revenus_total > 0:
            stats['taux_recouvrement'] = round(((revenus_total - impayes_total) / revenus_total) * 100, 1)
        else:
            stats['taux_recouvrement'] = 0
        
        # Taux de pertes moyen
        energie_totale = sum([
            (donnee.energie_distribuee_ht_mwh or 0) +
            (donnee.energie_distribuee_mt_mwh or 0) +
            (donnee.energie_distribuee_bt_mwh or 0)
            for donnee in donnees_annee
        ])
        
        pertes_totales = sum([
            (donnee.pertes_techniques_mwh or 0) +
            (donnee.pertes_commerciales_mwh or 0)
            for donnee in donnees_annee
        ])
        
        if energie_totale > 0:
            stats['taux_pertes'] = round((pertes_totales / energie_totale) * 100, 1)
        else:
            stats['taux_pertes'] = 0
        
    else:
        # Pas de données mensuelles, utiliser des valeurs par défaut
        stats.update({
            'nb_clients': 0,
            'energie_distribuee': 0.0,
            'revenus_totaux': 0,
            'taux_recouvrement': 0,
            'taux_pertes': 0
        })
    
    # Calcul du taux de desserte (basé sur l'infrastructure)
    clients_infrastructure = sum([p.nombre_clients_raccordes for p in postes if p.nombre_clients_raccordes])
    
    if clients_infrastructure > 0:
        clients_alimentes = sum([p.nombre_clients_raccordes for p in postes 
                               if p.statut == 'en_service' and p.nombre_clients_raccordes])
        stats['taux_desserte'] = round((clients_alimentes / clients_infrastructure) * 100, 2)
    else:
        stats['taux_desserte'] = 0
    
    return stats

def generer_donnees_graphiques_distribution(reseaux, postes, feeders):
    """Générer les données pour les graphiques du dashboard distribution"""
    
    donnees = {
        'repartition_zones': {},
        'types_reseaux': {},
        'statuts_postes': {},
        'repartition_clients': {},
        'types_alimentation_feeders': {}
    }
    
    # Répartition par zones géographiques
    for reseau in reseaux:
        zone = reseau.zone_desserte or 'Non définie'
        donnees['repartition_zones'][zone] = donnees['repartition_zones'].get(zone, 0) + 1
    
    # Types de réseaux
    for reseau in reseaux:
        type_reseau = reseau.type_reseau or 'Non défini'
        donnees['types_reseaux'][type_reseau] = donnees['types_reseaux'].get(type_reseau, 0) + 1
    
    # Statuts des postes
    for poste in postes:
        statut = poste.statut or 'Non défini'
        donnees['statuts_postes'][statut] = donnees['statuts_postes'].get(statut, 0) + 1
    
    # Répartition des clients par poste (top 10)
    postes_clients = [(p.nom, p.nombre_clients_raccordes) for p in postes if p.nombre_clients_raccordes]
    postes_clients.sort(key=lambda x: x[1], reverse=True)
    donnees['repartition_clients'] = dict(postes_clients[:10])
    
    # Types d'alimentation des feeders
    for feeder in feeders:
        type_alim = feeder.type_feeder or 'Non défini'
        donnees['types_alimentation_feeders'][type_alim] = donnees['types_alimentation_feeders'].get(type_alim, 0) + 1
    
    return donnees

def generer_donnees_performance_reseau(reseau):
    """Générer les données de performance pour un réseau"""
    
    # Récupérer les rapports des 12 derniers mois
    date_limite = datetime.now() - timedelta(days=365)
    
    # Récupérer les rapports directement par reseau_id
    rapports = RapportDistribution.query.filter(
        RapportDistribution.reseau_id == reseau.id,
        RapportDistribution.periode_debut >= date_limite.date(),
        RapportDistribution.actif == True
    ).order_by(RapportDistribution.periode_debut.asc()).all()
    
    donnees = {
        'labels': [],
        'disponibilite': [],
        'saidi': [],
        'saifi': []
    }
    
    # Grouper par mois
    rapports_par_mois = {}
    for rapport in rapports:
        mois = rapport.periode_debut.strftime('%m/%Y')
        if mois not in rapports_par_mois:
            rapports_par_mois[mois] = []
        rapports_par_mois[mois].append(rapport)
    
    # Calculer les moyennes mensuelles
    for mois in sorted(rapports_par_mois.keys()):
        rapports_mois = rapports_par_mois[mois]
        donnees['labels'].append(mois)
        
        # Moyennes des indicateurs
        disponibilite_moy = sum([r.taux_disponibilite for r in rapports_mois if r.taux_disponibilite]) / len(rapports_mois)
        saidi_moy = sum([r.saidi_realise for r in rapports_mois if r.saidi_realise]) / len(rapports_mois)
        saifi_moy = sum([r.saifi_realise for r in rapports_mois if r.saifi_realise]) / len(rapports_mois)
        
        donnees['disponibilite'].append(round(disponibilite_moy, 2))
        donnees['saidi'].append(round(saidi_moy, 2))
        donnees['saifi'].append(round(saifi_moy, 2))
    
    return donnees

def generer_donnees_charge_poste_distribution(poste, feeders):
    """Générer les données de charge pour un poste de distribution"""
    
    # Données simulées pour l'exemple - à remplacer par des vraies données
    from random import randint, choice
    
    donnees = {
        'labels': [f"H{h:02d}" for h in range(0, 24)],
        'charge_totale': [],
        'feeders': {}
    }
    
    # Charge totale du poste (simulation)
    charge_base = 60
    for h in range(24):
        if 6 <= h <= 10 or 17 <= h <= 22:  # Heures de pointe
            charge = randint(charge_base + 20, 95)
        elif 22 <= h <= 24 or 0 <= h <= 6:  # Heures creuses
            charge = randint(30, charge_base - 10)
        else:  # Heures normales
            charge = randint(charge_base - 10, charge_base + 10)
        
        donnees['charge_totale'].append(charge)
    
    # Charge par feeder (max 5 feeders pour la lisibilité)
    for i, feeder in enumerate(feeders[:5]):
        donnees['feeders'][feeder.nom] = []
        facteur = choice([0.6, 0.7, 0.8, 0.9, 1.0])  # Facteur aléatoire
        
        for charge_totale in donnees['charge_totale']:
            charge_feeder = int(charge_totale * facteur * randint(15, 35) / 100)
            donnees['feeders'][feeder.nom].append(charge_feeder)
    
    return donnees

def generer_donnees_performance_feeder(feeder):
    """Générer les données de performance pour un feeder"""
    
    # Données des 30 derniers jours
    from random import randint
    import datetime
    
    donnees = {
        'labels': [],
        'disponibilite': [],
        'nombre_pannes': [],
        'duree_pannes': []
    }
    
    # Générer les données pour les 30 derniers jours
    for i in range(30, 0, -1):
        date = datetime.date.today() - datetime.timedelta(days=i)
        donnees['labels'].append(date.strftime('%d/%m'))
        
        # Disponibilité (simulation: généralement haute)
        disponibilite = randint(95, 100) if randint(1, 10) > 2 else randint(70, 94)
        donnees['disponibilite'].append(disponibilite)
        
        # Nombre de pannes (rare)
        nb_pannes = 0 if randint(1, 10) > 3 else randint(1, 3)
        donnees['nombre_pannes'].append(nb_pannes)
        
        # Durée des pannes en minutes
        duree = 0 if nb_pannes == 0 else randint(30, 240)
        donnees['duree_pannes'].append(duree)
    
    return donnees


# Routes pour les transformateurs de distribution

@bp.route('/transformateurs')
@login_required
def liste_transformateurs():
    """Liste des transformateurs de distribution"""
    
    # Filtres
    operateur_id = request.args.get('operateur_id', type=int)
    poste_id = request.args.get('poste_id', type=int)
    page = request.args.get('page', 1, type=int)
    
    # Requête de base
    query = TransformateurDistribution.query
    
    # Filtrage par poste si spécifié
    if poste_id:
        poste = PosteDistribution.query.get_or_404(poste_id)
        # Vérifier les permissions d'accès au poste
        if not can_access_poste(poste.id):
            abort(403)
        query = query.filter_by(poste_distribution_id=poste_id)
    else:
        # Filtrage par permissions - accès via les postes
        accessible_operateurs = get_accessible_operateurs()
        if not current_user.is_admin():
            # Jointure avec PosteDistribution et ReseauDistribution pour filtrer
            query = query.join(PosteDistribution).join(ReseauDistribution).filter(
                ReseauDistribution.operateur_id.in_([op.id for op in accessible_operateurs])
            )
        elif operateur_id:
            query = query.join(PosteDistribution).join(ReseauDistribution).filter(
                ReseauDistribution.operateur_id == operateur_id
            )
    
    # Pagination
    transformateurs = query.order_by(TransformateurDistribution.nom).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Statistiques
    stats = {
        'total': query.count(),
        'en_service': query.filter_by(statut='en_service').count(),
        'hors_service': query.filter_by(statut='hors_service').count(),
        'maintenance': query.filter_by(statut='maintenance').count(),
        'puissance_totale': db.session.query(func.sum(TransformateurDistribution.puissance_nominale)).scalar() or 0
    }
    
    return render_template('distribution/transformateurs/liste.html',
                         transformateurs=transformateurs,
                         operateurs=get_accessible_operateurs(),
                         stats=stats,
                         title="Transformateurs de Distribution")


@bp.route('/transformateurs/nouveau', methods=['GET', 'POST'])
@login_required
def nouveau_transformateur():
    """Créer un nouveau transformateur"""
    
    # Récupérer le poste_id depuis les paramètres URL
    poste_id = request.args.get('poste_id', type=int)
    
    form = TransformateurDistributionForm()
    
    # Filtrer les postes selon les permissions
    accessible_operateurs = get_accessible_operateurs()
    if current_user.is_admin():
        postes_query = PosteDistribution.query.join(ReseauDistribution)
    else:
        postes_query = PosteDistribution.query.join(ReseauDistribution).filter(
            ReseauDistribution.operateur_id.in_([op.id for op in accessible_operateurs])
        )
    
    form.poste_distribution_id.choices = [
        (p.id, f"{p.nom} ({p.reseau.nom})")
        for p in postes_query.order_by(PosteDistribution.nom).all()
    ]
    
    # Pré-sélectionner le poste si fourni
    if poste_id and request.method == 'GET':
        poste = PosteDistribution.query.get_or_404(poste_id)
        if not can_access_poste(poste.id):
            abort(403)
        form.poste_distribution_id.data = poste_id
    
    if form.validate_on_submit():
        # Vérifier les permissions pour le poste sélectionné
        poste = PosteDistribution.query.get_or_404(form.poste_distribution_id.data)
        if not can_access_poste(poste.id):
            flash('Accès refusé pour ce poste', 'danger')
            return redirect(url_for('distribution.liste_transformateurs'))
        
        transformateur = TransformateurDistribution()
        form.populate_obj(transformateur)
        transformateur.save()
        
        flash(f'Transformateur "{transformateur.nom}" créé avec succès', 'success')
        
        # Rediriger vers les détails du poste si on vient de là
        if poste_id:
            return redirect(url_for('distribution.detail_poste', id=poste_id))
        else:
            return redirect(url_for('distribution.liste_transformateurs'))
    
    return render_template('distribution/transformateurs/nouveau.html',
                         form=form,
                         title="Nouveau Transformateur")


@bp.route('/transformateurs/<int:id>')
@login_required
def detail_transformateur(id):
    """Détail d'un transformateur"""
    
    transformateur = TransformateurDistribution.query.get_or_404(id)
    
    # Vérification des permissions via le poste
    if not can_access_poste(transformateur.poste_distribution.id):
        abort(403)
    
    # Statistiques et données de performance
    stats = {
        'puissance_installee': transformateur.puissance_nominale,
        'charge_actuelle': transformateur.puissance_nominale * 0.75,  # Simulation
        'taux_charge': 75,  # Simulation
        'temperature': 65,  # Simulation
        'derniere_maintenance': transformateur.date_installation,
        'prochaine_maintenance': transformateur.date_installation  # À calculer
    }
    
    from datetime import datetime
    
    return render_template('distribution/transformateurs/detail.html',
                         transformateur=transformateur,
                         stats=stats,
                         title=f"Transformateur {transformateur.nom}",
                         now=datetime.now())


@bp.route('/transformateurs/<int:id>/modifier', methods=['GET', 'POST'])
@login_required
def modifier_transformateur(id):
    """Modifier un transformateur"""
    
    transformateur = TransformateurDistribution.query.get_or_404(id)
    
    # Vérification des permissions
    if not can_access_poste(transformateur.poste_distribution.id):
        abort(403)
    
    form = TransformateurDistributionForm(obj=transformateur)
    
    # Filtrer les postes selon les permissions
    accessible_operateurs = get_accessible_operateurs()
    if current_user.is_admin():
        postes_query = PosteDistribution.query.join(ReseauDistribution)
    else:
        postes_query = PosteDistribution.query.join(ReseauDistribution).filter(
            ReseauDistribution.operateur_id.in_([op.id for op in accessible_operateurs])
        )
    
    form.poste_distribution_id.choices = [
        (p.id, f"{p.nom} ({p.reseau.nom})")
        for p in postes_query.order_by(PosteDistribution.nom).all()
    ]
    
    if form.validate_on_submit():
        # Vérifier les permissions pour le nouveau poste si changé
        if form.poste_distribution_id.data != transformateur.poste_distribution_id:
            nouveau_poste = PosteDistribution.query.get_or_404(form.poste_distribution_id.data)
            if not can_access_poste(nouveau_poste.id):
                flash('Accès refusé pour ce poste', 'danger')
                return redirect(url_for('distribution.detail_transformateur', id=id))
        
        form.populate_obj(transformateur)
        transformateur.update()
        
        flash(f'Transformateur "{transformateur.nom}" modifié avec succès', 'success')
        return redirect(url_for('distribution.detail_transformateur', id=id))
    
    return render_template('distribution/transformateurs/modifier.html',
                         form=form,
                         transformateur=transformateur,
                         title=f"Modifier {transformateur.nom}")


@bp.route('/transformateurs/<int:id>/supprimer', methods=['POST'])
@login_required
def supprimer_transformateur(id):
    """Supprimer un transformateur"""
    
    transformateur = TransformateurDistribution.query.get_or_404(id)
    
    # Vérification des permissions
    if not can_access_poste(transformateur.poste_distribution.id):
        abort(403)
    
    poste_id = transformateur.poste_distribution_id
    nom = transformateur.nom
    
    transformateur.delete()
    
    flash(f'Transformateur "{nom}" supprimé avec succès', 'success')
    return redirect(url_for('distribution.detail_poste', id=poste_id))


# === DONNÉES MENSUELLES DE DISTRIBUTION ===

@bp.route('/donnees-mensuelles')
@login_required
@role_required('operateur', 'admin_operateur', 'super_admin')
def donnees_mensuelles():
    """Page de gestion des données mensuelles de distribution"""
    
    from app.models.distribution import DonneesDistributionMensuelles
    
    # Filtres
    annee = request.args.get('annee', type=int, default=datetime.now().year)
    mois = request.args.get('mois', type=int)
    operateur_id = request.args.get('operateur_id', type=int)
    
    # Requête de base selon les permissions
    operateurs = get_accessible_operateurs()
    
    if current_user.is_admin():
        query = DonneesDistributionMensuelles.query
        if operateur_id:
            if not can_access_operateur(operateur_id):
                flash("Accès refusé à cet opérateur", "error")
                return redirect(url_for('distribution.donnees_mensuelles'))
            operateur_actuel = Operateur.query.get(operateur_id)
            query = query.filter_by(operateur_id=operateur_id)
        else:
            operateur_actuel = None
    else:
        # Opérateur ne voit que ses données
        if not current_user.operateur_id:
            flash("Aucun opérateur associé à votre compte", "warning")
            return redirect(url_for('distribution.index'))
        
        operateur_actuel = current_user.operateur
        query = DonneesDistributionMensuelles.query.filter_by(operateur_id=current_user.operateur_id)
    
    # Appliquer les filtres
    query = query.filter_by(annee=annee)
    if mois:
        query = query.filter_by(mois=mois)
    
    # Ordonner par période (plus récent en premier)
    donnees = query.order_by(
        DonneesDistributionMensuelles.annee.desc(),
        DonneesDistributionMensuelles.mois.desc()
    ).paginate(
        page=request.args.get('page', 1, type=int),
        per_page=20,
        error_out=False
    )
    
    # Calculer les statistiques globales pour l'année
    if operateur_actuel:
        # Statistiques pour un opérateur spécifique
        stats_operateur_id = operateur_actuel.id
    elif current_user.is_admin() and not operateur_id:
        # Super admin sans filtre opérateur - toutes les données
        stats_operateur_id = None
    else:
        # Cas par défaut - opérateur actuel ou premier accessible
        if current_user.operateur_id:
            stats_operateur_id = current_user.operateur_id
            operateur_actuel = current_user.operateur
        elif operateurs:
            stats_operateur_id = operateurs[0].id
            operateur_actuel = operateurs[0]
        else:
            stats_operateur_id = None
    
    if stats_operateur_id:
        stats_query = DonneesDistributionMensuelles.query.filter(
            DonneesDistributionMensuelles.operateur_id == stats_operateur_id,
            DonneesDistributionMensuelles.annee == annee
        )
    else:
        stats_query = DonneesDistributionMensuelles.query.filter(
            DonneesDistributionMensuelles.annee == annee
        )
    
    # Totaux sur l'année
    if stats_operateur_id:
        filter_condition = and_(
            DonneesDistributionMensuelles.operateur_id == stats_operateur_id,
            DonneesDistributionMensuelles.annee == annee
        )
    else:
        filter_condition = DonneesDistributionMensuelles.annee == annee
        
    total_energie = db.session.query(
        func.sum(
            func.coalesce(DonneesDistributionMensuelles.energie_distribuee_ht_mwh, 0) +
            func.coalesce(DonneesDistributionMensuelles.energie_distribuee_mt_mwh, 0) +
            func.coalesce(DonneesDistributionMensuelles.energie_distribuee_bt_mwh, 0)
        )
    ).filter(filter_condition).scalar() or 0
    
    total_revenus = db.session.query(
        func.sum(
            func.coalesce(DonneesDistributionMensuelles.revenus_ht_usd, 0) +
            func.coalesce(DonneesDistributionMensuelles.revenus_mt_usd, 0) +
            func.coalesce(DonneesDistributionMensuelles.revenus_bt_usd, 0)
        )
    ).filter(filter_condition).scalar() or 0
    
    # Dernières données client (du mois le plus récent)
    derniere_donnee = stats_query.order_by(
        DonneesDistributionMensuelles.mois.desc()
    ).first()
    
    total_clients = 0
    if derniere_donnee:
        total_clients = (
            (derniere_donnee.clients_ht_fin_mois or 0) +
            (derniere_donnee.clients_mt_fin_mois or 0) +
            (derniere_donnee.clients_bt_fin_mois or 0)
        )
    
    # Nombre de réseaux avec données
    nb_reseaux = db.session.query(
        func.count(func.distinct(DonneesDistributionMensuelles.reseau_id))
    ).filter(filter_condition).scalar() or 0
    
    stats = {
        'reseaux': nb_reseaux,
        'clients_connectes': total_clients,
        'energie_distribuee_gwh': round(total_energie / 1000, 2) if total_energie else 0,  # MWh -> GWh
        'revenus_usd': total_revenus
    }
    
    return render_template('distribution/donnees_mensuelles/index.html',
                         donnees=donnees,
                         operateurs=operateurs,
                         operateur_actuel=operateur_actuel,
                         annee=annee,
                         mois=mois,
                         stats=stats)


@bp.route('/donnees-mensuelles/nouvelle')
@login_required
@role_required('operateur', 'admin_operateur')
def nouvelle_donnee_mensuelle():
    """Formulaire pour ajouter des données mensuelles"""
    
    from app.distribution.forms import DonneesDistributionMensuellesForm
    
    if not current_user.operateur:
        flash("Vous devez être associé à un opérateur pour saisir des données", "error")
        return redirect(url_for('distribution.donnees_mensuelles'))
    
    form = DonneesDistributionMensuellesForm()
    
    return render_template('distribution/donnees_mensuelles/nouvelle.html',
                         form=form,
                         operateur=current_user.operateur)


@bp.route('/donnees-mensuelles/creer', methods=['POST'])
@login_required
@role_required('operateur', 'admin_operateur')
def creer_donnee_mensuelle():
    """Traiter la création des données mensuelles"""
    
    from app.distribution.forms import DonneesDistributionMensuellesForm
    from app.models.distribution import DonneesDistributionMensuelles
    
    if not current_user.operateur:
        flash("Vous devez être associé à un opérateur pour saisir des données", "error")
        return redirect(url_for('distribution.donnees_mensuelles'))
    
    form = DonneesDistributionMensuellesForm()
    
    if form.validate_on_submit():
        # Vérifier si des données existent déjà pour cette période/réseau
        existing = DonneesDistributionMensuelles.query.filter(
            DonneesDistributionMensuelles.reseau_id == form.reseau_id.data,
            DonneesDistributionMensuelles.annee == int(form.annee.data),
            DonneesDistributionMensuelles.mois == int(form.mois.data)
        ).first()
        
        if existing:
            flash(f"Des données existent déjà pour {form.mois.data}/{form.annee.data} sur ce réseau", "error")
            return render_template('distribution/donnees_mensuelles/nouvelle.html',
                                 form=form,
                                 operateur=current_user.operateur)
        
        # Vérifier que le réseau appartient à l'opérateur
        reseau = ReseauDistribution.query.get_or_404(form.reseau_id.data)
        if reseau.operateur_id != current_user.operateur.id:
            flash("Vous ne pouvez saisir des données que pour vos propres réseaux", "error")
            return render_template('distribution/donnees_mensuelles/nouvelle.html',
                                 form=form,
                                 operateur=current_user.operateur)
        
        # Créer les données
        donnee = DonneesDistributionMensuelles(
            reseau_id=form.reseau_id.data,
            operateur_id=current_user.operateur.id,
            annee=int(form.annee.data),
            mois=int(form.mois.data)
        )
        
        # Remplir tous les champs du formulaire
        form.populate_obj(donnee)
        
        # Corriger les champs qui ont été mal assignés
        donnee.reseau_id = form.reseau_id.data
        donnee.operateur_id = current_user.operateur.id
        donnee.annee = int(form.annee.data)
        donnee.mois = int(form.mois.data)
        
        donnee.save()
        
        flash(f"Données mensuelles ajoutées avec succès pour {donnee.get_periode_str()}", "success")
        return redirect(url_for('distribution.donnees_mensuelles'))
    
    # En cas d'erreur
    return render_template('distribution/donnees_mensuelles/nouvelle.html',
                         form=form,
                         operateur=current_user.operateur)


@bp.route('/donnees-mensuelles/<int:id>')
@login_required
def voir_donnee_mensuelle(id):
    """Voir le détail d'une donnée mensuelle"""
    
    from app.models.distribution import DonneesDistributionMensuelles
    
    donnee = DonneesDistributionMensuelles.query.get_or_404(id)
    
    # Vérification des permissions
    if current_user.role not in ['super_admin'] and current_user.operateur_id != donnee.operateur_id:
        flash("Accès refusé à ces données", "error")
        return redirect(url_for('distribution.donnees_mensuelles'))
    
    return render_template('distribution/donnees_mensuelles/voir.html',
                         donnee=donnee)


@bp.route('/donnees-mensuelles/<int:id>/modifier')
@login_required
@role_required('operateur', 'admin_operateur')
def modifier_donnee_mensuelle(id):
    """Formulaire de modification des données mensuelles"""
    
    from app.models.distribution import DonneesDistributionMensuelles
    from app.distribution.forms import DonneesDistributionMensuellesForm
    
    donnee = DonneesDistributionMensuelles.query.get_or_404(id)
    
    # Vérification des permissions
    if current_user.operateur_id != donnee.operateur_id:
        flash("Vous ne pouvez modifier que vos propres données", "error")
        return redirect(url_for('distribution.donnees_mensuelles'))
    
    form = DonneesDistributionMensuellesForm(obj=donnee)
    form.annee.data = str(donnee.annee)
    form.mois.data = str(donnee.mois)
    
    return render_template('distribution/donnees_mensuelles/modifier.html',
                         form=form,
                         donnee=donnee,
                         operateur=current_user.operateur)


@bp.route('/donnees-mensuelles/<int:id>/mettre-a-jour', methods=['POST'])
@login_required
@role_required('operateur', 'admin_operateur')
def mettre_a_jour_donnee_mensuelle(id):
    """Traiter la modification des données mensuelles"""
    
    from app.models.distribution import DonneesDistributionMensuelles
    from app.distribution.forms import DonneesDistributionMensuellesForm
    
    donnee = DonneesDistributionMensuelles.query.get_or_404(id)
    
    # Vérification des permissions
    if current_user.operateur_id != donnee.operateur_id:
        flash("Vous ne pouvez modifier que vos propres données", "error")
        return redirect(url_for('distribution.donnees_mensuelles'))
    
    form = DonneesDistributionMensuellesForm()
    
    if form.validate_on_submit():
        # Garder les identifiants inchangés
        original_reseau_id = donnee.reseau_id
        original_operateur_id = donnee.operateur_id
        original_annee = donnee.annee
        original_mois = donnee.mois
        
        # Remplir avec les données du formulaire
        form.populate_obj(donnee)
        
        # Restaurer les identifiants
        donnee.reseau_id = original_reseau_id
        donnee.operateur_id = original_operateur_id
        donnee.annee = original_annee
        donnee.mois = original_mois
        
        donnee.update()
        
        flash(f"Données mensuelles mises à jour avec succès", "success")
        return redirect(url_for('distribution.voir_donnee_mensuelle', id=id))
    
    return render_template('distribution/donnees_mensuelles/modifier.html',
                         form=form,
                         donnee=donnee,
                         operateur=current_user.operateur)