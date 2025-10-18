"""
Routes principales pour la production thermique (rapports)
"""
import calendar
from flask import render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_required, current_user
from datetime import datetime, date
from sqlalchemy import extract, func, and_
from app.production_thermique import production_thermique
from app.production_thermique.forms import (
    RapportThermiqueForm, FiltreRapportThermiqueForm
)
from app.models.production_thermique import (
    CentraleThermique, RapportThermique
)
from app.extensions import db
from app.production_thermique.utils import get_accessible_centrales_thermique


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

    # Requête de base pour les rapports
    if centrales_accessibles:
        query = RapportThermique.query.filter(RapportThermique.centrale_id.in_(centrale_ids))
    else:
        # Si pas de centrales mais utilisateur autorisé, afficher page vide
        query = RapportThermique.query.filter(False)  # Requête qui retourne rien

    # Filtres
    filtre_form = FiltreRapportThermiqueForm()
    filtre_form.centrale_id.choices = [(None, 'Toutes les centrales')] + [
        (c.id, c.nom) for c in centrales_accessibles
    ]

    # Années disponibles
    annees = db.session.query(extract('year', RapportThermique.periode_debut).label('annee'))\
        .filter(RapportThermique.centrale_id.in_(centrale_ids))\
        .distinct().order_by('annee').all()
    filtre_form.annee.choices = [(None, 'Toutes les années')] + [(int(a.annee), str(a.annee)) for a in annees]

    if filtre_form.validate_on_submit():
        if filtre_form.centrale_id.data is not None:
            query = query.filter(RapportThermique.centrale_id == filtre_form.centrale_id.data)
        if filtre_form.annee.data is not None:
            query = query.filter(extract('year', RapportThermique.periode_debut) == filtre_form.annee.data)
        if filtre_form.mois.data:
            query = query.filter(RapportThermique.mois == int(filtre_form.mois.data))
        if filtre_form.statut.data:
            query = query.filter(RapportThermique.statut == filtre_form.statut.data)

    # Pagination
    rapports = query.order_by(RapportThermique.periode_debut.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    # Statistiques générales
    stats = {
        'total_rapports': query.count(),
        'rapports_valides': query.filter(RapportThermique.statut == 'valide').count(),
        'energie_totale': db.session.query(func.sum(RapportThermique.energie_produite))\
            .filter(RapportThermique.centrale_id.in_(centrale_ids)).scalar() or 0,
        'nombre_centrales': len(centrales_accessibles)
    }

    return render_template('production_thermique/index.html',
                         rapports=rapports,
                         filtre_form=filtre_form,
                         stats=stats,
                         centrales=centrales_accessibles,
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
    # Initialiser les choix pour centrale_id
    form.centrale_id.choices = [(c.id, f"{c.nom} ({c.code})") for c in centrales]

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
            periode_fin=periode_fin
        )
        
        # Utiliser populate_obj pour tous les autres champs
        form.populate_obj(rapport)

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
            periode_fin=periode_fin,
            energie_produite=form.energie_produite.data,
            energie_disponible=form.energie_disponible.data,
            facteur_charge=form.facteur_charge.data,
            temps_fonctionnement=form.temps_fonctionnement.data,
            nombre_demarrages=form.nombre_demarrages.data,
            nombre_arrets=form.nombre_arrets.data,
            duree_arrets=form.duree_arrets.data,
            consommation_combustible=form.consommation_combustible.data,
            type_combustible_utilise=form.type_combustible_utilise.data,
            cout_combustible=form.cout_combustible.data,
            prix_unitaire_combustible=form.prix_unitaire_combustible.data,
            consommation_specifique_reelle=form.consommation_specifique_reelle.data,
            rendement_global=form.rendement_global.data,
            rendement_thermique=form.rendement_thermique.data,
            rendement_electrique=form.rendement_electrique.data,
            temperature_fumees=form.temperature_fumees.data,
            pression_admission=form.pression_admission.data,
            charge_moyenne=form.charge_moyenne.data,
            charge_maximale=form.charge_maximale.data,
            charge_minimale=form.charge_minimale.data,
            temperature_ambiante_moyenne=form.temperature_ambiante_moyenne.data,
            humidite_relative_moyenne=form.humidite_relative_moyenne.data,
            maintenances_preventives=form.maintenances_preventives.data,
            maintenances_correctives=form.maintenances_correctives.data,
            incidents_majeurs=form.incidents_majeurs.data,
            description_incidents=form.description_incidents.data,
            duree_maintenance=form.duree_maintenance.data,
            consommation_huile_moteur=form.consommation_huile_moteur.data,
            consommation_liquide_refroidissement=form.consommation_liquide_refroidissement.data,
            remplacement_filtres=form.remplacement_filtres.data,
            autres_consommables=form.autres_consommables.data,
            emissions_co2=form.emissions_co2.data,
            emissions_nox=form.emissions_nox.data,
            emissions_co=form.emissions_co.data,
            gestion_dechets=form.gestion_dechets.data,
            impact_environnemental=form.impact_environnemental.data,
            cout_exploitation=form.cout_exploitation.data,
            cout_maintenance=form.cout_maintenance.data,
            recettes_vente=form.recettes_vente.data,
            rentabilite=form.rentabilite.data,
            observations=form.observations.data,
            statut='brouillon'
        )

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
    # Initialiser les choix pour centrale_id
    form.centrale_id.choices = [(c.id, f"{c.nom} ({c.code})") for c in centrales_accessibles]

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