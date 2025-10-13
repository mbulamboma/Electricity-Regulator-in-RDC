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
from app.utils.decorators import admin_required
from app.utils.permissions import get_accessible_operateurs


@dashboard_bp.route('/')
@login_required
@admin_required
def index():
    """Page principale du dashboard ARE"""
    form = FiltreTableauBordForm()
    
    # Récupérer les filtres
    annee = request.args.get('annee', datetime.now().year, type=int)
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
                         annee=annee,
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


@dashboard_bp.route('/api/kpis/mettre-a-jour/<int:annee>', methods=['POST'])
@login_required
@admin_required
def api_mettre_a_jour_kpis(annee):
    """API pour mettre à jour les KPIs automatiquement"""
    kpis = IndicateursAREService.mettre_a_jour_kpis_strategiques(annee)
    
    return jsonify({
        'message': f'{len(kpis)} KPIs mis à jour',
        'kpis': [kpi.to_dict() for kpi in kpis]
    })