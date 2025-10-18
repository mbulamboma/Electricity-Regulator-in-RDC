"""
Routes d'export pour la production hydroélectrique
"""
from flask import Response
from flask_login import login_required
from app.production_hydro import production_hydro
from app.models.production_hydro import CentraleHydro, RapportHydro
from app.models.operateurs import Operateur
import csv
from io import StringIO


@production_hydro.route('/centrales/export')
@login_required
def export_centrales():
    """Exporter les centrales hydroélectriques au format CSV"""
    centrales_accessibles = CentraleHydro.query.filter_by(actif=True).all()

    # Créer un buffer pour le CSV
    output = StringIO()
    writer = csv.writer(output, delimiter=';')

    # En-têtes du CSV
    writer.writerow([
        'ID', 'Nom', 'Code', 'Localisation', 'Province', 'Cours d\'eau',
        'Puissance Installée (MW)', 'Puissance Disponible (MW)', 'Hauteur de Chute (m)',
        'Débit d\'Équipement (m³/s)', 'Type de Centrale', 'Nombre de Groupes',
        'Nombre de Transformateurs', 'Tension d\'Évacuation (kV)', 'Statut',
        'Nombre de Rapports', 'Dernière Période', 'Énergie Totale Produite (MWh)',
        'Opérateur'
    ])

    # Statistiques par centrale
    for centrale in centrales_accessibles:
        stats = {
            'nb_rapports': len(centrale.rapports),
            'derniere_periode': None,
            'energie_totale': 0
        }

        if centrale.rapports:
            dernier_rapport = max(centrale.rapports, key=lambda r: (r.annee, r.mois))
            stats['derniere_periode'] = dernier_rapport.get_periode_str()
            stats['energie_totale'] = sum([r.energie_produite or 0 for r in centrale.rapports])

        # Écrire la ligne de données
        writer.writerow([
            centrale.id,
            centrale.nom,
            centrale.code or '',
            centrale.localisation or '',
            centrale.province or '',
            centrale.cours_eau or '',
            centrale.puissance_installee or 0,
            centrale.puissance_disponible or 0,
            centrale.hauteur_chute or 0,
            centrale.debit_equipement or 0,
            centrale.type_centrale or '',
            centrale.nombre_groupes or 0,
            centrale.nombre_transformateurs or 0,
            centrale.tension_evacuation or 0,
            centrale.statut or '',
            stats['nb_rapports'],
            stats['derniere_periode'] or '',
            stats['energie_totale'],
            centrale.operateur.nom if centrale.operateur else ''
        ])

    # Préparer la réponse
    output.seek(0)
    response = Response(
        output.getvalue(),
        mimetype='text/csv; charset=utf-8',
        headers={
            'Content-Disposition': 'attachment; filename=centrales_hydroelectriques.csv',
            'Content-Type': 'text/csv; charset=utf-8'
        }
    )

    return response