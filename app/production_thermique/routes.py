"""
Routes pour la production thermique
"""
import calendar
from flask import render_template, redirect, url_for, flash, request, abort, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, date
from sqlalchemy import extract, func, and_
from app.production_thermique import production_thermique
from app.production_thermique.forms import (
    RapportThermiqueForm, CentraleThermiqueForm, FiltreRapportThermiqueForm,
    GroupeProductionThermiqueForm
)
from app.models.production_thermique import (
    CentraleThermique, RapportThermique, GroupeProductionThermique
)
from app.extensions import db
from app.models.operateurs import Operateur
from app.extensions import db
from app.utils.permissions import (
    get_accessible_operateurs, can_access_operateur, 
    filter_query_by_operateur, get_default_operateur_id
)
import calendar


def get_accessible_centrales_thermique():
    """Obtenir les centrales thermiques accessibles selon les permissions"""
    if current_user.is_admin():
        return CentraleThermique.query.filter_by(actif=True).all()
    elif current_user.operateur:
        return CentraleThermique.query.filter_by(
            operateur_id=current_user.operateur.id,
            actif=True
        ).all()
    return []


@production_thermique.route('/')
@login_required
def index():
    """Liste des rapports de production thermique"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Vérifier les permissions d'accès au module
    if not (current_user.is_admin() or current_user.operateur):
        flash('Aucune centrale thermique accessible.', 'warning')
        return render_template('production_thermique/no_access.html')
    
    # Obtenir les centrales accessibles
    centrales_accessibles = get_accessible_centrales_thermique()
    
    # IDs des centrales accessibles (peut être vide pour super admin)
    centrale_ids = [c.id for c in centrales_accessibles] if centrales_accessibles else []
    
    # Années disponibles pour les filtres
    annees = []
    if centrale_ids:
        annees = db.session.query(extract('year', RapportThermique.periode_debut).label('annee'))\
            .filter(RapportThermique.centrale_id.in_(centrale_ids))\
            .distinct().order_by('annee').all()
    
    # Créer le formulaire de filtrage
    filtre_form = FiltreRapportThermiqueForm()
    filtre_form.centrale_id.choices = [(None, 'Toutes les centrales')] + [
        (c.id, c.nom) for c in centrales_accessibles
    ]
    filtre_form.annee.choices = [(None, 'Toutes les années')] + [(int(a.annee), str(a.annee)) for a in annees]
    
    # Requête de base pour les rapports
    if centrales_accessibles:
        query = RapportThermique.query.filter(RapportThermique.centrale_id.in_(centrale_ids))
    else:
        # Si pas de centrales mais utilisateur autorisé, afficher page vide
        query = RapportThermique.query.filter(False)  # Requête qui retourne rien

        # Maintenant initialiser avec les données de l'URL
    filtre_form.process(dict(request.args))
    
    # Requête de base pour les rapports
    if centrales_accessibles:
        query = RapportThermique.query.filter(RapportThermique.centrale_id.in_(centrale_ids))
    else:
        # Si pas de centrales mais utilisateur autorisé, afficher page vide
        query = RapportThermique.query.filter(False)  # Requête qui retourne rien
    
    # Appliquer les filtres depuis les paramètres GET
    mois_param = request.args.get('mois')
    if mois_param and mois_param.isdigit():
        query = query.filter(RapportThermique.mois == int(mois_param))
    
    annee_param = request.args.get('annee')
    if annee_param and annee_param.isdigit():
        query = query.filter(extract('year', RapportThermique.periode_debut) == int(annee_param))
    
    centrale_param = request.args.get('centrale_id')
    if centrale_param and centrale_param.isdigit():
        query = query.filter(RapportThermique.centrale_id == int(centrale_param))
    
    statut_param = request.args.get('statut')
    if statut_param:
        query = query.filter(RapportThermique.statut == statut_param)
    
    # Recherche textuelle
    search = request.args.get('search', '', type=str)
    if search:
        centrales_ids_search = [c.id for c in centrales_accessibles if search.lower() in c.nom.lower()]
        if centrales_ids_search:
            query = query.filter(RapportThermique.centrale_id.in_(centrales_ids_search))
        else:
            query = query.filter(False)  # Aucun résultat si pas de correspondance
    
    # Pagination
    rapports = query.order_by(RapportThermique.periode_debut.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Statistiques générales (toujours basées sur tous les rapports accessibles)
    stats = {
        'total_rapports': RapportThermique.query.filter(RapportThermique.centrale_id.in_(centrale_ids)).count(),
        'rapports_valides': RapportThermique.query.filter(
            RapportThermique.centrale_id.in_(centrale_ids),
            RapportThermique.statut == 'valide'
        ).count(),
        'energie_totale': db.session.query(func.sum(RapportThermique.energie_produite))\
            .filter(RapportThermique.centrale_id.in_(centrale_ids)).scalar() or 0,
        'nombre_centrales': len(centrales_accessibles),
        'rapports_brouillon': RapportThermique.query.filter(
            RapportThermique.centrale_id.in_(centrale_ids),
            RapportThermique.statut == 'brouillon'
        ).count()
    }
    
    return render_template('production_thermique/index.html',
                         rapports=rapports,
                         filtre_form=filtre_form,
                         stats=stats,
                         centrales=centrales_accessibles,
                         search=search,
                         title='Production Thermique')


@production_thermique.route('/rapport/nouveau', methods=['GET', 'POST'])
@login_required
def nouveau_rapport():
    """Nouveau rapport de production thermique"""
    centrales = get_accessible_centrales_thermique()
    if not centrales:
        flash('Aucune centrale thermique disponible pour créer un rapport.', 'warning')
        return redirect(url_for('production_thermique.index'))
    
    form = RapportThermiqueForm()
    
    if form.validate_on_submit():
        # Vérifier les permissions pour cette centrale
        centrale = CentraleThermique.query.get_or_404(form.centrale_id.data)
        if not current_user.is_admin() and centrale.operateur_id != current_user.operateur_id:
            flash('Vous n\'avez pas l\'autorisation de créer un rapport pour cette centrale.', 'error')
            return redirect(url_for('production_thermique.index'))
            
        # Vérifier qu'un rapport n'existe pas déjà pour cette période
        rapport_existant = RapportThermique.query.filter_by(
            centrale_id=form.centrale_id.data,
            annee=form.annee.data,
            mois=form.mois.data
        ).first()
        
        if rapport_existant:
            flash(f'Un rapport existe déjà pour {calendar.month_name[form.mois.data]} {form.annee.data}.', 'error')
            return render_template('production_thermique/rapport_form.html',
                                 form=form,
                                 centrales=centrales,
                                 action='nouveau',
                                 title='Nouveau Rapport Thermique')
        
        # Créer le nouveau rapport
        # Convertir les dates en datetime pour la base de données
        periode_debut = datetime.combine(form.periode_debut.data, datetime.min.time())
        periode_fin = datetime.combine(form.periode_fin.data, datetime.min.time())
        
        rapport = RapportThermique(
            centrale_id=form.centrale_id.data,
            annee=form.annee.data,
            mois=form.mois.data,
            periode_debut=periode_debut,
            periode_fin=periode_fin,
            energie_produite=form.energie_produite.data,
            energie_disponible=form.energie_disponible.data,
            facteur_charge=form.facteur_charge.data,
            temps_fonctionnement=form.temps_fonctionnement.data,
            nombre_demarrages=form.nombre_demarrages.data,
            nombre_arrets=form.nombre_arrets.data,
            consommation_combustible=form.consommation_combustible.data,
            type_combustible_utilise=form.type_combustible_utilise.data,
            cout_combustible=form.cout_combustible.data,
            observations=form.observations.data,
            statut=form.statut.data
        )
        
        try:
            rapport.save()
            flash('Rapport thermique créé avec succès.', 'success')
            return redirect(url_for('production_thermique.detail_rapport', id=rapport.id))
        except Exception as e:
            db.session.rollback()
            flash('Erreur lors de la création du rapport.', 'error')
            current_app.logger.error(f"Erreur création rapport: {e}")
    
    # Pré-remplir avec la date actuelle pour GET requests
    if not form.annee.data:
        form.annee.data = datetime.now().year
    if not form.mois.data:
        form.mois.data = datetime.now().month
    
    # Calculer les dates de début et fin du mois
    if form.annee.data and form.mois.data:
        debut_mois = date(form.annee.data, form.mois.data, 1)
        if form.mois.data == 12:
            fin_mois = date(form.annee.data + 1, 1, 1)
        else:
            fin_mois = date(form.annee.data, form.mois.data + 1, 1)
        
        if not form.periode_debut.data:
            form.periode_debut.data = debut_mois
        if not form.periode_fin.data:
            form.periode_fin.data = fin_mois
    
    return render_template('production_thermique/rapport_form.html',
                         form=form,
                         centrales=centrales,
                         action='nouveau',
                         title='Nouveau Rapport Thermique')


@production_thermique.route('/rapport/nouveau/<int:centrale_id>', methods=['GET', 'POST'])
@login_required
def nouveau_rapport_centrale(centrale_id):
    """Nouveau rapport pour une centrale spécifique"""
    centrales = get_accessible_centrales_thermique()
    centrale = next((c for c in centrales if c.id == centrale_id), None)
    
    if not centrale:
        flash('Centrale non trouvée ou accès refusé.', 'error')
        return redirect(url_for('production_thermique.index'))
    
    form = RapportThermiqueForm()
    
    if form.validate_on_submit():
        # Vérifier qu'un rapport n'existe pas déjà pour cette période
        rapport_existant = RapportThermique.query.filter_by(
            centrale_id=centrale_id,
            annee=form.annee.data,
            mois=form.mois.data
        ).first()
        
        if rapport_existant:
            flash(f'Un rapport existe déjà pour {calendar.month_name[form.mois.data]} {form.annee.data}.', 'error')
            return render_template('production_thermique/rapport_form.html',
                                 form=form,
                                 centrale=centrale,
                                 action='nouveau',
                                 title='Nouveau Rapport Thermique')
        
        # Créer le nouveau rapport
        # Convertir les dates en datetime pour la base de données
        periode_debut = datetime.combine(form.periode_debut.data, datetime.min.time())
        periode_fin = datetime.combine(form.periode_fin.data, datetime.min.time())

        rapport = RapportThermique(
            centrale_id=centrale_id,
            annee=form.annee.data,
            mois=form.mois.data,
            periode_debut=periode_debut,
            periode_fin=periode_fin
        )
        
        # Utiliser populate_obj pour tous les autres champs
        form.populate_obj(rapport)
        
        # Définir le statut par défaut si pas défini
        if not rapport.statut:
            rapport.statut = 'brouillon'
        
        try:
            rapport.save()
            flash('Rapport créé avec succès.', 'success')
            return redirect(url_for('production_thermique.detail_rapport', id=rapport.id))
        except Exception as e:
            current_app.logger.error(f'Erreur lors de la création du rapport: {e}')
            flash('Erreur lors de la création du rapport.', 'error')
    
    return render_template('production_thermique/rapport_form.html',
                         form=form,
                         centrale=centrale,
                         action='nouveau',
                         title='Nouveau Rapport Thermique')


@production_thermique.route('/rapport/<int:id>')
@login_required
def detail_rapport(id):
    """Détail d'un rapport de production thermique"""
    rapport = RapportThermique.query.get_or_404(id)
    
    # Vérifier l'accès
    centrales_accessibles = get_accessible_centrales_thermique()
    if rapport.centrale not in centrales_accessibles:
        abort(403)
    
    return render_template('production_thermique/detail_rapport.html',
                         rapport=rapport,
                         title=f'Rapport {rapport.centrale.nom} - {rapport.mois}/{rapport.annee}')


@production_thermique.route('/rapport/<int:id>/modifier', methods=['GET', 'POST'])
@login_required
def modifier_rapport(id):
    """Modifier un rapport de production thermique"""
    rapport = RapportThermique.query.get_or_404(id)
    
    # Vérifier l'accès
    centrales_accessibles = get_accessible_centrales_thermique()
    if rapport.centrale not in centrales_accessibles:
        abort(403)
    
    # Vérifier si le rapport peut être modifié
    if rapport.statut == 'transmis' and current_user.role != 'super_admin':
        flash('Ce rapport a déjà été transmis et ne peut plus être modifié.', 'error')
        return redirect(url_for('production_thermique.detail_rapport', id=id))
    
    form = RapportThermiqueForm(obj=rapport)
    
    if form.validate_on_submit():
        # Mettre à jour le rapport
        form.populate_obj(rapport)
        
        try:
            rapport.save()
            flash('Rapport modifié avec succès.', 'success')
            return redirect(url_for('production_thermique.detail_rapport', id=id))
        except Exception as e:
            current_app.logger.error(f'Erreur lors de la modification du rapport: {e}')
            flash('Erreur lors de la modification du rapport.', 'error')
    
    return render_template('production_thermique/rapport_form.html',
                         form=form,
                         centrale=rapport.centrale,
                         rapport=rapport,
                         action='modifier',
                         title='Modifier Rapport Thermique')


@production_thermique.route('/rapport/<int:id>/supprimer', methods=['POST'])
@login_required
def supprimer_rapport(id):
    """Supprimer un rapport de production thermique"""
    rapport = RapportThermique.query.get_or_404(id)
    
    # Vérifier l'accès
    centrales_accessibles = get_accessible_centrales_thermique()
    if rapport.centrale not in centrales_accessibles:
        abort(403)
    
    # Vérifier les permissions
    if rapport.statut == 'transmis' and current_user.role != 'super_admin':
        flash('Ce rapport a déjà été transmis et ne peut pas être supprimé.', 'error')
        return redirect(url_for('production_thermique.detail_rapport', id=id))
    
    try:
        rapport.delete()
        flash('Rapport supprimé avec succès.', 'success')
    except Exception as e:
        current_app.logger.error(f'Erreur lors de la suppression du rapport: {e}')
        flash('Erreur lors de la suppression du rapport.', 'error')
    
    return redirect(url_for('production_thermique.index'))


@production_thermique.route('/centrales')
@login_required
def liste_centrales():
    """Liste des centrales thermiques"""
    centrales = get_accessible_centrales_thermique()
    
    return render_template('production_thermique/liste_centrales.html',
                         centrales=centrales,
                         title='Centrales Thermiques')


@production_thermique.route('/centrale/nouvelle', methods=['GET', 'POST'])
@login_required
def nouvelle_centrale():
    """Nouvelle centrale thermique"""
    if current_user.role != 'super_admin':
        flash('Accès refusé. Seuls les super administrateurs peuvent créer des centrales.', 'error')
        return redirect(url_for('production_thermique.liste_centrales'))
    
    form = CentraleThermiqueForm()
    operateurs = Operateur.query.filter_by(actif=True).all()
    
    if form.validate_on_submit():
        # Vérifier l'unicité du code
        centrale_existante = CentraleThermique.query.filter_by(code=form.code.data).first()
        if centrale_existante:
            flash('Une centrale avec ce code existe déjà.', 'error')
            return render_template('production_thermique/centrale_form.html',
                                 form=form,
                                 operateurs=operateurs,
                                 action='nouvelle',
                                 title='Nouvelle Centrale Thermique')
        
        # Créer la nouvelle centrale
        centrale = CentraleThermique(
            operateur_id=form.operateur_id.data,
            nom=form.nom.data,
            code=form.code.data,
            localisation=form.localisation.data,
            province=form.province.data,
            puissance_installee=form.puissance_installee.data,
            puissance_disponible=form.puissance_disponible.data,
            type_centrale=form.type_centrale.data,
            type_combustible=form.type_combustible.data,
            consommation_specifique=form.consommation_specifique.data,
            latitude=form.latitude.data,
            longitude=form.longitude.data,
            nombre_groupes=form.nombre_groupes.data,
            type_moteur=form.type_moteur.data,
            refroidissement=form.refroidissement.data,
            niveau_tension=form.niveau_tension.data,
            tension_evacuation=form.tension_evacuation.data,
            systeme_demarrage=form.systeme_demarrage.data,
            systeme_refroidissement=form.systeme_refroidissement.data,
            capacite_stockage_combustible=form.capacite_stockage_combustible.data,
            autonomie_combustible=form.autonomie_combustible.data,
            systeme_traitement_fumees=form.systeme_traitement_fumees.data,
            niveau_emission_nox=form.niveau_emission_nox.data,
            niveau_emission_co=form.niveau_emission_co.data,
            certification_environnementale=form.certification_environnementale.data,
            statut=form.statut.data,
            mode_fonctionnement=form.mode_fonctionnement.data,
            description=form.description.data,
            date_mise_service=form.date_mise_service.data,
            date_derniere_revision=form.date_derniere_revision.data,
            prochaine_maintenance=form.prochaine_maintenance.data,
            constructeur=form.constructeur.data,
            fournisseur_combustible=form.fournisseur_combustible.data,
            annee_construction=form.annee_construction.data,
            duree_vie_estimee=form.duree_vie_estimee.data,
            observations=form.observations.data
        )
        
        try:
            centrale.save()
            flash('Centrale créée avec succès.', 'success')
            return redirect(url_for('production_thermique.detail_centrale', id=centrale.id))
        except Exception as e:
            current_app.logger.error(f'Erreur lors de la création de la centrale: {e}')
            flash('Erreur lors de la création de la centrale.', 'error')
    
    return render_template('production_thermique/centrale_form.html',
                         form=form,
                         operateurs=operateurs,
                         action='nouvelle',
                         title='Nouvelle Centrale Thermique')


@production_thermique.route('/centrale/<int:id>/modifier', methods=['GET', 'POST'])
@login_required
def modifier_centrale(id):
    """Modifier une centrale thermique"""
    centrale = CentraleThermique.query.get_or_404(id)
    
    # Vérifier les permissions
    if not current_user.is_super_admin():
        flash('Accès refusé. Seuls les super administrateurs peuvent modifier des centrales.', 'error')
        return redirect(url_for('production_thermique.detail_centrale', id=id))
    
    form = CentraleThermiqueForm(obj=centrale)
    operateurs = Operateur.query.filter_by(actif=True).all()
    
    if form.validate_on_submit():
        # Vérifier l'unicité du code (sauf pour la centrale actuelle)
        centrale_existante = CentraleThermique.query.filter(
            CentraleThermique.code == form.code.data,
            CentraleThermique.id != id
        ).first()
        if centrale_existante:
            flash('Une centrale avec ce code existe déjà.', 'error')
            return render_template('production_thermique/centrale_form.html',
                                 form=form,
                                 operateurs=operateurs,
                                 action='modifier',
                                 title=f'Modifier Centrale {centrale.nom}')
        
        # Mettre à jour la centrale
        centrale.operateur_id = form.operateur_id.data
        centrale.nom = form.nom.data
        centrale.code = form.code.data
        centrale.localisation = form.localisation.data
        centrale.province = form.province.data
        centrale.puissance_installee = form.puissance_installee.data
        centrale.puissance_disponible = form.puissance_disponible.data
        centrale.type_centrale = form.type_centrale.data
        centrale.type_combustible = form.type_combustible.data
        centrale.consommation_specifique = form.consommation_specifique.data
        centrale.latitude = form.latitude.data
        centrale.longitude = form.longitude.data
        centrale.nombre_groupes = form.nombre_groupes.data
        centrale.type_moteur = form.type_moteur.data
        centrale.refroidissement = form.refroidissement.data
        centrale.niveau_tension = form.niveau_tension.data
        centrale.tension_evacuation = form.tension_evacuation.data
        centrale.systeme_demarrage = form.systeme_demarrage.data
        centrale.systeme_refroidissement = form.systeme_refroidissement.data
        centrale.capacite_stockage_combustible = form.capacite_stockage_combustible.data
        centrale.autonomie_combustible = form.autonomie_combustible.data
        centrale.systeme_traitement_fumees = form.systeme_traitement_fumees.data
        centrale.niveau_emission_nox = form.niveau_emission_nox.data
        centrale.niveau_emission_co = form.niveau_emission_co.data
        centrale.certification_environnementale = form.certification_environnementale.data
        centrale.statut = form.statut.data
        centrale.mode_fonctionnement = form.mode_fonctionnement.data
        centrale.description = form.description.data
        centrale.date_mise_service = form.date_mise_service.data
        centrale.date_derniere_revision = form.date_derniere_revision.data
        centrale.prochaine_maintenance = form.prochaine_maintenance.data
        centrale.constructeur = form.constructeur.data
        centrale.fournisseur_combustible = form.fournisseur_combustible.data
        centrale.annee_construction = form.annee_construction.data
        centrale.duree_vie_estimee = form.duree_vie_estimee.data
        centrale.observations = form.observations.data
        
        try:
            centrale.save()
            flash('Centrale modifiée avec succès.', 'success')
            return redirect(url_for('production_thermique.detail_centrale', id=centrale.id))
        except Exception as e:
            current_app.logger.error(f'Erreur lors de la modification de la centrale: {e}')
            flash('Erreur lors de la modification de la centrale.', 'error')
    
    return render_template('production_thermique/centrale_form.html',
                         form=form,
                         operateurs=operateurs,
                         action='modifier',
                         title=f'Modifier Centrale {centrale.nom}')


@production_thermique.route('/centrale/<int:id>')
@login_required
def detail_centrale(id):
    """Détail d'une centrale thermique"""
    centrale = CentraleThermique.query.get_or_404(id)
    
    # Vérifier l'accès
    centrales_accessibles = get_accessible_centrales_thermique()
    if centrale not in centrales_accessibles:
        abort(403)
    
    # Derniers rapports
    derniers_rapports = RapportThermique.query.filter_by(centrale_id=id)\
        .order_by(RapportThermique.periode_debut.desc()).limit(5).all()
    
    # Statistiques de production
    stats = {
        'total_rapports': RapportThermique.query.filter_by(centrale_id=id).count(),
        'energie_totale': db.session.query(func.sum(RapportThermique.energie_produite))\
            .filter_by(centrale_id=id).scalar() or 0,
        'facteur_charge_moyen': db.session.query(func.avg(RapportThermique.facteur_charge))\
            .filter_by(centrale_id=id).scalar() or 0,
        'derniere_maintenance': centrale.date_derniere_revision
    }
    
    return render_template('production_thermique/detail_centrale.html',
                         centrale=centrale,
                         derniers_rapports=derniers_rapports,
                         stats=stats,
                         title=f'Centrale {centrale.nom}')


@production_thermique.route('/centrale/<int:id>/supprimer', methods=['POST', 'DELETE'])
@login_required
def supprimer_centrale(id):
    """Supprimer une centrale thermique (soft delete)"""
    # Vérifier les permissions
    if not current_user.is_super_admin():
        flash('Accès refusé. Seuls les super administrateurs peuvent supprimer des centrales.', 'danger')
        return redirect(url_for('production_thermique.liste_centrales'))

    # Récupérer la centrale
    centrale = CentraleThermique.query.get_or_404(id)

    # Vérifier s'il y a des rapports associés
    rapports_count = RapportThermique.query.filter_by(centrale_id=id, actif=True).count()
    if rapports_count > 0:
        flash(f'Impossible de supprimer la centrale "{centrale.nom}". Elle possède {rapports_count} rapport(s) associé(s).', 'danger')
        return redirect(url_for('production_thermique.liste_centrales'))

    try:
        # Soft delete
        centrale.actif = False
        centrale.save()

        flash(f'Centrale "{centrale.nom}" supprimée avec succès.', 'success')
    except Exception as e:
        current_app.logger.error(f'Erreur lors de la suppression de la centrale {id}: {str(e)}')
        flash('Erreur lors de la suppression de la centrale.', 'danger')

    return redirect(url_for('production_thermique.liste_centrales'))


@production_thermique.route('/api/statistiques')
@login_required
def api_statistiques():
    """API pour les statistiques de production thermique"""
    centrales_accessibles = get_accessible_centrales_thermique()
    centrale_ids = [c.id for c in centrales_accessibles]
    
    if not centrale_ids:
        return jsonify({
            'total_centrales': 0,
            'energie_totale': 0,
            'production_mensuelle': [],
            'repartition_type': []
        })
    
    # Production mensuelle des 12 derniers mois
    production_mensuelle = db.session.query(
        RapportThermique.mois,
        func.sum(RapportThermique.energie_produite).label('production')
    ).filter(
        RapportThermique.centrale_id.in_(centrale_ids),
        RapportThermique.annee == datetime.now().year
    ).group_by(RapportThermique.mois).all()
    
    # Répartition par type de combustible
    repartition_type = db.session.query(
        CentraleThermique.type_combustible,
        func.sum(RapportThermique.energie_produite).label('production')
    ).join(
        RapportThermique
    ).filter(
        CentraleThermique.id.in_(centrale_ids)
    ).group_by(CentraleThermique.type_combustible).all()
    
    return jsonify({
        'total_centrales': len(centrales_accessibles),
        'energie_totale': db.session.query(func.sum(RapportThermique.energie_produite))\
            .filter(RapportThermique.centrale_id.in_(centrale_ids)).scalar() or 0,
        'production_mensuelle': [
            {'mois': p.mois, 'production': float(p.production or 0)}
            for p in production_mensuelle
        ],
        'repartition_type': [
            {'type': r.type_combustible or 'Non défini', 'production': float(r.production or 0)}
            for r in repartition_type
        ]
    })