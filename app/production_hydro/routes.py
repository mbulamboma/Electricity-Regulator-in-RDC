"""
Routes pour la production hydroélectrique
"""
from flask import render_template, redirect, url_for, flash, request, abort, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, date
from sqlalchemy import extract, func, and_
from app.production_hydro import production_hydro
from app.production_hydro.forms import (
    RapportHydroForm, CentraleHydroForm, FiltreRapportForm,
    GroupeProductionForm, TransformateurRapportForm
)
from app.models.production_hydro import (
    CentraleHydro, RapportHydro, GroupeProduction, 
    TransformateurRapport, DonneesMensuelles
)
from app.models.operateurs import Operateur
from app.extensions import db
from app.utils.decorators import super_admin_required, operateur_access_required
from app.utils.permissions import (
    get_accessible_operateurs, can_access_operateur, 
    filter_query_by_operateur, get_default_operateur_id
)
import calendar


def get_accessible_centrales():
    """Obtenir les centrales accessibles selon les permissions"""
    if current_user.is_admin():
        return CentraleHydro.query.filter_by(actif=True).all()
    elif current_user.operateur:
        return CentraleHydro.query.filter_by(
            operateur_id=current_user.operateur.id,
            actif=True
        ).all()
    return []


@production_hydro.route('/')
@login_required
def index():
    """Liste des rapports de production hydroélectrique"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Obtenir les centrales accessibles
    centrales_accessibles = get_accessible_centrales()
    if not centrales_accessibles:
        flash('Aucune centrale hydroélectrique accessible.', 'warning')
        return render_template('production_hydro/no_access.html')
    
    # IDs des centrales accessibles
    centrale_ids = [c.id for c in centrales_accessibles]
    
    # Formulaire de filtrage
    filtre_form = FiltreRapportForm()
    filtre_form.populate_centrales(centrales_accessibles)
    
    # Obtenir les années disponibles
    annees = db.session.query(RapportHydro.annee).filter(
        RapportHydro.centrale_id.in_(centrale_ids)
    ).distinct().all()
    filtre_form.populate_annees([a[0] for a in annees])
    
    # Construction de la requête
    query = RapportHydro.query.filter(RapportHydro.centrale_id.in_(centrale_ids))
    
    # Application des filtres
    if filtre_form.centrale_id.data:
        query = query.filter(RapportHydro.centrale_id == filtre_form.centrale_id.data)
    
    if filtre_form.annee.data:
        query = query.filter(RapportHydro.annee == int(filtre_form.annee.data))
    
    if filtre_form.mois.data:
        query = query.filter(RapportHydro.mois == int(filtre_form.mois.data))
    
    if filtre_form.statut.data:
        query = query.filter(RapportHydro.statut == filtre_form.statut.data)
    
    # Recherche textuelle
    search = request.args.get('search', '', type=str)
    if search:
        query = query.join(CentraleHydro).filter(
            CentraleHydro.nom.contains(search)
        )
    
    # Pagination avec jointure correcte
    rapports = query.join(CentraleHydro).order_by(
        RapportHydro.annee.desc(),
        RapportHydro.mois.desc(),
        CentraleHydro.nom
    ).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Statistiques rapides
    stats = {
        'total_rapports': query.count(),
        'rapports_brouillon': query.filter(RapportHydro.statut == 'brouillon').count(),
        'rapports_valides': query.filter(RapportHydro.statut == 'valide').count(),
        'rapports_transmis': query.filter(RapportHydro.statut == 'transmis').count(),
        'nombre_centrales': len(centrales_accessibles)
    }
    
    return render_template('production_hydro/index.html',
                         title='Rapports Production Hydroélectrique',
                         rapports=rapports,
                         filtre_form=filtre_form,
                         stats=stats,
                         search=search)


@production_hydro.route('/nouveau', methods=['GET', 'POST'])
@login_required
def nouveau():
    """Créer un nouveau rapport"""
    centrales_accessibles = get_accessible_centrales()
    if not centrales_accessibles:
        flash('Aucune centrale hydroélectrique accessible pour créer un rapport.', 'error')
        return redirect(url_for('production_hydro.index'))
    
    form = RapportHydroForm()
    form.populate_centrales(centrales_accessibles)
    
    if form.validate_on_submit():
        try:
            # Vérifier qu'un rapport n'existe pas déjà pour cette période
            existing = RapportHydro.query.filter_by(
                centrale_id=form.centrale_id.data,
                annee=form.annee.data,
                mois=form.mois.data
            ).first()
            
            if existing:
                flash('Un rapport existe déjà pour cette centrale et cette période.', 'error')
                return render_template('production_hydro/form.html',
                                     title='Nouveau Rapport',
                                     form=form,
                                     centrales=centrales_accessibles)
            
            # Créer le rapport
            rapport = RapportHydro(
                centrale_id=form.centrale_id.data,
                annee=form.annee.data,
                mois=form.mois.data,
                periode_debut=form.periode_debut.data,
                periode_fin=form.periode_fin.data,
                niveau_retenue_moyen=form.niveau_retenue_moyen.data,
                niveau_retenue_min=form.niveau_retenue_min.data,
                niveau_retenue_max=form.niveau_retenue_max.data,
                debit_moyen=form.debit_moyen.data,
                debit_min=form.debit_min.data,
                debit_max=form.debit_max.data,
                volume_turbiné=form.volume_turbiné.data,
                energie_produite=form.energie_produite.data,
                energie_disponible=form.energie_disponible.data,
                facteur_charge=form.facteur_charge.data,
                temps_fonctionnement=form.temps_fonctionnement.data,
                nombre_arrets=form.nombre_arrets.data,
                duree_arrets=form.duree_arrets.data,
                rendement_global=form.rendement_global.data,
                rendement_turbine=form.rendement_turbine.data,
                rendement_alternateur=form.rendement_alternateur.data,
                maintenances_preventives=form.maintenances_preventives.data,
                maintenances_correctives=form.maintenances_correctives.data,
                incidents_majeurs=form.incidents_majeurs.data,
                description_incidents=form.description_incidents.data,
                debit_reserve=form.debit_reserve.data,
                impact_environnemental=form.impact_environnemental.data,
                statut=form.statut.data,
                observations=form.observations.data
            )
            
            # Gérer la validation directe
            if 'submit_validate' in request.form and form.statut.data == 'brouillon':
                rapport.statut = 'valide'
                rapport.date_validation = datetime.utcnow()
                rapport.validé_par = f"{current_user.prenom or ''} {current_user.nom or current_user.username}".strip()
            
            rapport.save()
            
            # Sauvegarder les groupes de production
            for groupe_form in form.groupes_production:
                if groupe_form.numero_groupe.data and not groupe_form.delete.data:
                    groupe = GroupeProduction(
                        rapport_id=rapport.id,
                        numero_groupe=groupe_form.numero_groupe.data,
                        nom_groupe=groupe_form.nom_groupe.data,
                        puissance_nominale=groupe_form.puissance_nominale.data,
                        tension_nominale=groupe_form.tension_nominale.data,
                        vitesse_rotation=groupe_form.vitesse_rotation.data,
                        type_turbine=groupe_form.type_turbine.data,
                        heures_fonctionnement=groupe_form.heures_fonctionnement.data,
                        energie_produite=groupe_form.energie_produite.data,
                        puissance_moyenne=groupe_form.puissance_moyenne.data,
                        puissance_max=groupe_form.puissance_max.data,
                        nombre_arrets_programme=groupe_form.nombre_arrets_programme.data,
                        nombre_arrets_force=groupe_form.nombre_arrets_force.data,
                        duree_arrets_programme=groupe_form.duree_arrets_programme.data,
                        duree_arrets_force=groupe_form.duree_arrets_force.data,
                        rendement_moyen=groupe_form.rendement_moyen.data,
                        date_derniere_revision=groupe_form.date_derniere_revision.data,
                        type_derniere_revision=groupe_form.type_derniere_revision.data,
                        prochaine_revision=groupe_form.prochaine_revision.data,
                        incidents=groupe_form.incidents.data,
                        travaux_realises=groupe_form.travaux_realises.data,
                        observations=groupe_form.observations.data
                    )
                    groupe.save()
            
            # Sauvegarder les transformateurs
            for transfo_form in form.transformateurs:
                if transfo_form.numero_transformateur.data and not transfo_form.delete.data:
                    transfo = TransformateurRapport(
                        rapport_id=rapport.id,
                        numero_transformateur=transfo_form.numero_transformateur.data,
                        nom_transformateur=transfo_form.nom_transformateur.data,
                        puissance_nominale=transfo_form.puissance_nominale.data,
                        tension_primaire=transfo_form.tension_primaire.data,
                        tension_secondaire=transfo_form.tension_secondaire.data,
                        type_refroidissement=transfo_form.type_refroidissement.data,
                        energie_transferee=transfo_form.energie_transferee.data,
                        heures_service=transfo_form.heures_service.data,
                        charge_moyenne=transfo_form.charge_moyenne.data,
                        charge_max=transfo_form.charge_max.data,
                        temperature_huile_moyenne=transfo_form.temperature_huile_moyenne.data,
                        temperature_huile_max=transfo_form.temperature_huile_max.data,
                        temperature_enroulements_max=transfo_form.temperature_enroulements_max.data,
                        etat_general=transfo_form.etat_general.data,
                        date_derniere_maintenance=transfo_form.date_derniere_maintenance.data,
                        type_maintenance=transfo_form.type_maintenance.data,
                        prochaine_maintenance=transfo_form.prochaine_maintenance.data,
                        incidents=transfo_form.incidents.data,
                        travaux_realises=transfo_form.travaux_realises.data,
                        observations=transfo_form.observations.data
                    )
                    transfo.save()
            
            flash('Rapport créé avec succès!', 'success')
            return redirect(url_for('production_hydro.details', id=rapport.id))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erreur création rapport: {e}")
            flash('Erreur lors de la création du rapport.', 'error')
    
    return render_template('production_hydro/form.html',
                         title='Nouveau Rapport',
                         form=form,
                         centrales=centrales_accessibles)


@production_hydro.route('/<int:id>')
@login_required
def details(id):
    """Afficher les détails d'un rapport"""
    rapport = RapportHydro.query.get_or_404(id)
    
    # Vérifier les permissions
    if not current_user.is_admin():
        if not current_user.operateur or current_user.operateur.id != rapport.centrale.operateur_id:
            abort(403)
    
    # Calculer des statistiques
    stats = {
        'total_groupes': len(rapport.groupes_production),
        'groupes_actifs': len([g for g in rapport.groupes_production if g.heures_fonctionnement and g.heures_fonctionnement > 0]),
        'total_transformateurs': len(rapport.transformateurs),
        'energie_totale_groupes': sum([g.energie_produite or 0 for g in rapport.groupes_production]),
        'puissance_totale_installee': sum([g.puissance_nominale or 0 for g in rapport.groupes_production]),
        'disponibilite_moyenne': rapport.calcul_disponibilite()
    }
    
    return render_template('production_hydro/details.html',
                         title=f'Rapport {rapport.centrale.nom} - {rapport.get_periode_str()}',
                         rapport=rapport,
                         stats=stats)


@production_hydro.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Modifier un rapport"""
    rapport = RapportHydro.query.get_or_404(id)
    
    # Vérifier les permissions
    if not current_user.is_admin():
        if not current_user.operateur or current_user.operateur.id != rapport.centrale.operateur_id:
            abort(403)
    
    # Vérifier que le rapport peut être modifié
    if rapport.statut == 'transmis' and not current_user.is_admin():
        flash('Ce rapport a été transmis et ne peut plus être modifié.', 'error')
        return redirect(url_for('production_hydro.details', id=id))
    
    centrales_accessibles = get_accessible_centrales()
    
    form = RapportHydroForm(obj=rapport)
    form.populate_centrales(centrales_accessibles)
    
    # Pré-remplir les sous-formulaires
    if request.method == 'GET':
        # Créer des dictionnaires de données pour pré-remplir le formulaire
        form_data = {}
        
        # Données des groupes de production
        for i, groupe in enumerate(rapport.groupes_production):
            form_data[f'groupes_production-{i}-id'] = str(groupe.id)
            form_data[f'groupes_production-{i}-delete'] = ''
            form_data[f'groupes_production-{i}-numero_groupe'] = groupe.numero_groupe or ''
            form_data[f'groupes_production-{i}-nom_groupe'] = groupe.nom_groupe or ''
            form_data[f'groupes_production-{i}-puissance_nominale'] = str(groupe.puissance_nominale) if groupe.puissance_nominale else ''
            form_data[f'groupes_production-{i}-tension_nominale'] = str(groupe.tension_nominale) if groupe.tension_nominale else ''
            form_data[f'groupes_production-{i}-vitesse_rotation'] = str(groupe.vitesse_rotation) if groupe.vitesse_rotation else ''
            form_data[f'groupes_production-{i}-type_turbine'] = groupe.type_turbine or ''
            form_data[f'groupes_production-{i}-heures_fonctionnement'] = str(groupe.heures_fonctionnement) if groupe.heures_fonctionnement else ''
            form_data[f'groupes_production-{i}-energie_produite'] = str(groupe.energie_produite) if groupe.energie_produite else ''
            form_data[f'groupes_production-{i}-puissance_moyenne'] = str(groupe.puissance_moyenne) if groupe.puissance_moyenne else ''
            form_data[f'groupes_production-{i}-puissance_max'] = str(groupe.puissance_max) if groupe.puissance_max else ''
            form_data[f'groupes_production-{i}-nombre_arrets_programme'] = str(groupe.nombre_arrets_programme or 0)
            form_data[f'groupes_production-{i}-nombre_arrets_force'] = str(groupe.nombre_arrets_force or 0)
            form_data[f'groupes_production-{i}-duree_arrets_programme'] = str(groupe.duree_arrets_programme or 0.0)
            form_data[f'groupes_production-{i}-duree_arrets_force'] = str(groupe.duree_arrets_force or 0.0)
            form_data[f'groupes_production-{i}-rendement_moyen'] = str(groupe.rendement_moyen) if groupe.rendement_moyen else ''
            form_data[f'groupes_production-{i}-incidents'] = groupe.incidents or ''
            form_data[f'groupes_production-{i}-travaux_realises'] = groupe.travaux_realises or ''
            form_data[f'groupes_production-{i}-observations'] = groupe.observations or ''
            
        # Données des transformateurs
        for i, transfo in enumerate(rapport.transformateurs):
            form_data[f'transformateurs-{i}-id'] = str(transfo.id)
            form_data[f'transformateurs-{i}-delete'] = ''
            form_data[f'transformateurs-{i}-numero_transformateur'] = transfo.numero_transformateur or ''
            form_data[f'transformateurs-{i}-nom_transformateur'] = transfo.nom_transformateur or ''
            form_data[f'transformateurs-{i}-puissance_nominale'] = str(transfo.puissance_nominale) if transfo.puissance_nominale else ''
            form_data[f'transformateurs-{i}-type_refroidissement'] = transfo.type_refroidissement or ''
            form_data[f'transformateurs-{i}-tension_primaire'] = str(transfo.tension_primaire) if transfo.tension_primaire else ''
            form_data[f'transformateurs-{i}-tension_secondaire'] = str(transfo.tension_secondaire) if transfo.tension_secondaire else ''
            form_data[f'transformateurs-{i}-etat_general'] = transfo.etat_general or 'bon'
            form_data[f'transformateurs-{i}-incidents'] = transfo.incidents or ''
            form_data[f'transformateurs-{i}-observations'] = transfo.observations or ''
        
        # Recréer le formulaire avec les données existantes
        from werkzeug.datastructures import MultiDict
        form = RapportHydroForm(MultiDict(form_data), obj=rapport)
        form.populate_centrales(centrales_accessibles)
    
    if form.validate_on_submit():
        try:
            # Mettre à jour le rapport principal
            form.populate_obj(rapport)
            
            # Gérer la validation
            if 'submit_validate' in request.form and rapport.statut == 'brouillon':
                rapport.statut = 'valide'
                rapport.date_validation = datetime.utcnow()
                rapport.validé_par = f"{current_user.prenom or ''} {current_user.nom or current_user.username}".strip()
            
            rapport.date_modification = datetime.utcnow()
            
            # Mettre à jour les groupes de production
            # Supprimer les groupes marqués pour suppression
            for groupe_form in form.groupes_production:
                if groupe_form.delete.data == 'true' and groupe_form.id.data:
                    groupe = GroupeProduction.query.get(groupe_form.id.data)
                    if groupe and groupe.rapport_id == rapport.id:
                        db.session.delete(groupe)
            
            # Mettre à jour ou créer les groupes
            for groupe_form in form.groupes_production:
                if groupe_form.numero_groupe.data and groupe_form.delete.data != 'true':
                    if groupe_form.id.data:
                        # Mise à jour
                        groupe = GroupeProduction.query.get(groupe_form.id.data)
                        if groupe and groupe.rapport_id == rapport.id:
                            groupe_form.populate_obj(groupe)
                            groupe.date_modification = datetime.utcnow()
                    else:
                        # Création
                        groupe = GroupeProduction(rapport_id=rapport.id)
                        groupe_form.populate_obj(groupe)
                        groupe.save()
            
            # Même logique pour les transformateurs
            for transfo_form in form.transformateurs:
                if transfo_form.delete.data == 'true' and transfo_form.id.data:
                    transfo = TransformateurRapport.query.get(transfo_form.id.data)
                    if transfo and transfo.rapport_id == rapport.id:
                        db.session.delete(transfo)
            
            for transfo_form in form.transformateurs:
                if transfo_form.numero_transformateur.data and transfo_form.delete.data != 'true':
                    if transfo_form.id.data:
                        # Mise à jour
                        transfo = TransformateurRapport.query.get(transfo_form.id.data)
                        if transfo and transfo.rapport_id == rapport.id:
                            transfo_form.populate_obj(transfo)
                            transfo.date_modification = datetime.utcnow()
                    else:
                        # Création
                        transfo = TransformateurRapport(rapport_id=rapport.id)
                        transfo_form.populate_obj(transfo)
                        transfo.save()
            
            db.session.commit()
            flash('Rapport mis à jour avec succès!', 'success')
            return redirect(url_for('production_hydro.details', id=rapport.id))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erreur modification rapport: {e}")
            flash('Erreur lors de la modification du rapport.', 'error')
    
    return render_template('production_hydro/form.html',
                         title=f'Modifier Rapport - {rapport.centrale.nom}',
                         form=form,
                         centrales=centrales_accessibles,
                         rapport=rapport,
                         edit_mode=True)


@production_hydro.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """Supprimer un rapport"""
    rapport = RapportHydro.query.get_or_404(id)
    
    # Vérifier les permissions (seuls les super admins peuvent supprimer)
    if not current_user.is_admin():
        abort(403)
    
    try:
        centrale_nom = rapport.centrale.nom
        periode = rapport.get_periode_str()
        
        # La suppression en cascade se charge des sous-éléments
        db.session.delete(rapport)
        db.session.commit()
        
        flash(f'Rapport {centrale_nom} - {periode} supprimé avec succès.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erreur suppression rapport: {e}")
        flash('Erreur lors de la suppression du rapport.', 'error')
    
    return redirect(url_for('production_hydro.index'))


@production_hydro.route('/centrales')
@login_required
def centrales():
    """Gestion des centrales hydroélectriques"""
    centrales_accessibles = get_accessible_centrales()
    
    # Statistiques par centrale
    centrales_stats = []
    for centrale in centrales_accessibles:
        stats = {
            'centrale': centrale,
            'nb_rapports': len(centrale.rapports),
            'derniere_periode': None,
            'energie_totale': 0
        }
        
        if centrale.rapports:
            dernier_rapport = max(centrale.rapports, key=lambda r: (r.annee, r.mois))
            stats['derniere_periode'] = dernier_rapport.get_periode_str()
            stats['energie_totale'] = sum([r.energie_produite or 0 for r in centrale.rapports])
        
        centrales_stats.append(stats)
    
    return render_template('production_hydro/centrales.html',
                         title='Centrales Hydroélectriques',
                         centrales_stats=centrales_stats)


@production_hydro.route('/centrales/nouvelle', methods=['GET', 'POST'])
@login_required
@super_admin_required
def nouvelle_centrale():
    """Créer une nouvelle centrale (super admin seulement)"""
    form = CentraleHydroForm()
    
    # Peupler la liste des opérateurs
    operateurs = Operateur.query.filter_by(actif=True).all()
    
    if form.validate_on_submit():
        try:
            centrale = CentraleHydro(
                operateur_id=request.form.get('operateur_id'),  # À ajouter au formulaire
                nom=form.nom.data,
                code=form.code.data,
                localisation=form.localisation.data,
                province=form.province.data,
                cours_eau=form.cours_eau.data,
                puissance_installee=form.puissance_installee.data,
                puissance_disponible=form.puissance_disponible.data,
                hauteur_chute=form.hauteur_chute.data,
                debit_equipement=form.debit_equipement.data,
                type_centrale=form.type_centrale.data,
                nombre_groupes=form.nombre_groupes.data,
                nombre_transformateurs=form.nombre_transformateurs.data,
                tension_evacuation=form.tension_evacuation.data,
                date_mise_service=form.date_mise_service.data,
                date_derniere_revision=form.date_derniere_revision.data,
                constructeur=form.constructeur.data,
                annee_construction=form.annee_construction.data,
                observations=form.observations.data
            )
            
            centrale.save()
            flash('Centrale créée avec succès!', 'success')
            return redirect(url_for('production_hydro.centrales'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erreur création centrale: {e}")
            flash('Erreur lors de la création de la centrale.', 'error')
    
    return render_template('production_hydro/centrale_form.html',
                         title='Nouvelle Centrale',
                         form=form,
                         operateurs=operateurs)


# Routes API pour les formulaires dynamiques
@production_hydro.route('/api/centrale/<int:centrale_id>/info')
@login_required
def api_centrale_info(centrale_id):
    """API: Informations sur une centrale"""
    centrale = CentraleHydro.query.get_or_404(centrale_id)
    
    # Vérifier les permissions
    if not current_user.is_admin():
        if not current_user.operateur or current_user.operateur.id != centrale.operateur_id:
            abort(403)
    
    return jsonify({
        'success': True,
        'centrale': {
            'id': centrale.id,
            'nom': centrale.nom,
            'code': centrale.code,
            'puissance_installee': centrale.puissance_installee,
            'nombre_groupes': centrale.nombre_groupes,
            'nombre_transformateurs': centrale.nombre_transformateurs,
            'type_centrale': centrale.type_centrale
        }
    })


@production_hydro.route('/api/calculs/facteur-charge', methods=['POST'])
@login_required
def api_calcul_facteur_charge():
    """API: Calculer le facteur de charge"""
    data = request.get_json()
    
    try:
        energie_produite = float(data.get('energie_produite', 0))
        puissance_nominale = float(data.get('puissance_nominale', 0))
        heures_fonctionnement = float(data.get('heures_fonctionnement', 0))
        
        if puissance_nominale > 0 and heures_fonctionnement > 0:
            energie_theorique = puissance_nominale * heures_fonctionnement
            facteur_charge = (energie_produite / energie_theorique) * 100
            facteur_charge = min(100, max(0, facteur_charge))  # Limiter entre 0 et 100
        else:
            facteur_charge = 0
        
        return jsonify({
            'success': True,
            'facteur_charge': round(facteur_charge, 2)
        })
    
    except (ValueError, TypeError):
        return jsonify({
            'success': False,
            'error': 'Données invalides'
        }), 400


@production_hydro.route('/api/calculs/disponibilite', methods=['POST'])
@login_required
def api_calcul_disponibilite():
    """API: Calculer la disponibilité"""
    data = request.get_json()
    
    try:
        duree_arrets_programme = float(data.get('duree_arrets_programme', 0))
        duree_arrets_force = float(data.get('duree_arrets_force', 0))
        heures_periode = float(data.get('heures_periode', 24 * 30))  # Par défaut 30 jours
        
        heures_indisponibles = duree_arrets_programme + duree_arrets_force
        
        if heures_periode > 0:
            disponibilite = ((heures_periode - heures_indisponibles) / heures_periode) * 100
            disponibilite = min(100, max(0, disponibilite))
        else:
            disponibilite = 0
        
        return jsonify({
            'success': True,
            'disponibilite': round(disponibilite, 2)
        })
    
    except (ValueError, TypeError):
        return jsonify({
            'success': False,
            'error': 'Données invalides'
        }), 400