"""
Routes API pour la production hydroélectrique
"""
from flask import request, abort, jsonify
from flask_login import login_required, current_user
from app.production_hydro import production_hydro
from app.models.production_hydro import CentraleHydro
from app.utils.permissions import can_access_operateur


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


@production_hydro.route('/api/centrale/<int:centrale_id>/equipements')
@login_required
def api_centrale_equipements(centrale_id):
    """API pour obtenir les équipements d'une centrale pour pré-remplir les formulaires"""
    centrale = CentraleHydro.query.get_or_404(centrale_id)

    # Vérifier les permissions
    if not can_access_operateur(centrale.operateur_id):
        abort(403)

    # Récupérer les groupes de production
    groupes = []
    for groupe in centrale.groupes_production:
        groupes.append({
            'id': groupe.id,
            'numero_groupe': groupe.numero_groupe,
            'nom_groupe': groupe.nom_groupe,
            'puissance_nominale': groupe.puissance_nominale,
            'tension_nominale': groupe.tension_nominale,
            'vitesse_rotation': groupe.vitesse_rotation,
            'type_turbine': groupe.type_turbine,
            # Champs opérationnels vides pour le rapport
            'heures_fonctionnement': None,
            'energie_produite': None,
            'puissance_moyenne': None,
            'puissance_max': None,
            'nombre_arrets_programme': None,
            'nombre_arrets_force': None,
            'duree_arrets_programme': None,
            'duree_arrets_force': None,
            'rendement_moyen': None,
            'facteur_charge': None,
            'disponibilite': None,
            'date_derniere_revision': groupe.date_derniere_revision,
            'type_derniere_revision': groupe.type_derniere_revision,
            'prochaine_revision': groupe.prochaine_revision,
            'incidents': None,
            'travaux_realises': None,
            'observations': None
        })

    # Récupérer les transformateurs
    transformateurs = []
    for transfo in centrale.transformateurs:
        transformateurs.append({
            'id': transfo.id,
            'numero_transformateur': transfo.numero_transformateur,
            'nom_transformateur': transfo.nom_transformateur,
            'puissance_nominale': transfo.puissance_nominale,
            'tension_primaire': transfo.tension_primaire,
            'tension_secondaire': transfo.tension_secondaire,
            'type_refroidissement': transfo.type_refroidissement,
            # Champs opérationnels vides pour le rapport
            'energie_transferee': None,
            'heures_service': None,
            'charge_moyenne': None,
            'charge_max': None,
            'temperature_huile_moyenne': None,
            'temperature_huile_max': None,
            'temperature_enroulements_max': None,
            'etat_general': None,
            'date_derniere_maintenance': transfo.date_derniere_maintenance,
            'type_maintenance': transfo.type_maintenance,
            'prochaine_maintenance': transfo.prochaine_maintenance,
            'incidents': None,
            'travaux_realises': None,
            'observations': None
        })

    return jsonify({
        'groupes': groupes,
        'transformateurs': transformateurs
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