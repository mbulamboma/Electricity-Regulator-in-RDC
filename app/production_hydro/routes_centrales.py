"""
Routes pour la gestion des centrales hydroélectriques
"""
from flask import render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_required, current_user
from datetime import datetime
from app.production_hydro import production_hydro
from app.production_hydro.forms import CentraleHydroForm
from app.models.production_hydro import CentraleHydro, RapportHydro
from app.models.operateurs import Operateur
from app.extensions import db
from app.utils.decorators import super_admin_required
from app.utils.permissions import can_access_operateur


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
            # Vérifier que le code n'existe pas déjà
            existing_centrale = CentraleHydro.query.filter_by(code=form.code.data, actif=True).first()
            if existing_centrale:
                flash('Une centrale avec ce code existe déjà.', 'error')
                return render_template('production_hydro/centrale_form.html',
                                     title='Nouvelle Centrale',
                                     form=form,
                                     operateurs=operateurs)

            centrale = CentraleHydro(
                operateur_id=form.operateur_id.data,
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
                type_turbine=form.type_turbine.data,
                type_barrage=form.type_barrage.data,
                niveau_tension=form.niveau_tension.data,
                superficie_bassin=form.superficie_bassin.data,
                volume_retenue=form.volume_retenue.data,
                latitude=form.latitude.data,
                longitude=form.longitude.data,
                statut=form.statut.data,
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
            current_app.logger.info(f"Centrale créée avec ID: {centrale.id}")

            flash('Centrale créée avec succès! Vous pouvez maintenant ajouter des groupes et transformateurs.', 'success')
            return redirect(url_for('production_hydro.detail_centrale', centrale_id=centrale.id))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erreur création centrale: {type(e).__name__}: {e}")
            import traceback
            current_app.logger.error(f"Traceback: {traceback.format_exc()}")
            flash('Erreur lors de la création de la centrale.', 'error')
    else:
        # Log validation errors
        if request.method == 'POST':
            current_app.logger.error(f"Form validation failed. Errors: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'Erreur dans le champ {field}: {error}', 'error')

    return render_template('production_hydro/centrale_form.html',
                         title='Nouvelle Centrale',
                         form=form,
                         operateurs=operateurs)


@production_hydro.route('/centrales')
@login_required
def centrales():
    """Liste des centrales hydroélectriques"""
    centrales_list = CentraleHydro.query.filter_by(actif=True).all()

    return render_template('production_hydro/centrales_list.html',
                         title='Centrales Hydroélectriques',
                         centrales=centrales_list)


@production_hydro.route('/centrale/<int:centrale_id>/modifier', methods=['GET', 'POST'])
@login_required
@super_admin_required
def modifier_centrale(centrale_id):
    """Modifier une centrale existante"""
    centrale = CentraleHydro.query.get_or_404(centrale_id)

    form = CentraleHydroForm(obj=centrale)
    form.centrale_id.data = str(centrale_id)  # Définir l'ID pour la validation

    # Peupler la liste des opérateurs
    operateurs = Operateur.query.filter_by(actif=True).all()

    if form.validate_on_submit():
        try:
            form.populate_obj(centrale)
            centrale.save()

            flash('Centrale modifiée avec succès!', 'success')
            return redirect(url_for('production_hydro.centrales'))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erreur modification centrale: {type(e).__name__}: {e}")
            flash('Erreur lors de la modification de la centrale.', 'error')

    return render_template('production_hydro/centrale_form.html',
                         title=f'Modifier Centrale - {centrale.nom}',
                         form=form,
                         operateurs=operateurs)


@production_hydro.route('/centrale/<int:centrale_id>')
@login_required
def detail_centrale(centrale_id):
    """Voir les détails d'une centrale hydroélectrique"""
    centrale = CentraleHydro.query.get_or_404(centrale_id)

    # Pour les admin_operateur, vérifier qu'ils ont accès à l'opérateur de la centrale
    if current_user.role == 'admin_operateur' and not can_access_operateur(centrale.operateur_id):
        abort(403)

    # Obtenir les statistiques de la centrale
    rapports = RapportHydro.query.filter_by(centrale_id=centrale_id).all()
    nb_rapports = len(rapports)
    derniere_periode = None
    energie_totale = 0
    if rapports:
        dernier_rapport = max(rapports, key=lambda r: (r.annee, r.mois) if r.annee and r.mois else (0, 0))
        derniere_periode = f"{dernier_rapport.annee}-{dernier_rapport.mois:02d}" if dernier_rapport.annee and dernier_rapport.mois else None
        energie_totale = sum(r.energie_produite or 0 for r in rapports if r.energie_produite)

    # Obtenir les équipements directement depuis la centrale (plus depuis les rapports)
    groupes_production = centrale.groupes_production or []
    transformateurs = centrale.transformateurs or []

    return render_template('production_hydro/detail_centrale.html',
                         centrale=centrale,
                         nb_rapports=nb_rapports,
                         derniere_periode=derniere_periode,
                         energie_totale=energie_totale,
                         rapports=rapports[:5],  # Derniers 5 rapports
                         groupes_production=groupes_production,
                         transformateurs=transformateurs)


@production_hydro.route('/centrale/<int:centrale_id>/supprimer', methods=['POST', 'DELETE'])
@login_required
def supprimer_centrale(centrale_id):
    """Supprimer une centrale hydroélectrique (soft delete)"""
    # Seuls super_admin et admin_operateur peuvent supprimer
    if current_user.role not in ['super_admin', 'admin_operateur']:
        abort(403)

    centrale = CentraleHydro.query.get_or_404(centrale_id)

    # Pour les admin_operateur, vérifier qu'ils ont accès à l'opérateur de la centrale
    if current_user.role == 'admin_operateur' and not can_access_operateur(centrale.operateur_id):
        abort(403)

    # Vérifier s'il y a des rapports associés
    nb_rapports = RapportHydro.query.filter_by(centrale_id=centrale_id).count()
    if nb_rapports > 0:
        flash(f'Impossible de supprimer la centrale "{centrale.nom}" car elle contient {nb_rapports} rapport(s).', 'error')
        return redirect(url_for('production_hydro.detail_centrale', centrale_id=centrale_id))

    # Soft delete
    centrale.actif = False
    centrale.date_modification = datetime.utcnow()
    db.session.commit()

    flash(f'Centrale "{centrale.nom}" supprimée avec succès.', 'success')
    return redirect(url_for('production_hydro.centrales'))