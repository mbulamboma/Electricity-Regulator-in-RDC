"""
Routes pour le dashboard ARE
"""
from flask import render_template, request, redirect, url_for, flash, jsonify, abort, send_file
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import json
import io

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    from openpyxl import Workbook
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

try:
    from pptx import Presentation
    PPTX_AVAILABLE = True
except ImportError:
    PPTX_AVAILABLE = False

from app.are.dashboard import dashboard_bp
from app.extensions import db
from app.models.dashboard_are import (
    KPIStrategic, IndicateurSectoriel, AlerteRegulateur, 
    DonneesProvince, RapportAnnuel
)
from app.models.operateurs import Operateur
from app.are.dashboard.forms import (
    FiltreTableauBordForm, AlerteForm, KPIForm, 
    IndicateurSectorielForm, RapportAnnuelForm, ExportForm
)
from app.are.services import IndicateursAREService
from app.are.services_statistiques import StatistiquesAREService, DashboardAREService
from app.utils.decorators import admin_required
from app.utils.permissions import get_accessible_operateurs


@dashboard_bp.route('/api/kpis/<int:annee>/mettre-a-jour', methods=['POST'])
@login_required
@admin_required
def api_mettre_a_jour_kpis(annee):
    """API pour mettre à jour les KPIs automatiquement"""
    kpis = IndicateursAREService.mettre_a_jour_kpis_strategiques(annee)
    
    return jsonify({
        'message': f'{len(kpis)} KPIs mis à jour',
        'kpis': [kpi.to_dict() for kpi in kpis]
    })


# ===== NOUVELLES ROUTES STATISTIQUES ARE =====

@dashboard_bp.route('/statistiques')
@login_required
@admin_required
def statistiques():
    """Page des statistiques complètes ARE"""
    annee_debut = request.args.get('annee_debut', 2020, type=int)
    annee_fin = request.args.get('annee_fin', 2024, type=int)
    
    # 1. Portfolio de projets
    portfolio = DashboardAREService.get_portfolio_projets()
    
    # 2. Evolution de la capacité installée
    evolution_capacite = DashboardAREService.get_evolution_capacite(annee_debut, annee_fin)
    
    # 3. Statistiques nationales
    stats_nationales = DashboardAREService.get_statistiques_nationales_periode(annee_debut, annee_fin)
    
    # 4. Données solaires
    donnees_solaires = DashboardAREService.get_donnees_solaires()
    
    # 5. Statistiques de clientèle
    stats_clientele = DashboardAREService.get_statistiques_clientele(annee_debut, annee_fin)
    
    # 6. Données provinciales pour la carte
    donnees_provinciales = DonneesProvince.query.filter(
        DonneesProvince.annee.between(annee_debut, annee_fin),
        DonneesProvince.actif == True
    ).order_by(DonneesProvince.province, DonneesProvince.annee).all()
    
    # Préparer les données pour les graphiques
    graphiques_data = {
        'evolution_capacite_labels': list(range(annee_debut, annee_fin + 1)),
        'evolution_capacite_hydro': [],
        'evolution_capacite_thermique': [],
        'evolution_capacite_solaire': [],
        'evolution_production_labels': list(range(annee_debut, annee_fin + 1)),
        'evolution_production_values': [],
        'evolution_clients_labels': list(range(annee_debut, annee_fin + 1)),
        'evolution_clients_values': []
    }
    
    # Remplir les données de graphiques
    for annee in range(annee_debut, annee_fin + 1):
        # Capacités par source
        capacite_hydro = sum([c['capacite_installee_mw'] for c in evolution_capacite 
                             if c['annee'] == annee and c['type_source'] == 'production_hydro'])
        capacite_thermique = sum([c['capacite_installee_mw'] for c in evolution_capacite 
                                 if c['annee'] == annee and c['type_source'] == 'production_thermique'])
        capacite_solaire = sum([c['capacite_installee_mw'] for c in evolution_capacite 
                               if c['annee'] == annee and c['type_source'] == 'production_solaire'])
        
        graphiques_data['evolution_capacite_hydro'].append(capacite_hydro)
        graphiques_data['evolution_capacite_thermique'].append(capacite_thermique)
        graphiques_data['evolution_capacite_solaire'].append(capacite_solaire)
        
        # Production totale
        stat_nat = next((s for s in stats_nationales if s['annee'] == annee), None)
        production_totale = stat_nat['production_totale_annuelle_gwh'] if stat_nat else 0
        graphiques_data['evolution_production_values'].append(production_totale)
        
        # Clients totaux
        clients_totaux = sum([c['total_clients'] for c in stats_clientele if c['annee'] == annee])
        graphiques_data['evolution_clients_values'].append(clients_totaux)
    
    return render_template('are/dashboard/statistiques.html',
                         portfolio=portfolio,
                         evolution_capacite=evolution_capacite,
                         stats_nationales=stats_nationales,
                         donnees_solaires=donnees_solaires,
                         stats_clientele=stats_clientele,
                         donnees_provinciales=donnees_provinciales,
                         graphiques_data=graphiques_data,
                         annee_debut=annee_debut,
                         annee_fin=annee_fin)


@dashboard_bp.route('/calculer-statistiques/<int:annee>')
@login_required
@admin_required
def calculer_statistiques(annee):
    """Lance le calcul des statistiques pour une année donnée"""
    try:
        success = StatistiquesAREService.calculer_toutes_statistiques(annee)
        
        if success:
            flash(f'✅ Statistiques calculées avec succès pour l\'année {annee}', 'success')
        else:
            flash(f'❌ Erreur lors du calcul des statistiques pour l\'année {annee}', 'error')
    
    except Exception as e:
        flash(f'❌ Erreur technique: {str(e)}', 'error')
    
    return redirect(url_for('are_dashboard.statistiques'))


@dashboard_bp.route('/api/statistiques/portfolio')
@login_required
@admin_required
def api_portfolio_projets():
    """API pour récupérer le portfolio des projets"""
    portfolio = DashboardAREService.get_portfolio_projets()
    return jsonify(portfolio)


@dashboard_bp.route('/api/statistiques/evolution-capacite')
@login_required
@admin_required
def api_evolution_capacite():
    """API pour récupérer l'évolution de la capacité"""
    annee_debut = request.args.get('annee_debut', 2020, type=int)
    annee_fin = request.args.get('annee_fin', 2024, type=int)
    
    evolution = DashboardAREService.get_evolution_capacite(annee_debut, annee_fin)
    return jsonify(evolution)


@dashboard_bp.route('/api/statistiques/nationales')
@login_required
@admin_required
def api_statistiques_nationales():
    """API pour récupérer les statistiques nationales"""
    annee_debut = request.args.get('annee_debut', 2020, type=int)
    annee_fin = request.args.get('annee_fin', 2024, type=int)
    
    stats = DashboardAREService.get_statistiques_nationales_periode(annee_debut, annee_fin)
    return jsonify(stats)


def _calculer_statistiques_nationales_avancees(annee_debut=2020, annee_fin=None):
    """Calculer toutes les statistiques nationales demandées"""
    from sqlalchemy import func, and_, extract
    from app.models.production_hydro import CentraleHydro, RapportHydro
    from app.models.production_thermique import CentraleThermique, RapportThermique  
    from app.models.production_solaire import CentraleSolaire, RapportSolaire
    from app.models.distribution import ReseauDistribution, DonneesDistributionMensuelles
    from app.models.transport import LigneTransport, PosteTransport
    
    if annee_fin is None:
        annee_fin = datetime.now().year
    
    stats = {}
    
    # 1. Evolution de la capacité installée en puissance MW
    evolution_capacite = []
    for annee in range(annee_debut, annee_fin + 1):
        capacite_hydro = db.session.query(func.sum(CentraleHydro.puissance_installee)).filter(
            CentraleHydro.actif == True,
            extract('year', CentraleHydro.date_mise_service) <= annee
        ).scalar() or 0
        
        capacite_thermique = db.session.query(func.sum(CentraleThermique.puissance_installee)).filter(
            CentraleThermique.actif == True,
            extract('year', CentraleThermique.date_mise_service) <= annee
        ).scalar() or 0
        
        capacite_solaire = db.session.query(func.sum(CentraleSolaire.puissance_installee)).filter(
            CentraleSolaire.actif == True,
            extract('year', CentraleSolaire.date_mise_service) <= annee
        ).scalar() or 0
        
        evolution_capacite.append({
            'annee': annee,
            'capacite_hydro_mw': round(capacite_hydro, 2),
            'capacite_thermique_mw': round(capacite_thermique, 2),
            'capacite_solaire_mw': round(capacite_solaire, 2),
            'capacite_totale_mw': round(capacite_hydro + capacite_thermique + capacite_solaire, 2)
        })
    
    # 2. Production annuelle d'énergie électrique
    evolution_production = []
    for annee in range(annee_debut, annee_fin + 1):
        prod_hydro = db.session.query(func.sum(RapportHydro.energie_produite)).filter(
            RapportHydro.annee == annee,
            RapportHydro.actif == True
        ).scalar() or 0
        
        prod_thermique = db.session.query(func.sum(RapportThermique.energie_produite)).filter(
            RapportThermique.annee == annee,
            RapportThermique.actif == True
        ).scalar() or 0
        
        prod_solaire = db.session.query(func.sum(RapportSolaire.energie_produite)).filter(
            RapportSolaire.annee == annee,
            RapportSolaire.actif == True
        ).scalar() or 0
        
        evolution_production.append({
            'annee': annee,
            'production_hydro_gwh': round(prod_hydro / 1000, 2) if prod_hydro else 0,
            'production_thermique_gwh': round(prod_thermique / 1000, 2) if prod_thermique else 0,
            'production_solaire_gwh': round(prod_solaire / 1000, 2) if prod_solaire else 0,
            'production_totale_gwh': round((prod_hydro + prod_thermique + prod_solaire) / 1000, 2)
        })
    
    # 3. Statistiques de clientèle
    evolution_clients = []
    for annee in range(annee_debut, annee_fin + 1):
        # Trouver le dernier mois avec des données pour l'année
        dernier_mois = db.session.query(
            func.max(DonneesDistributionMensuelles.mois)
        ).filter(
            DonneesDistributionMensuelles.annee == annee,
            DonneesDistributionMensuelles.actif == True
        ).scalar() or 12
        
        # Calculer les totaux par type de client au dernier mois disponible
        clients_ht_total = db.session.query(
            func.sum(DonneesDistributionMensuelles.clients_ht_debut_mois + 
                    DonneesDistributionMensuelles.nouveaux_raccordements_ht - 
                    DonneesDistributionMensuelles.deconnexions_ht)
        ).filter(
            DonneesDistributionMensuelles.annee == annee,
            DonneesDistributionMensuelles.mois == dernier_mois,
            DonneesDistributionMensuelles.actif == True
        ).scalar() or 0
        
        clients_mt_total = db.session.query(
            func.sum(DonneesDistributionMensuelles.clients_mt_debut_mois + 
                    DonneesDistributionMensuelles.nouveaux_raccordements_mt - 
                    DonneesDistributionMensuelles.deconnexions_mt)
        ).filter(
            DonneesDistributionMensuelles.annee == annee,
            DonneesDistributionMensuelles.mois == dernier_mois,
            DonneesDistributionMensuelles.actif == True
        ).scalar() or 0
        
        clients_bt_total = db.session.query(
            func.sum(DonneesDistributionMensuelles.clients_bt_debut_mois + 
                    DonneesDistributionMensuelles.nouveaux_raccordements_bt - 
                    DonneesDistributionMensuelles.deconnexions_bt)
        ).filter(
            DonneesDistributionMensuelles.annee == annee,
            DonneesDistributionMensuelles.mois == dernier_mois,
            DonneesDistributionMensuelles.actif == True
        ).scalar() or 0
            
        # Somme de tous les opérateurs pour l'année
        total_clients_annee = db.session.query(
            func.sum(DonneesDistributionMensuelles.clients_ht_debut_mois + 
                    DonneesDistributionMensuelles.nouveaux_raccordements_ht - 
                    DonneesDistributionMensuelles.deconnexions_ht +
                    DonneesDistributionMensuelles.clients_mt_debut_mois + 
                    DonneesDistributionMensuelles.nouveaux_raccordements_mt - 
                    DonneesDistributionMensuelles.deconnexions_mt +
                    DonneesDistributionMensuelles.clients_bt_debut_mois + 
                    DonneesDistributionMensuelles.nouveaux_raccordements_bt - 
                    DonneesDistributionMensuelles.deconnexions_bt)
        ).filter(
            DonneesDistributionMensuelles.annee == annee,
            DonneesDistributionMensuelles.mois == dernier_mois,
            DonneesDistributionMensuelles.actif == True
        ).scalar() or 0
        
        # Factures émises et payées
        factures_emises = db.session.query(func.sum(DonneesDistributionMensuelles.factures_emises)).filter(
            DonneesDistributionMensuelles.annee == annee,
            DonneesDistributionMensuelles.actif == True
        ).scalar() or 0
        
        factures_payees = db.session.query(func.sum(DonneesDistributionMensuelles.factures_payees)).filter(
            DonneesDistributionMensuelles.annee == annee,
            DonneesDistributionMensuelles.actif == True
        ).scalar() or 0
        
        evolution_clients.append({
            'annee': annee,
            'clients_ht': clients_ht_total,
            'clients_mt': clients_mt_total,
            'clients_bt': clients_bt_total,
            'clients_total': total_clients_annee,
            'factures_emises': factures_emises,
            'factures_payees': factures_payees,
            'taux_paiement': round((factures_payees / factures_emises * 100), 2) if factures_emises > 0 else 0
        })
    
    # 4. Capacité solaire domestique (estimation basée sur les centrales solaires)
    capacite_solaire_domestique = {}
    for annee in range(annee_debut, annee_fin + 1):
        # Estimation : 30% de la capacité solaire totale pour le domestique
        capacite_totale = db.session.query(func.sum(CentraleSolaire.puissance_installee)).filter(
            CentraleSolaire.actif == True,
            extract('year', CentraleSolaire.date_mise_service) <= annee
        ).scalar() or 0
        
        capacite_solaire_domestique[annee] = round(capacite_totale * 0.3, 2)
    
    # 5. Statistiques d'infrastructure
    stats_infrastructure = {
        'nb_centrales_hydro': CentraleHydro.query.filter_by(actif=True).count(),
        'nb_centrales_thermique': CentraleThermique.query.filter_by(actif=True).count(),
        'nb_centrales_solaire': CentraleSolaire.query.filter_by(actif=True).count(),
        'nb_reseaux_distribution': ReseauDistribution.query.filter_by(actif=True).count(),
        'nb_lignes_transport': LigneTransport.query.filter_by(actif=True).count(),
        'nb_postes_transport': PosteTransport.query.filter_by(actif=True).count(),
    }
    
    # 6. Taux et couverture (estimations basées sur les données disponibles)
    # Population totale estimée de la RDC : ~105 millions (2025)
    population_rdc = 105000000
    
    taux_electrification = []
    for annee in range(annee_debut, annee_fin + 1):
        # Récupérer les données de StatistiqueNationale si disponibles
        from app.models.statistiques_are import StatistiqueNationale
        stats_annee = StatistiqueNationale.query.filter_by(annee=annee).first()
        
        if stats_annee:
            # Utiliser les vraies statistiques
            clients_annee = stats_annee.total_clients_nationaux or 0
            taux_electrification_reel = stats_annee.taux_electrification_national or 0
            taux_acces_reel = stats_annee.taux_acces_national or 0
            taux_couverture_reel = stats_annee.taux_couverture_national or 0
            
            taux_electrification.append({
                'annee': annee,
                'clients': clients_annee,
                'personnes_desservies': int(clients_annee * 4.5),  # 4.5 personnes par ménage
                'taux_acces_pct': round(taux_acces_reel, 3),
                'taux_electrification_pct': round(taux_electrification_reel, 3),
                'taux_couverture_pct': round(taux_couverture_reel, 3)
            })
        else:
            # Fallback vers l'ancien calcul si pas de StatistiqueNationale
            clients_annee = next((c['clients_total'] for c in evolution_clients if c['annee'] == annee), 0)
            # Estimation : 1 client = 5 personnes desservies en moyenne
            personnes_desservies = clients_annee * 5
            taux = round((personnes_desservies / population_rdc * 100), 2) if population_rdc > 0 else 0
            
            taux_electrification.append({
                'annee': annee,
                'clients': clients_annee,
                'personnes_desservies': personnes_desservies,
                'taux_acces_pct': taux,
                'taux_electrification_pct': taux * 0.8,  # Facteur de correction
                'taux_couverture_pct': taux * 1.2 if taux * 1.2 <= 100 else 100
            })
    
    return {
        'evolution_capacite': evolution_capacite,
        'evolution_production': evolution_production, 
        'evolution_clients': evolution_clients,
        'capacite_solaire_domestique': capacite_solaire_domestique,
        'stats_infrastructure': stats_infrastructure,
        'taux_electrification': taux_electrification,
        'periode': {'debut': annee_debut, 'fin': annee_fin}
    }


@dashboard_bp.route('/')
@login_required
@admin_required
def index():
    """Page principale du dashboard ARE avec statistiques nationales complètes"""
    form = FiltreTableauBordForm()
    
    # Récupérer les filtres
    annee = request.args.get('annee', datetime.now().year, type=int)
    annee_debut = request.args.get('annee_debut', 2020, type=int)
    annee_fin = request.args.get('annee_fin', datetime.now().year, type=int)
    operateur_id = request.args.get('operateur_id', type=int)
    province = request.args.get('province', '')
    
    # KPIs stratégiques
    kpis_query = KPIStrategic.query.filter_by(annee=annee, actif=True)
    if operateur_id:
        kpis_query = kpis_query.filter_by(operateur_id=operateur_id)
    kpis = kpis_query.all()
    
    # Alertes critiques récentes
    alertes_critiques = AlerteRegulateur.query.filter_by(
        statut='active'
    ).filter(
        AlerteRegulateur.severite.in_(['critique', 'elevee'])
    ).order_by(AlerteRegulateur.date_creation.desc()).limit(5).all()
    
    # Mix énergétique
    mix_energetique = IndicateursAREService.calculer_mix_energetique(annee, operateur_id)
    
    # Performance des opérateurs
    performance_operateurs = IndicateursAREService.calculer_performance_operateurs(annee)
    if operateur_id:
        performance_operateurs = [p for p in performance_operateurs if p['operateur_id'] == operateur_id]
    
    # Données par province pour la carte
    donnees_provinces = []
    if not operateur_id:  # Affichage national uniquement
        donnees_provinces_obj = DonneesProvince.query.filter_by(annee=annee).all()
        donnees_provinces = [province.to_dict() for province in donnees_provinces_obj]
    
    # NOUVELLES STATISTIQUES NATIONALES AVANCÉES
    stats_nationales = _calculer_statistiques_nationales_avancees(annee_debut, annee_fin)
    
    # Statistiques générales
    stats = {
        'nb_operateurs_actifs': Operateur.query.filter_by(actif=True).count(),
        'nb_alertes_actives': AlerteRegulateur.query.filter_by(statut='active').count(),
        'nb_kpis': len(kpis),
        'production_totale': mix_energetique['total']
    }
    
    return render_template('are/dashboard/index.html',
                         form=form,
                         kpis=kpis,
                         alertes_critiques=alertes_critiques,
                         mix_energetique=mix_energetique,
                         performance_operateurs=performance_operateurs,
                         donnees_provinces=donnees_provinces,
                         stats=stats,
                         stats_nationales=stats_nationales,
                         annee=annee,
                         annee_debut=annee_debut,
                         annee_fin=annee_fin,
                         operateur_id=operateur_id,
                         province=province)


@dashboard_bp.route('/kpis')
@login_required
@admin_required
def kpis():
    """Page détaillée des KPIs"""
    form = FiltreTableauBordForm()
    
    # Filtres
    annee = request.args.get('annee', datetime.now().year, type=int)
    operateur_id = request.args.get('operateur_id', type=int)
    
    # Récupérer tous les KPIs
    kpis_query = KPIStrategic.query.filter_by(annee=annee, actif=True)
    if operateur_id:
        kpis_query = kpis_query.filter_by(operateur_id=operateur_id)
    
    kpis = kpis_query.order_by(KPIStrategic.code).all()
    
    # Grouper les KPIs par catégorie
    kpis_groupes = {}
    for kpi in kpis:
        prefix = kpi.code.split('_')[0]
        if prefix not in kpis_groupes:
            kpis_groupes[prefix] = []
        kpis_groupes[prefix].append(kpi)
    
    # Indicateurs sectoriels
    indicateurs = IndicateurSectoriel.query.filter_by(annee=annee, actif=True)
    if operateur_id:
        indicateurs = indicateurs.filter_by(operateur_id=operateur_id)
    indicateurs = indicateurs.all()
    
    # Grouper les indicateurs par catégorie
    indicateurs_groupes = {}
    for ind in indicateurs:
        cat = ind.categorie.value
        if cat not in indicateurs_groupes:
            indicateurs_groupes[cat] = []
        indicateurs_groupes[cat].append(ind)
    
    return render_template('are/dashboard/kpis.html',
                         form=form,
                         kpis_groupes=kpis_groupes,
                         indicateurs_groupes=indicateurs_groupes,
                         annee=annee,
                         operateur_id=operateur_id)


@dashboard_bp.route('/kpis/nouveau', methods=['GET', 'POST'])
@login_required
@admin_required
def nouveau_kpi():
    """Créer un nouveau KPI"""
    form = KPIForm()
    
    if form.validate_on_submit():
        kpi = KPIStrategic(
            code=form.code.data,
            nom=form.nom.data,
            description=form.description.data,
            valeur=form.valeur.data,
            unite=form.unite.data,
            periode=form.periode.data,
            annee=form.annee.data,
            objectif=form.objectif.data,
            seuil_alerte=form.seuil_alerte.data,
            operateur_id=form.operateur_id.data,
            source_donnees=form.source_donnees.data
        )
        
        kpi.save()
        flash('KPI créé avec succès.', 'success')
        return redirect(url_for('are_dashboard.kpis'))
    
    return render_template('are/dashboard/kpi_form.html', form=form, title='Nouveau KPI')


@dashboard_bp.route('/kpis/<int:kpi_id>/modifier', methods=['GET', 'POST'])
@login_required
@admin_required
def modifier_kpi(kpi_id):
    """Modifier un KPI existant"""
    kpi = KPIStrategic.query.get_or_404(kpi_id)
    form = KPIForm(obj=kpi)
    
    if form.validate_on_submit():
        kpi.update(
            code=form.code.data,
            nom=form.nom.data,
            description=form.description.data,
            valeur=form.valeur.data,
            unite=form.unite.data,
            periode=form.periode.data,
            annee=form.annee.data,
            objectif=form.objectif.data,
            seuil_alerte=form.seuil_alerte.data,
            operateur_id=form.operateur_id.data,
            source_donnees=form.source_donnees.data
        )
        
        flash('KPI modifié avec succès.', 'success')
        return redirect(url_for('are_dashboard.kpis'))
    
    return render_template('are/dashboard/kpi_form.html', 
                         form=form, 
                         kpi=kpi,
                         title='Modifier KPI')


@dashboard_bp.route('/alertes')
@login_required
@admin_required
def alertes():
    """Page de gestion des alertes"""
    # Filtres
    statut = request.args.get('statut', 'active')
    type_alerte = request.args.get('type')
    severite = request.args.get('severite')
    
    # Construire la requête
    alertes_query = AlerteRegulateur.query
    
    if statut:
        alertes_query = alertes_query.filter_by(statut=statut)
    if type_alerte:
        alertes_query = alertes_query.filter_by(type=type_alerte)
    if severite:
        alertes_query = alertes_query.filter_by(severite=severite)
    
    alertes = alertes_query.order_by(
        AlerteRegulateur.priorite.asc(),
        AlerteRegulateur.date_creation.desc()
    ).all()
    
    # Statistiques des alertes
    stats_alertes = {
        'total': AlerteRegulateur.query.count(),
        'actives': AlerteRegulateur.query.filter_by(statut='active').count(),
        'critiques': AlerteRegulateur.query.filter_by(
            statut='active', 
            severite='critique'
        ).count(),
        'expirees': AlerteRegulateur.query.filter(
            AlerteRegulateur.date_echeance < datetime.now().date(),
            AlerteRegulateur.statut == 'active'
        ).count() if AlerteRegulateur.query.filter(
            AlerteRegulateur.date_echeance.isnot(None)
        ).first() else 0
    }
    
    return render_template('are/dashboard/alertes.html',
                         alertes=alertes,
                         stats_alertes=stats_alertes,
                         statut=statut,
                         type_alerte=type_alerte,
                         severite=severite)


@dashboard_bp.route('/alertes/nouvelle', methods=['GET', 'POST'])
@login_required
@admin_required
def nouvelle_alerte():
    """Créer une nouvelle alerte"""
    form = AlerteForm()
    
    if form.validate_on_submit():
        alerte = AlerteRegulateur(
            type=form.type.data,
            severite=form.severite.data,
            operateur_id=form.operateur_id.data,
            entite_concernee=form.entite_concernee.data,
            titre=form.titre.data,
            description=form.description.data,
            date_echeance=form.date_echeance.data,
            actions_recommandees=form.actions_recommandees.data,
            priorite=form.priorite.data,
            createur_id=current_user.id
        )
        
        alerte.save()
        flash('Alerte créée avec succès.', 'success')
        return redirect(url_for('are_dashboard.alertes'))
    
    return render_template('are/dashboard/alerte_form.html', 
                         form=form, 
                         title='Nouvelle alerte')


@dashboard_bp.route('/alertes/<int:alerte_id>/resoudre', methods=['POST'])
@login_required
@admin_required
def resoudre_alerte(alerte_id):
    """Marquer une alerte comme résolue"""
    alerte = AlerteRegulateur.query.get_or_404(alerte_id)
    
    alerte.update(
        statut='resolue',
        date_resolution=datetime.now().date()
    )
    
    flash('Alerte marquée comme résolue.', 'success')
    return redirect(url_for('are_dashboard.alertes'))


@dashboard_bp.route('/alertes/<int:alerte_id>')
@login_required
@admin_required
def detail_alerte(alerte_id):
    """Voir les détails d'une alerte"""
    alerte = AlerteRegulateur.query.get_or_404(alerte_id)
    return render_template('are/dashboard/alerte_detail.html', alerte=alerte)


@dashboard_bp.route('/alertes/<int:alerte_id>/supprimer', methods=['POST'])
@login_required
@admin_required
def supprimer_alerte(alerte_id):
    """Supprimer une alerte"""
    alerte = AlerteRegulateur.query.get_or_404(alerte_id)
    
    # Sauvegarder les infos pour le message
    titre_alerte = alerte.titre
    
    # Supprimer l'alerte
    alerte.delete()
    
    flash(f'Alerte "{titre_alerte}" supprimée avec succès.', 'success')
    return redirect(url_for('are_dashboard.alertes'))


@dashboard_bp.route('/rapports')
@login_required
@admin_required
def rapports():
    """Page de gestion des rapports annuels"""
    rapports = RapportAnnuel.query.order_by(
        RapportAnnuel.annee.desc()
    ).all()
    
    return render_template('are/dashboard/rapports.html', rapports=rapports)


@dashboard_bp.route('/rapports/nouveau', methods=['GET', 'POST'])
@login_required
@admin_required
def nouveau_rapport():
    """Créer un nouveau rapport annuel"""
    form = RapportAnnuelForm()
    
    if form.validate_on_submit():
        # Générer le contenu du rapport
        contenu = {
            'titre': form.titre.data,
            'annee': form.annee.data,
            'periode': {
                'debut': form.periode_debut.data.isoformat(),
                'fin': form.periode_fin.data.isoformat()
            },
            'sections': {
                'mix_energetique': form.inclure_mix_energetique.data == 'oui',
                'performance_operateurs': form.inclure_performance_operateurs.data == 'oui',
                'indicateurs_financiers': form.inclure_indicateurs_financiers.data == 'oui',
                'activites_regulation': form.inclure_activites_regulation.data == 'oui',
                'perspectives': form.inclure_perspectives.data == 'oui'
            },
            'donnees': {}
        }
        
        # Récupérer les données selon les sections sélectionnées
        if contenu['sections']['mix_energetique']:
            contenu['donnees']['mix_energetique'] = IndicateursAREService.calculer_mix_energetique(form.annee.data)
        
        if contenu['sections']['performance_operateurs']:
            contenu['donnees']['performance_operateurs'] = IndicateursAREService.calculer_performance_operateurs(form.annee.data)
        
        # Créer le rapport
        rapport = RapportAnnuel(
            annee=form.annee.data,
            titre=form.titre.data,
            contenu_json=contenu,
            periode_debut=form.periode_debut.data,
            periode_fin=form.periode_fin.data,
            nombre_operateurs=Operateur.query.filter_by(actif=True).count(),
            auteur_id=current_user.id
        )
        
        rapport.save()
        flash('Rapport annuel généré avec succès.', 'success')
        return redirect(url_for('are_dashboard.voir_rapport', rapport_id=rapport.id))
    
    return render_template('are/dashboard/rapport_form.html', 
                         form=form, 
                         title='Nouveau rapport annuel')


@dashboard_bp.route('/rapports/<int:rapport_id>')
@login_required
@admin_required
def voir_rapport(rapport_id):
    """Voir un rapport annuel"""
    rapport = RapportAnnuel.query.get_or_404(rapport_id)
    
    return render_template('are/dashboard/rapport_detail.html', rapport=rapport)


@dashboard_bp.route('/export', methods=['GET', 'POST'])
@login_required
@admin_required
def export_donnees():
    """Exporter les données du dashboard"""
    form = ExportForm()
    
    if form.validate_on_submit():
        format_export = form.format_export.data
        donnees_export = form.donnees_export.data
        annee = form.annee_export.data
        operateur_id = form.operateur_id.data
        
        if format_export == 'excel':
            return export_excel(donnees_export, annee, operateur_id)
        elif format_export == 'powerpoint':
            return export_powerpoint(donnees_export, annee, operateur_id)
        else:
            flash('Format d\'export non supporté.', 'error')
    
    return render_template('are/dashboard/export.html', form=form)


def export_excel(donnees_export, annee, operateur_id):
    """Exporter vers Excel"""
    if not OPENPYXL_AVAILABLE:
        flash('Openpyxl n\'est pas installé. Veuillez installer openpyxl pour l\'export Excel.', 'error')
        return redirect(url_for('are_dashboard.export_donnees'))
    
    output = io.BytesIO()
    workbook = Workbook()
    
    # Supprimer la feuille par défaut
    workbook.remove(workbook.active)
    
    if donnees_export in ['kpis', 'tout']:
        # Feuille KPIs
        ws_kpis = workbook.create_sheet("KPIs Stratégiques")
        ws_kpis.append(['Code', 'Nom', 'Valeur', 'Unité', 'Période', 'Objectif', 'Opérateur'])
        
        kpis_query = KPIStrategic.query.filter_by(annee=annee, actif=True)
        if operateur_id:
            kpis_query = kpis_query.filter_by(operateur_id=operateur_id)
        
        for kpi in kpis_query.all():
            ws_kpis.append([
                kpi.code, kpi.nom, kpi.valeur, kpi.unite, 
                kpi.periode, kpi.objectif or '',
                kpi.operateur.nom_commercial if kpi.operateur else 'National'
            ])
    
    if donnees_export in ['performance', 'tout']:
        # Feuille Performance
        ws_perf = workbook.create_sheet("Performance Opérateurs")
        ws_perf.append([
            'Opérateur', 'Puissance Installée (MW)', 'Production (MWh)', 
            'Facteur de Charge (%)', 'Clients Total', 'Part Hydro (%)', 
            'Part Thermique (%)', 'Part Solaire (%)'
        ])
        
        performance = IndicateursAREService.calculer_performance_operateurs(annee)
        if operateur_id:
            performance = [p for p in performance if p['operateur_id'] == operateur_id]
        
        for perf in performance:
            ws_perf.append([
                perf['operateur'], 
                perf['puissance_installee'],
                perf['production_annuelle'],
                perf['facteur_charge'],
                perf['clients_total'],
                perf['mix_energetique']['hydro'],
                perf['mix_energetique']['thermique'],
                perf['mix_energetique']['solaire']
            ])
    
    workbook.save(output)
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'dashboard_are_{annee}.xlsx'
    )


def export_powerpoint(donnees_export, annee, operateur_id):
    """Exporter vers PowerPoint"""
    if not PPTX_AVAILABLE:
        flash('python-pptx n\'est pas installé. Veuillez installer python-pptx pour l\'export PowerPoint.', 'error')
        return redirect(url_for('are_dashboard.export_donnees'))
    
    prs = Presentation()
    
    # Slide de titre
    slide_layout = prs.slide_layouts[0]  # Layout titre
    slide = prs.slides.add_slide(slide_layout)
    title = slide.shapes.title
    subtitle = slide.placeholders[1]
    
    title.text = f"Dashboard ARE - Année {annee}"
    subtitle.text = f"Rapport généré le {datetime.now().strftime('%d/%m/%Y')}"
    
    if donnees_export in ['kpis', 'tout']:
        # Slide KPIs
        slide_layout = prs.slide_layouts[1]  # Layout contenu
        slide = prs.slides.add_slide(slide_layout)
        title = slide.shapes.title
        title.text = "KPIs Stratégiques"
        
        # Récupérer les KPIs principaux
        kpis_query = KPIStrategic.query.filter_by(annee=annee, actif=True)
        if operateur_id:
            kpis_query = kpis_query.filter_by(operateur_id=operateur_id)
        
        kpis = kpis_query.limit(5).all()  # Top 5 KPIs
        
        content = slide.placeholders[1]
        text_frame = content.text_frame
        text_frame.text = "Principaux indicateurs:"
        
        for kpi in kpis:
            p = text_frame.add_paragraph()
            p.text = f"• {kpi.nom}: {kpi.valeur} {kpi.unite}"
    
    # Sauvegarder
    output = io.BytesIO()
    prs.save(output)
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation',
        as_attachment=True,
        download_name=f'dashboard_are_{annee}.pptx'
    )


# API endpoints pour les données dynamiques

@dashboard_bp.route('/api/kpis/<int:annee>')
@login_required
@admin_required
def api_kpis(annee):
    """API pour récupérer les KPIs d'une année"""
    operateur_id = request.args.get('operateur_id', type=int)
    
    kpis_query = KPIStrategic.query.filter_by(annee=annee, actif=True)
    if operateur_id:
        kpis_query = kpis_query.filter_by(operateur_id=operateur_id)
    
    kpis = kpis_query.all()
    
    return jsonify({
        'kpis': [kpi.to_dict() for kpi in kpis],
        'total': len(kpis)
    })


@dashboard_bp.route('/api/mix-energetique/<int:annee>')
@login_required
@admin_required
def api_mix_energetique(annee):
    """API pour le mix énergétique"""
    operateur_id = request.args.get('operateur_id', type=int)
    
    mix = IndicateursAREService.calculer_mix_energetique(annee, operateur_id)
    
    return jsonify(mix)


@dashboard_bp.route('/api/alertes/generer', methods=['POST'])
@login_required
@admin_required
def api_generer_alertes():
    """API pour générer les alertes automatiques"""
    alertes = IndicateursAREService.generer_alertes_automatiques()
    
    return jsonify({
        'message': f'{len(alertes)} alertes générées',
        'alertes': [alerte.to_dict() for alerte in alertes]
    })


@dashboard_bp.route('/kpi/<int:kpi_id>/supprimer', methods=['POST'])
@login_required
@admin_required
def supprimer_kpi(kpi_id):
    """Supprimer un KPI stratégique"""
    kpi = KPIStrategic.query.get_or_404(kpi_id)
    
    try:
        nom_kpi = kpi.nom
        kpi.delete()
        flash(f'KPI "{nom_kpi}" supprimé avec succès.', 'success')
    except Exception as e:
        flash(f'Erreur lors de la suppression du KPI: {str(e)}', 'error')
    
    return redirect(url_for('are_dashboard.index'))


@dashboard_bp.route('/export/<export_type>/<data_type>')
@login_required
@admin_required
def export_data(export_type, data_type):
    """Exporter des données du dashboard en différents formats"""
    if not current_user.is_super_admin():
        abort(403)
    
    try:
        # Récupérer les services de données
        stats_service = StatistiquesAREService()
        dashboard_service = DashboardAREService()
        
        # Générer le nom de fichier avec timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if export_type == 'excel':
            return _export_to_excel(data_type, timestamp, stats_service, dashboard_service)
        elif export_type == 'csv':
            return _export_to_csv(data_type, timestamp, stats_service, dashboard_service)
        elif export_type == 'json':
            return _export_to_json(data_type, timestamp, stats_service, dashboard_service)
        else:
            flash('Format d\'export non supporté.', 'error')
            return redirect(url_for('are_dashboard.index'))
            
    except Exception as e:
        flash(f'Erreur lors de l\'export: {str(e)}', 'error')
        return redirect(url_for('are_dashboard.index'))


def _export_to_excel(data_type, timestamp, stats_service, dashboard_service):
    """Export en format Excel"""
    if not PANDAS_AVAILABLE:
        flash('Pandas n\'est pas disponible pour l\'export Excel.', 'error')
        return redirect(url_for('are_dashboard.index'))
    
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        if data_type == 'production' or data_type == 'all':
            # Données de production
            stats = stats_service.calculer_statistiques_nationales()
            if stats and stats.evolution_production:
                production_data = []
                for item in stats.evolution_production:
                    production_data.append({
                        'Année': item.annee,
                        'Production Hydro (GWh)': item.production_hydro_gwh,
                        'Production Thermique (GWh)': item.production_thermique_gwh,
                        'Production Solaire (GWh)': item.production_solaire_gwh,
                        'Production Totale (GWh)': item.production_totale_gwh
                    })
                
                if production_data:
                    df_production = pd.DataFrame(production_data)
                    df_production.to_excel(writer, sheet_name='Production', index=False)
        
        if data_type == 'capacite' or data_type == 'all':
            # Données de capacité installée
            stats = stats_service.calculer_statistiques_nationales()
            if stats and stats.evolution_capacite:
                capacite_data = []
                for item in stats.evolution_capacite:
                    capacite_data.append({
                        'Année': item.annee,
                        'Capacité Hydro (MW)': item.capacite_hydro_mw,
                        'Capacité Thermique (MW)': item.capacite_thermique_mw,
                        'Capacité Solaire (MW)': item.capacite_solaire_mw,
                        'Capacité Totale (MW)': item.capacite_totale_mw
                    })
                
                if capacite_data:
                    df_capacite = pd.DataFrame(capacite_data)
                    df_capacite.to_excel(writer, sheet_name='Capacité', index=False)
        
        if data_type == 'kpis' or data_type == 'all':
            # KPIs stratégiques
            kpis = KPIStrategic.query.filter_by(actif=True).all()
            if kpis:
                kpi_data = []
                for kpi in kpis:
                    kpi_data.append({
                        'Nom': kpi.nom,
                        'Valeur': kpi.valeur_actuelle,
                        'Objectif': kpi.valeur_objectif,
                        'Unité': kpi.unite,
                        'Tendance': kpi.tendance,
                        'Dernière MAJ': kpi.date_modification.strftime('%Y-%m-%d %H:%M')
                    })
                
                df_kpis = pd.DataFrame(kpi_data)
                df_kpis.to_excel(writer, sheet_name='KPIs', index=False)
        
        if data_type == 'alertes' or data_type == 'all':
            # Alertes
            alertes = AlerteRegulateur.query.filter_by(actif=True).order_by(
                AlerteRegulateur.date_creation.desc()
            ).limit(100).all()
            
            if alertes:
                alerte_data = []
                for alerte in alertes:
                    alerte_data.append({
                        'Titre': alerte.titre,
                        'Type': alerte.type_alerte,
                        'Niveau': alerte.niveau_urgence,
                        'Statut': alerte.statut,
                        'Description': alerte.description,
                        'Date': alerte.date_creation.strftime('%Y-%m-%d %H:%M')
                    })
                
                df_alertes = pd.DataFrame(alerte_data)
                df_alertes.to_excel(writer, sheet_name='Alertes', index=False)
    
    output.seek(0)
    
    filename = f'are_dashboard_{data_type}_{timestamp}.xlsx'
    
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


def _export_to_csv(data_type, timestamp, stats_service, dashboard_service):
    """Export en format CSV"""
    # Implementation CSV similaire mais plus simple
    pass


def _export_to_json(data_type, timestamp, stats_service, dashboard_service):
    """Export en format JSON"""
    # Implementation JSON
    pass


# Fonction supprimée - dupliquée plus haut avec route différente