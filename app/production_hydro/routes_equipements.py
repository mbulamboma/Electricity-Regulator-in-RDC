"""
Routes pour la gestion des équipements (groupes de production et transformateurs)
"""
from flask import render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_required, current_user
from app.production_hydro import production_hydro
from app.production_hydro.forms import (
    GroupeProductionSimpleForm, TransformateurSimpleForm
)
from app.models.production_hydro import (
    CentraleHydro, GroupeProduction, TransformateurRapport
)
from app.extensions import db
from app.utils.permissions import can_access_operateur


# Routes pour la gestion des équipements
@production_hydro.route('/centrale/<int:centrale_id>/groupe/nouveau', methods=['GET', 'POST'])
@login_required
def nouveau_groupe(centrale_id):
    """Ajouter un nouveau groupe de production à une centrale"""
    centrale = CentraleHydro.query.get_or_404(centrale_id)

    # Vérifier les permissions
    if not current_user.is_admin():
        if not current_user.operateur or current_user.operateur.id != centrale.operateur_id:
            abort(403)

    form = GroupeProductionSimpleForm()

    if form.validate_on_submit():
        # Vérifier l'unicité du numéro de groupe au sein de la centrale
        existing_groupe = GroupeProduction.query.filter_by(
            centrale_id=centrale.id,
            numero_groupe=form.numero_groupe.data,
            actif=True
        ).first()

        if existing_groupe:
            form.numero_groupe.errors.append('Un groupe avec ce numéro existe déjà dans cette centrale.')
        else:
            try:
                groupe = GroupeProduction(
                    centrale_id=centrale.id,
                    numero_groupe=form.numero_groupe.data,
                    nom_groupe=form.nom_groupe.data,
                    puissance_nominale=form.puissance_nominale.data,
                    tension_nominale=form.tension_nominale.data,
                    vitesse_rotation=form.vitesse_rotation.data,
                    type_turbine=form.type_turbine.data
                )
                groupe.save()

                flash('Groupe de production ajouté avec succès!', 'success')
                return redirect(url_for('production_hydro.detail_centrale', centrale_id=centrale.id))

            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Erreur création groupe: {type(e).__name__}: {e}")
                flash('Erreur lors de l\'ajout du groupe de production.', 'error')

    return render_template('production_hydro/groupe_form.html',
                         title=f'Nouveau Groupe - {centrale.nom}',
                         form=form,
                         centrale=centrale)


@production_hydro.route('/centrale/<int:centrale_id>/transformateur/nouveau', methods=['GET', 'POST'])
@login_required
def nouveau_transformateur(centrale_id):
    """Ajouter un nouveau transformateur à une centrale"""
    centrale = CentraleHydro.query.get_or_404(centrale_id)

    # Vérifier les permissions
    if not current_user.is_admin():
        if not current_user.operateur or current_user.operateur.id != centrale.operateur_id:
            abort(403)

    form = TransformateurSimpleForm()

    if form.validate_on_submit():
        # Vérifier l'unicité du numéro de transformateur au sein de la centrale
        existing_transformateur = TransformateurRapport.query.filter_by(
            centrale_id=centrale.id,
            numero_transformateur=form.numero_transformateur.data,
            actif=True
        ).first()

        if existing_transformateur:
            form.numero_transformateur.errors.append('Un transformateur avec ce numéro existe déjà dans cette centrale.')
        else:
            try:
                transformateur = TransformateurRapport(
                    centrale_id=centrale.id,
                    numero_transformateur=form.numero_transformateur.data,
                    nom_transformateur=form.nom_transformateur.data,
                    puissance_nominale=form.puissance_nominale.data,
                    tension_primaire=form.tension_primaire.data,
                    tension_secondaire=form.tension_secondaire.data,
                    type_refroidissement=form.type_refroidissement.data
                )
                transformateur.save()

                flash('Transformateur ajouté avec succès!', 'success')
                return redirect(url_for('production_hydro.detail_centrale', centrale_id=centrale.id))

            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Erreur création transformateur: {type(e).__name__}: {e}")
                flash('Erreur lors de l\'ajout du transformateur.', 'error')

    return render_template('production_hydro/transformateur_form.html',
                         title=f'Nouveau Transformateur - {centrale.nom}',
                         form=form,
                         centrale=centrale)


@production_hydro.route('/groupe/<int:groupe_id>/modifier', methods=['GET', 'POST'])
@login_required
def modifier_groupe(groupe_id):
    """Modifier un groupe de production"""
    groupe = GroupeProduction.query.get_or_404(groupe_id)
    centrale = groupe.centrale

    # Vérifier les permissions
    if not current_user.is_admin():
        if not current_user.operateur or current_user.operateur.id != centrale.operateur_id:
            abort(403)

    form = GroupeProductionSimpleForm(obj=groupe)

    if form.validate_on_submit():
        # Vérifier l'unicité du numéro de groupe au sein de la centrale (en excluant le groupe actuel)
        existing_groupe = GroupeProduction.query.filter_by(
            centrale_id=centrale.id,
            numero_groupe=form.numero_groupe.data,
            actif=True
        ).filter(GroupeProduction.id != groupe.id).first()

        if existing_groupe:
            form.numero_groupe.errors.append('Un groupe avec ce numéro existe déjà dans cette centrale.')
        else:
            try:
                form.populate_obj(groupe)
                groupe.save()

                flash('Groupe de production modifié avec succès!', 'success')
                return redirect(url_for('production_hydro.detail_centrale', centrale_id=centrale.id))

            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Erreur modification groupe: {type(e).__name__}: {e}")
                flash('Erreur lors de la modification du groupe.', 'error')

    return render_template('production_hydro/groupe_form.html',
                         title=f'Modifier Groupe {groupe.numero_groupe} - {centrale.nom}',
                         form=form,
                         centrale=centrale,
                         groupe=groupe)


@production_hydro.route('/transformateur/<int:transformateur_id>/modifier', methods=['GET', 'POST'])
@login_required
def modifier_transformateur(transformateur_id):
    """Modifier un transformateur"""
    transformateur = TransformateurRapport.query.get_or_404(transformateur_id)
    centrale = transformateur.centrale

    # Vérifier les permissions
    if not current_user.is_admin():
        if not current_user.operateur or current_user.operateur.id != centrale.operateur_id:
            abort(403)

    form = TransformateurSimpleForm(obj=transformateur)

    if form.validate_on_submit():
        # Vérifier l'unicité du numéro de transformateur au sein de la centrale (en excluant le transformateur actuel)
        existing_transformateur = TransformateurRapport.query.filter_by(
            centrale_id=centrale.id,
            numero_transformateur=form.numero_transformateur.data,
            actif=True
        ).filter(TransformateurRapport.id != transformateur.id).first()

        if existing_transformateur:
            form.numero_transformateur.errors.append('Un transformateur avec ce numéro existe déjà dans cette centrale.')
        else:
            try:
                form.populate_obj(transformateur)
                transformateur.save()

                flash('Transformateur modifié avec succès!', 'success')
                return redirect(url_for('production_hydro.detail_centrale', centrale_id=centrale.id))

            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Erreur modification transformateur: {type(e).__name__}: {e}")
                flash('Erreur lors de la modification du transformateur.', 'error')

    return render_template('production_hydro/transformateur_form.html',
                         title=f'Modifier Transformateur {transformateur.numero_transformateur} - {centrale.nom}',
                         form=form,
                         centrale=centrale,
                         transformateur=transformateur)


@production_hydro.route('/groupe/<int:groupe_id>/supprimer', methods=['POST', 'DELETE'])
@login_required
def supprimer_groupe(groupe_id):
    """Supprimer un groupe de production"""
    groupe = GroupeProduction.query.get_or_404(groupe_id)
    centrale = groupe.centrale

    # Vérifier les permissions
    if not current_user.is_admin():
        if not current_user.operateur or current_user.operateur.id != centrale.operateur_id:
            abort(403)

    try:
        numero_groupe = groupe.numero_groupe
        groupe.delete()
        flash(f'Groupe {numero_groupe} supprimé avec succès!', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erreur suppression groupe: {type(e).__name__}: {e}")
        flash('Erreur lors de la suppression du groupe.', 'error')

    return redirect(url_for('production_hydro.detail_centrale', centrale_id=centrale.id))


@production_hydro.route('/transformateur/<int:transformateur_id>/supprimer', methods=['POST', 'DELETE'])
@login_required
def supprimer_transformateur(transformateur_id):
    """Supprimer un transformateur"""
    transformateur = TransformateurRapport.query.get_or_404(transformateur_id)
    centrale = transformateur.centrale

    # Vérifier les permissions
    if not current_user.is_admin():
        if not current_user.operateur or current_user.operateur.id != centrale.operateur_id:
            abort(403)

    try:
        numero_transformateur = transformateur.numero_transformateur
        transformateur.delete()
        flash(f'Transformateur {numero_transformateur} supprimé avec succès!', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erreur suppression transformateur: {type(e).__name__}: {e}")
        flash('Erreur lors de la suppression du transformateur.', 'error')

    return redirect(url_for('production_hydro.detail_centrale', centrale_id=centrale.id))