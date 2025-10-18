"""
Routes pour la gestion des rapports de production hydroélectrique
"""
from flask import render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_required, current_user
from datetime import datetime
from sqlalchemy import extract, func
from app.production_hydro import production_hydro
from app.production_hydro.forms import RapportHydroForm, FiltreRapportForm
from app.models.production_hydro import (
    CentraleHydro, RapportHydro, GroupeProduction, 
    TransformateurRapport
)
from app.extensions import db
from app.utils.decorators import super_admin_required


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

    # Formulaire de filtrage - initialiser avec les paramètres GET
    filtre_form = FiltreRapportForm(request.args)
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
                        centrale_id=rapport.centrale_id,
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
                        centrale_id=rapport.centrale_id,
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
            # Puisque les groupes sont liés à la centrale, on met à jour les données opérationnelles
            for groupe_form in form.groupes_production:
                if groupe_form.numero_groupe.data and groupe_form.delete.data != 'true':
                    if groupe_form.id.data:
                        # Mise à jour d'un groupe existant
                        groupe = GroupeProduction.query.get(groupe_form.id.data)
                        if groupe and groupe.centrale_id == rapport.centrale_id:
                            # Mettre à jour seulement les données opérationnelles
                            groupe.heures_fonctionnement = groupe_form.heures_fonctionnement.data
                            groupe.energie_produite = groupe_form.energie_produite.data
                            groupe.puissance_moyenne = groupe_form.puissance_moyenne.data
                            groupe.puissance_max = groupe_form.puissance_max.data
                            groupe.nombre_arrets_programme = groupe_form.nombre_arrets_programme.data
                            groupe.nombre_arrets_force = groupe_form.nombre_arrets_force.data
                            groupe.duree_arrets_programme = groupe_form.duree_arrets_programme.data
                            groupe.duree_arrets_force = groupe_form.duree_arrets_force.data
                            groupe.rendement_moyen = groupe_form.rendement_moyen.data
                            groupe.incidents = groupe_form.incidents.data
                            groupe.travaux_realises = groupe_form.travaux_realises.data
                            groupe.observations = groupe_form.observations.data
                            groupe.date_modification = datetime.utcnow()
                    # Note: On ne crée pas de nouveaux groupes depuis l'édition de rapport
                    # Les groupes sont gérés séparément dans la gestion des équipements

            # Mettre à jour les transformateurs
            for transfo_form in form.transformateurs:
                if transfo_form.numero_transformateur.data and transfo_form.delete.data != 'true':
                    if transfo_form.id.data:
                        # Mise à jour d'un transformateur existant
                        transfo = TransformateurRapport.query.get(transfo_form.id.data)
                        if transfo and transfo.centrale_id == rapport.centrale_id:
                            # Mettre à jour seulement les données opérationnelles
                            transfo.energie_transferee = transfo_form.energie_transferee.data
                            transfo.heures_service = transfo_form.heures_service.data
                            transfo.nombre_arrets = transfo_form.nombre_arrets.data
                            transfo.duree_arrets = transfo_form.duree_arrets.data
                            transfo.rendement = transfo_form.rendement.data
                            transfo.temperature_moyenne = transfo_form.temperature_moyenne.data
                            transfo.incidents = transfo_form.incidents.data
                            transfo.travaux_realises = transfo_form.travaux_realises.data
                            transfo.observations = transfo_form.observations.data
                            transfo.date_modification = datetime.utcnow()
                    # Note: On ne crée pas de nouveaux transformateurs depuis l'édition de rapport

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
@super_admin_required
def delete(id):
    """Supprimer un rapport"""
    rapport = RapportHydro.query.get_or_404(id)

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