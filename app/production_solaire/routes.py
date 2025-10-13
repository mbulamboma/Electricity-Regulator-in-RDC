"""
Routes pour la production solaire
"""
import calendar
from flask import render_template, redirect, url_for, flash, request, abort, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, date
from sqlalchemy import extract, func, and_
from app.production_solaire import production_solaire
from app.production_solaire.forms import (
    RapportSolaireForm, CentraleSolaireForm, FiltreRapportSolaireForm,
    DonneesSolaireQuotidiennesForm
)
from app.models.production_solaire import (
    CentraleSolaire, RapportSolaire, DonneesSolaireQuotidiennes
)
from app.extensions import db
from app.models.operateurs import Operateur
from app.extensions import db
from app.utils.permissions import (
    get_accessible_operateurs, can_access_operateur, 
    filter_query_by_operateur, get_default_operateur_id
)
import calendar


def get_accessible_centrales_solaire():
    """Obtenir les centrales solaires accessibles selon les permissions"""
    if current_user.is_admin():
        return CentraleSolaire.query.filter_by(actif=True).all()
    elif current_user.operateur:
        return CentraleSolaire.query.filter_by(
            operateur_id=current_user.operateur.id,
            actif=True
        ).all()
    return []


@production_solaire.route('/')
@login_required
def index():
    """Liste des rapports de production solaire"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Vérifier les permissions d'accès au module
    if not (current_user.is_admin() or current_user.operateur):
        flash('Aucune centrale solaire accessible.', 'warning')
        return render_template('production_solaire/no_access.html')
    
    # Obtenir les centrales accessibles
    centrales_accessibles = get_accessible_centrales_solaire()
    
    # IDs des centrales accessibles (peut être vide pour super admin)
    centrale_ids = [c.id for c in centrales_accessibles] if centrales_accessibles else []
    
    # Requête de base pour les rapports
    if centrales_accessibles:
        query = RapportSolaire.query.filter(RapportSolaire.centrale_id.in_(centrale_ids))
    else:
        # Si pas de centrales mais utilisateur autorisé, afficher page vide
        query = RapportSolaire.query.filter(False)  # Requête qui retourne rien
    
    # Filtres
    filtre_form = FiltreRapportSolaireForm()
    filtre_form.centrale_id.choices = [(None, 'Toutes les centrales')] + [
        (c.id, c.nom) for c in centrales_accessibles
    ]
    
    # Années disponibles
    annees = db.session.query(extract('year', RapportSolaire.periode_debut).label('annee'))\
        .filter(RapportSolaire.centrale_id.in_(centrale_ids))\
        .distinct().order_by('annee').all()
    filtre_form.annee.choices = [(None, 'Toutes les années')] + [(int(a.annee), str(a.annee)) for a in annees]
    
    if filtre_form.validate_on_submit():
        if filtre_form.centrale_id.data is not None:
            query = query.filter(RapportSolaire.centrale_id == filtre_form.centrale_id.data)
        if filtre_form.annee.data is not None:
            query = query.filter(extract('year', RapportSolaire.periode_debut) == filtre_form.annee.data)
        if filtre_form.mois.data:
            query = query.filter(RapportSolaire.mois == int(filtre_form.mois.data))
        if filtre_form.statut.data:
            query = query.filter(RapportSolaire.statut == filtre_form.statut.data)
    
    # Pagination
    rapports = query.order_by(RapportSolaire.periode_debut.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Statistiques générales
    stats = {
        'total_rapports': query.count(),
        'rapports_valides': query.filter(RapportSolaire.statut == 'valide').count(),
        'energie_totale': db.session.query(func.sum(RapportSolaire.energie_produite))\
            .filter(RapportSolaire.centrale_id.in_(centrale_ids)).scalar() or 0,
        'nombre_centrales': len(centrales_accessibles),
        'performance_ratio_moyenne': db.session.query(func.avg(RapportSolaire.performance_ratio))\
            .filter(RapportSolaire.centrale_id.in_(centrale_ids)).scalar() or 0
    }
    
    return render_template('production_solaire/index.html',
                         rapports=rapports,
                         filtre_form=filtre_form,
                         stats=stats,
                         centrales=centrales_accessibles,
                         title='Production Solaire')


@production_solaire.route('/rapport/nouveau', methods=['GET', 'POST'])
@login_required
def nouveau_rapport():
    """Nouveau rapport de production solaire"""
    centrales = get_accessible_centrales_solaire()
    if not centrales:
        flash('Aucune centrale solaire disponible pour créer un rapport.', 'warning')
        return redirect(url_for('production_solaire.index'))
    
    form = RapportSolaireForm()
    
    if form.validate_on_submit():
        # Vérifier les permissions pour cette centrale
        centrale = CentraleSolaire.query.get_or_404(form.centrale_id.data)
        if not current_user.is_admin() and centrale.operateur_id != current_user.operateur_id:
            flash('Vous n\'avez pas l\'autorisation de créer un rapport pour cette centrale.', 'error')
            return redirect(url_for('production_solaire.index'))
            
        # Vérifier qu'un rapport n'existe pas déjà pour cette période
        rapport_existant = RapportSolaire.query.filter_by(
            centrale_id=form.centrale_id.data,
            annee=form.annee.data,
            mois=form.mois.data
        ).first()
        
        if rapport_existant:
            flash(f'Un rapport existe déjà pour {calendar.month_name[form.mois.data]} {form.annee.data}.', 'error')
            return render_template('production_solaire/rapport_form.html',
                                 form=form,
                                 centrales=centrales,
                                 action='nouveau',
                                 title='Nouveau Rapport Solaire')
        
        # Créer le nouveau rapport
        # Convertir les dates en datetime pour la base de données
        periode_debut = datetime.combine(form.periode_debut.data, datetime.min.time())
        periode_fin = datetime.combine(form.periode_fin.data, datetime.min.time())
        
        rapport = RapportSolaire(
            centrale_id=form.centrale_id.data,
            annee=form.annee.data,
            mois=form.mois.data,
            periode_debut=periode_debut,
            periode_fin=periode_fin,
            energie_produite=form.energie_produite.data,
            energie_disponible=form.energie_disponible.data,
            facteur_charge=form.facteur_charge.data,
            productible_theorique=form.productible_theorique.data,
            performance_ratio=form.performance_ratio.data,
            irradiation_totale=form.irradiation_totale.data,
            irradiation_moyenne_quotidienne=form.irradiation_moyenne_quotidienne.data,
            temperature_ambiante_moyenne=form.temperature_ambiante_moyenne.data,
            temperature_modules_moyenne=form.temperature_modules_moyenne.data,
            humidite_relative_moyenne=form.humidite_relative_moyenne.data,
            vitesse_vent_moyenne=form.vitesse_vent_moyenne.data,
            heures_ensoleillement=form.heures_ensoleillement.data,
            rendement_global=form.rendement_global.data,
            rendement_modules=form.rendement_modules.data,
            rendement_onduleurs=form.rendement_onduleurs.data,
            observations=form.observations.data,
            statut=form.statut.data
        )
        
        try:
            rapport.save()
            flash('Rapport solaire créé avec succès.', 'success')
            return redirect(url_for('production_solaire.detail_rapport', id=rapport.id))
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
    
    return render_template('production_solaire/rapport_form.html',
                         form=form,
                         centrales=centrales,
                         action='nouveau',
                         title='Nouveau Rapport Solaire')


@production_solaire.route('/rapport/nouveau/<int:centrale_id>', methods=['GET', 'POST'])
@login_required
def nouveau_rapport_centrale(centrale_id):
    """Nouveau rapport pour une centrale solaire spécifique"""
    centrales = get_accessible_centrales_solaire()
    centrale = next((c for c in centrales if c.id == centrale_id), None)
    
    if not centrale:
        flash('Centrale non trouvée ou accès refusé.', 'error')
        return redirect(url_for('production_solaire.index'))
    
    form = RapportSolaireForm()
    
    if form.validate_on_submit():
        # Vérifier qu'un rapport n'existe pas déjà pour cette période
        rapport_existant = RapportSolaire.query.filter_by(
            centrale_id=centrale_id,
            annee=form.annee.data,
            mois=form.mois.data
        ).first()
        
        if rapport_existant:
            flash(f'Un rapport existe déjà pour {calendar.month_name[form.mois.data]} {form.annee.data}.', 'error')
            return render_template('production_solaire/rapport_form.html',
                                 form=form,
                                 centrale=centrale,
                                 action='nouveau',
                                 title='Nouveau Rapport Solaire')
        
        # Créer le nouveau rapport
        # Convertir les dates en datetime pour la base de données
        periode_debut = datetime.combine(form.periode_debut.data, datetime.min.time())
        periode_fin = datetime.combine(form.periode_fin.data, datetime.min.time())
        
        rapport = RapportSolaire(
            centrale_id=centrale_id,
            annee=form.annee.data,
            mois=form.mois.data,
            periode_debut=periode_debut,
            periode_fin=periode_fin,
            energie_produite=form.energie_produite.data,
            energie_disponible=form.energie_disponible.data,
            facteur_charge=form.facteur_charge.data,
            productible_theorique=form.productible_theorique.data,
            performance_ratio=form.performance_ratio.data,
            irradiation_totale=form.irradiation_totale.data,
            irradiation_moyenne_quotidienne=form.irradiation_moyenne_quotidienne.data,
            temperature_ambiante_moyenne=form.temperature_ambiante_moyenne.data,
            temperature_modules_moyenne=form.temperature_modules_moyenne.data,
            humidite_relative_moyenne=form.humidite_relative_moyenne.data,
            vitesse_vent_moyenne=form.vitesse_vent_moyenne.data,
            heures_ensoleillement=form.heures_ensoleillement.data,
            rendement_global=form.rendement_global.data,
            rendement_modules=form.rendement_modules.data,
            rendement_onduleurs=form.rendement_onduleurs.data,
            pertes_ombrages=form.pertes_ombrages.data,
            pertes_cables=form.pertes_cables.data,
            pertes_poussiere=form.pertes_poussiere.data,
            pertes_thermiques=form.pertes_thermiques.data,
            temps_fonctionnement_onduleurs=form.temps_fonctionnement_onduleurs.data,
            nombre_demarrages_onduleurs=form.nombre_demarrages_onduleurs.data,
            nombre_arrets_onduleurs=form.nombre_arrets_onduleurs.data,
            alarmes_onduleurs=form.alarmes_onduleurs.data,
            energie_stockee=form.energie_stockee.data,
            energie_destockee=form.energie_destockee.data,
            rendement_stockage=form.rendement_stockage.data,
            cycles_charge_decharge=form.cycles_charge_decharge.data,
            etat_sante_batteries=form.etat_sante_batteries.data,
            precision_suivi_moyenne=form.precision_suivi_moyenne.data,
            defauts_suivi=form.defauts_suivi.data,
            maintenance_systeme_suivi=form.maintenance_systeme_suivi.data,
            maintenances_preventives=form.maintenances_preventives.data,
            maintenances_correctives=form.maintenances_correctives.data,
            nettoyage_modules=form.nettoyage_modules.data,
            incidents_majeurs=form.incidents_majeurs.data,
            description_incidents=form.description_incidents.data,
            modules_defectueux=form.modules_defectueux.data,
            onduleurs_defectueux=form.onduleurs_defectueux.data,
            defauts_systeme_monitoring=form.defauts_systeme_monitoring.data,
            disponibilite_donnees=form.disponibilite_donnees.data,
            precision_mesures=form.precision_mesures.data,
            reduction_emissions_co2=form.reduction_emissions_co2.data,
            impact_environnemental=form.impact_environnemental.data,
            gestion_fin_vie_composants=form.gestion_fin_vie_composants.data,
            cout_maintenance=form.cout_maintenance.data,
            cout_nettoyage=form.cout_nettoyage.data,
            recettes_vente=form.recettes_vente.data,
            economie_carburant=form.economie_carburant.data,
            rentabilite=form.rentabilite.data,
            degradation_observee=form.degradation_observee.data,
            disponibilite_systeme=form.disponibilite_systeme.data,
            taux_defaillance=form.taux_defaillance.data,
            observations=form.observations.data,
            statut='brouillon'
        )
        
        try:
            rapport.save()
            flash('Rapport créé avec succès.', 'success')
            return redirect(url_for('production_solaire.detail_rapport', id=rapport.id))
        except Exception as e:
            current_app.logger.error(f'Erreur lors de la création du rapport: {e}')
            flash('Erreur lors de la création du rapport.', 'error')
    
    return render_template('production_solaire/rapport_form.html',
                         form=form,
                         centrale=centrale,
                         action='nouveau',
                         title='Nouveau Rapport Solaire')


@production_solaire.route('/rapport/<int:id>')
@login_required
def detail_rapport(id):
    """Détail d'un rapport de production solaire"""
    rapport = RapportSolaire.query.get_or_404(id)
    
    # Vérifier l'accès
    centrales_accessibles = get_accessible_centrales_solaire()
    if rapport.centrale not in centrales_accessibles:
        abort(403)
    
    return render_template('production_solaire/detail_rapport.html',
                         rapport=rapport,
                         title=f'Rapport {rapport.centrale.nom} - {rapport.mois}/{rapport.annee}')


@production_solaire.route('/rapport/<int:id>/modifier', methods=['GET', 'POST'])
@login_required
def modifier_rapport(id):
    """Modifier un rapport de production solaire"""
    rapport = RapportSolaire.query.get_or_404(id)
    
    # Vérifier l'accès
    centrales_accessibles = get_accessible_centrales_solaire()
    if rapport.centrale not in centrales_accessibles:
        abort(403)
    
    # Vérifier si le rapport peut être modifié
    if rapport.statut == 'transmis' and current_user.role != 'super_admin':
        flash('Ce rapport a déjà été transmis et ne peut plus être modifié.', 'error')
        return redirect(url_for('production_solaire.detail_rapport', id=id))
    
    form = RapportSolaireForm(obj=rapport)
    
    if form.validate_on_submit():
        # Mettre à jour le rapport
        form.populate_obj(rapport)
        
        try:
            rapport.save()
            flash('Rapport modifié avec succès.', 'success')
            return redirect(url_for('production_solaire.detail_rapport', id=id))
        except Exception as e:
            current_app.logger.error(f'Erreur lors de la modification du rapport: {e}')
            flash('Erreur lors de la modification du rapport.', 'error')
    
    return render_template('production_solaire/rapport_form.html',
                         form=form,
                         centrale=rapport.centrale,
                         rapport=rapport,
                         action='modifier',
                         title='Modifier Rapport Solaire')


@production_solaire.route('/rapport/<int:id>/supprimer', methods=['POST'])
@login_required
def supprimer_rapport(id):
    """Supprimer un rapport de production solaire"""
    rapport = RapportSolaire.query.get_or_404(id)
    
    # Vérifier l'accès
    centrales_accessibles = get_accessible_centrales_solaire()
    if rapport.centrale not in centrales_accessibles:
        abort(403)
    
    # Vérifier les permissions
    if rapport.statut == 'transmis' and current_user.role != 'super_admin':
        flash('Ce rapport a déjà été transmis et ne peut pas être supprimé.', 'error')
        return redirect(url_for('production_solaire.detail_rapport', id=id))
    
    try:
        rapport.delete()
        flash('Rapport supprimé avec succès.', 'success')
    except Exception as e:
        current_app.logger.error(f'Erreur lors de la suppression du rapport: {e}')
        flash('Erreur lors de la suppression du rapport.', 'error')
    
    return redirect(url_for('production_solaire.index'))


@production_solaire.route('/centrales')
@login_required
def liste_centrales():
    """Liste des centrales solaires"""
    centrales = get_accessible_centrales_solaire()
    
    return render_template('production_solaire/liste_centrales.html',
                         centrales=centrales,
                         title='Centrales Solaires')


@production_solaire.route('/centrale/nouvelle', methods=['GET', 'POST'])
@login_required
def nouvelle_centrale():
    """Nouvelle centrale solaire"""
    if current_user.role != 'super_admin':
        flash('Accès refusé. Seuls les super administrateurs peuvent créer des centrales.', 'error')
        return redirect(url_for('production_solaire.liste_centrales'))
    
    form = CentraleSolaireForm()
    operateurs = Operateur.query.filter_by(actif=True).all()
    
    if form.validate_on_submit():
        # Vérifier l'unicité du code
        centrale_existante = CentraleSolaire.query.filter_by(code=form.code.data).first()
        if centrale_existante:
            flash('Une centrale avec ce code existe déjà.', 'error')
            return render_template('production_solaire/centrale_form.html',
                                 form=form,
                                 operateurs=operateurs,
                                 action='nouvelle',
                                 title='Nouvelle Centrale Solaire')
        
        # Créer la nouvelle centrale
        centrale = CentraleSolaire(
            operateur_id=form.operateur_id.data,
            nom=form.nom.data,
            code=form.code.data,
            localisation=form.localisation.data,
            province=form.province.data,
            puissance_installee=form.puissance_installee.data,
            puissance_disponible=form.puissance_disponible.data,
            type_centrale=form.type_centrale.data,
            technologie_modules=form.technologie_modules.data,
            latitude=form.latitude.data,
            longitude=form.longitude.data,
            altitude=form.altitude.data,
            orientation_azimut=form.orientation_azimut.data,
            inclinaison_modules=form.inclinaison_modules.data,
            nombre_modules=form.nombre_modules.data,
            puissance_unitaire_module=form.puissance_unitaire_module.data,
            marque_modules=form.marque_modules.data,
            modele_modules=form.modele_modules.data,
            technologie_cellules=form.technologie_cellules.data,
            nombre_onduleurs=form.nombre_onduleurs.data,
            puissance_unitaire_onduleur=form.puissance_unitaire_onduleur.data,
            marque_onduleurs=form.marque_onduleurs.data,
            type_onduleur=form.type_onduleur.data,
            rendement_onduleur=form.rendement_onduleur.data,
            stockage_batterie=form.stockage_batterie.data,
            capacite_stockage=form.capacite_stockage.data,
            type_batterie=form.type_batterie.data,
            nombre_batteries=form.nombre_batteries.data,
            marque_batteries=form.marque_batteries.data,
            systeme_suivi=form.systeme_suivi.data,
            type_suivi=form.type_suivi.data,
            precision_suivi=form.precision_suivi.data,
            niveau_tension=form.niveau_tension.data,
            tension_evacuation=form.tension_evacuation.data,
            nombre_transformateurs=form.nombre_transformateurs.data,
            puissance_transformateurs=form.puissance_transformateurs.data,
            irradiation_annuelle_estimee=form.irradiation_annuelle_estimee.data,
            temperature_fonctionnement_nominale=form.temperature_fonctionnement_nominale.data,
            coefficient_temperature=form.coefficient_temperature.data,
            facteur_degradation_annuelle=form.facteur_degradation_annuelle.data,
            systeme_monitoring=form.systeme_monitoring.data,
            fournisseur_monitoring=form.fournisseur_monitoring.data,
            precision_mesure=form.precision_mesure.data,
            statut=form.statut.data,
            mode_fonctionnement=form.mode_fonctionnement.data,
            superficie_totale=form.superficie_totale.data,
            description=form.description.data,
            date_mise_service=form.date_mise_service.data,
            date_derniere_revision=form.date_derniere_revision.data,
            prochaine_maintenance=form.prochaine_maintenance.data,
            constructeur=form.constructeur.data,
            installateur=form.installateur.data,
            annee_construction=form.annee_construction.data,
            duree_vie_estimee=form.duree_vie_estimee.data,
            garantie_modules=form.garantie_modules.data,
            garantie_onduleurs=form.garantie_onduleurs.data,
            observations=form.observations.data
        )
        
        try:
            centrale.save()
            flash('Centrale créée avec succès.', 'success')
            return redirect(url_for('production_solaire.detail_centrale', id=centrale.id))
        except Exception as e:
            current_app.logger.error(f'Erreur lors de la création de la centrale: {e}')
            flash('Erreur lors de la création de la centrale.', 'error')
    
    return render_template('production_solaire/centrale_form.html',
                         form=form,
                         operateurs=operateurs,
                         action='nouvelle',
                         title='Nouvelle Centrale Solaire')


@production_solaire.route('/centrale/<int:id>')
@login_required
def detail_centrale(id):
    """Détail d'une centrale solaire"""
    centrale = CentraleSolaire.query.get_or_404(id)
    
    # Vérifier l'accès
    centrales_accessibles = get_accessible_centrales_solaire()
    if centrale not in centrales_accessibles:
        abort(403)
    
    # Derniers rapports
    derniers_rapports = RapportSolaire.query.filter_by(centrale_id=id)\
        .order_by(RapportSolaire.periode_debut.desc()).limit(5).all()
    
    # Statistiques de production
    stats = {
        'total_rapports': RapportSolaire.query.filter_by(centrale_id=id).count(),
        'energie_totale': db.session.query(func.sum(RapportSolaire.energie_produite))\
            .filter_by(centrale_id=id).scalar() or 0,
        'performance_ratio_moyen': db.session.query(func.avg(RapportSolaire.performance_ratio))\
            .filter_by(centrale_id=id).scalar() or 0,
        'derniere_maintenance': centrale.date_derniere_revision
    }
    
    return render_template('production_solaire/detail_centrale.html',
                         centrale=centrale,
                         derniers_rapports=derniers_rapports,
                         stats=stats,
                         title=f'Centrale {centrale.nom}')


@production_solaire.route('/api/stats')
@login_required
def api_stats():
    """API pour les statistiques de production solaire"""
    centrales_accessibles = get_accessible_centrales_solaire()
    centrale_ids = [c.id for c in centrales_accessibles]
    
    if not centrale_ids:
        return jsonify({
            'total_centrales': 0,
            'energie_totale': 0,
            'production_mensuelle': [],
            'repartition_technologie': []
        })
    
    # Production mensuelle des 12 derniers mois
    production_mensuelle = db.session.query(
        RapportSolaire.mois,
        func.sum(RapportSolaire.energie_produite).label('production')
    ).filter(
        RapportSolaire.centrale_id.in_(centrale_ids),
        RapportSolaire.annee == datetime.now().year
    ).group_by(RapportSolaire.mois).all()
    
    # Répartition par technologie
    repartition_technologie = db.session.query(
        CentraleSolaire.technologie_modules,
        func.sum(RapportSolaire.energie_produite).label('production')
    ).join(
        RapportSolaire
    ).filter(
        CentraleSolaire.id.in_(centrale_ids)
    ).group_by(CentraleSolaire.technologie_modules).all()
    
    return jsonify({
        'total_centrales': len(centrales_accessibles),
        'energie_totale': db.session.query(func.sum(RapportSolaire.energie_produite))\
            .filter(RapportSolaire.centrale_id.in_(centrale_ids)).scalar() or 0,
        'production_mensuelle': [
            {'mois': p.mois, 'production': float(p.production or 0)}
            for p in production_mensuelle
        ],
        'repartition_technologie': [
            {'technologie': r.technologie_modules or 'Non défini', 'production': float(r.production or 0)}
            for r in repartition_technologie
        ]
    })