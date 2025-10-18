"""
Routes API pour la production thermique
"""
from flask import jsonify, request
from flask_login import login_required, current_user
from datetime import datetime
from sqlalchemy import extract, func
from app.production_thermique import production_thermique
from app.models.production_thermique import (
    CentraleThermique, RapportThermique
)
from app.extensions import db
from app.production_thermique.utils import get_accessible_centrales_thermique


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


@production_thermique.route('/api/filters', methods=['GET'])
@login_required
def api_filters():
    """API pour les filtres AJAX - retourne toujours du JSON"""
    page = request.args.get('page', 1, type=int)
    per_page = 10

    # Vérifier les permissions d'accès au module
    if not (current_user.is_admin() or current_user.operateur):
        return jsonify({'error': 'Accès non autorisé'}), 403

    # Obtenir les centrales accessibles
    centrales_accessibles = get_accessible_centrales_thermique()
    centrale_ids = [c.id for c in centrales_accessibles] if centrales_accessibles else []

    # Requête de base pour les rapports
    if centrales_accessibles:
        query = RapportThermique.query.filter(RapportThermique.centrale_id.in_(centrale_ids))
    else:
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
    if centrale_ids:
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
    else:
        stats = {
            'total_rapports': 0,
            'rapports_valides': 0,
            'energie_totale': 0,
            'nombre_centrales': 0,
            'rapports_brouillon': 0
        }

    # Préparer les données JSON
    rapports_data = []
    for rapport in rapports.items:
        rapports_data.append({
            'id': rapport.id,
            'centrale': {
                'id': rapport.centrale.id,
                'nom': rapport.centrale.nom,
                'code': rapport.centrale.code,
                'type_combustible': rapport.centrale.type_combustible
            },
            'periode': {
                'str': rapport.get_periode_str(),
                'debut': rapport.periode_debut.strftime('%d/%m'),
                'fin': rapport.periode_fin.strftime('%d/%m/%Y')
            },
            'energie_produite': rapport.energie_produite,
            'energie_disponible': rapport.energie_disponible,
            'facteur_charge': rapport.facteur_charge,
            'consommation_combustible': rapport.consommation_combustible,
            'consommation_specifique_reelle': rapport.consommation_specifique_reelle,
            'statut': rapport.statut,
            'date_modification': rapport.date_modification.strftime('%d/%m/%Y %H:%M') if rapport.date_modification else rapport.date_creation.strftime('%d/%m/%Y %H:%M'),
            'can_edit': rapport.statut != 'transmis' or current_user.is_super_admin(),
            'can_delete': current_user.is_super_admin()
        })

    return jsonify({
        'rapports': rapports_data,
        'pagination': {
            'page': rapports.page,
            'pages': rapports.pages,
            'total': rapports.total,
            'per_page': per_page,
            'has_prev': rapports.has_prev,
            'has_next': rapports.has_next,
            'prev_num': rapports.prev_num if rapports.has_prev else None,
            'next_num': rapports.next_num if rapports.has_next else None
        },
        'stats': stats,
        'filters': {
            'centrale_id': centrale_param,
            'annee': annee_param,
            'mois': mois_param,
            'statut': statut_param,
            'search': search
        }
    })