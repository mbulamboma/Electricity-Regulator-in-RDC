"""
Routes pour la gestion des centrales thermiques
"""
from flask import render_template, redirect, url_for, flash, abort, current_app
from flask_login import login_required, current_user
from sqlalchemy import func
from app.production_thermique import production_thermique
from app.production_thermique.forms import CentraleThermiqueForm
from app.models.production_thermique import (
    CentraleThermique, RapportThermique
)
from app.models.operateurs import Operateur
from app.extensions import db
from app.production_thermique.utils import get_accessible_centrales_thermique


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


@production_thermique.route('/centrale/<int:id>/modifier', methods=['GET', 'POST'])
@login_required
def modifier_centrale(id):
    """Modifier une centrale thermique"""
    if current_user.role != 'super_admin':
        flash('Accès refusé. Seuls les super administrateurs peuvent modifier des centrales.', 'error')
        return redirect(url_for('production_thermique.liste_centrales'))

    centrale = CentraleThermique.query.get_or_404(id)
    form = CentraleThermiqueForm(obj=centrale)
    operateurs = Operateur.query.filter_by(actif=True).all()

    if form.validate_on_submit():
        # Vérifier l'unicité du code (sauf si c'est le même)
        if form.code.data != centrale.code:
            centrale_existante = CentraleThermique.query.filter_by(code=form.code.data).first()
            if centrale_existante:
                flash('Une centrale avec ce code existe déjà.', 'error')
                return render_template('production_thermique/centrale_form.html',
                                     form=form,
                                     operateurs=operateurs,
                                     centrale=centrale,
                                     action='modifier',
                                     title='Modifier Centrale Thermique')

        # Mettre à jour la centrale
        form.populate_obj(centrale)

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
                         centrale=centrale,
                         action='modifier',
                         title='Modifier Centrale Thermique')


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