"""
Routes du module d'administration
"""
import os
import json
from datetime import datetime, timedelta
from flask import render_template, request, jsonify, flash, redirect, url_for, current_app, send_file
from flask_login import login_required, current_user
from sqlalchemy import func, text
from werkzeug.utils import secure_filename
import zipfile
import shutil
from io import BytesIO

# Import optionnel de pandas
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

from . import admin
from app.extensions import db
from app.models.utilisateurs import User
from app.models.operateurs import Operateur
from app.models.production_hydro import CentraleHydro, RapportHydro, GroupeProduction
from .forms import ConfigurationForm, BackupForm
from .utils import (
    get_dashboard_stats, get_production_analytics, 
    create_backup, get_backup_history, generate_report_analytics
)


def require_super_admin(f):
    """Décorateur pour vérifier les droits super admin"""
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_super_admin():
            flash('Accès réservé aux super administrateurs.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function


@admin.route('/dashboard')
@login_required
@require_super_admin
def dashboard():
    """Dashboard principal du super administrateur"""
    try:
        # Statistiques générales
        stats = get_dashboard_stats()
        
        # Données pour les graphiques
        production_data = get_production_analytics()
        
        # Dernières activités
        recent_reports = RapportHydro.query.order_by(RapportHydro.date_creation.desc()).limit(10).all()
        recent_users = User.query.filter(User.derniere_connexion.isnot(None)).order_by(User.derniere_connexion.desc()).limit(5).all()
        
        # Alertes
        alerts = []
        
        # Vérifier les centrales sans rapport récent
        centrales_sans_rapport = db.session.query(CentraleHydro).outerjoin(
            RapportHydro, 
            (CentraleHydro.id == RapportHydro.centrale_id) & 
            (RapportHydro.date_creation >= datetime.now() - timedelta(days=60))
        ).filter(RapportHydro.id.is_(None)).all()
        
        if centrales_sans_rapport:
            alerts.append({
                'type': 'warning',
                'message': f'{len(centrales_sans_rapport)} centrale(s) sans rapport depuis 60 jours',
                'count': len(centrales_sans_rapport)
            })
        
        # Vérifier les rapports en attente de validation
        rapports_en_attente = RapportHydro.query.filter_by(statut='transmis').count()
        if rapports_en_attente > 0:
            alerts.append({
                'type': 'info',
                'message': f'{rapports_en_attente} rapport(s) en attente de validation',
                'count': rapports_en_attente
            })
        
        return render_template('admin/dashboard.html',
                             title='Dashboard Administrateur',
                             current_time=datetime.now(),
                             stats=stats,
                             production_data=production_data,
                             recent_reports=recent_reports,
                             recent_users=recent_users,
                             alerts=alerts)
    
    except Exception as e:
        current_app.logger.error(f"Erreur dashboard admin: {e}")
        flash('Erreur lors du chargement du dashboard.', 'error')
        return redirect(url_for('main.index'))


@admin.route('/analytics')
@login_required
@require_super_admin
def analytics():
    """Page d'analyses avancées"""
    try:
        # Paramètres de filtre
        annee = request.args.get('annee', datetime.now().year, type=int)
        mois = request.args.get('mois', type=int)
        operateur_id = request.args.get('operateur_id', type=int)
        
        # Données d'analyse
        analytics_data = generate_report_analytics(
            annee=annee,
            mois=mois,
            operateur_id=operateur_id
        )
        
        # Liste des opérateurs pour le filtre
        operateurs = Operateur.query.filter_by(actif=True).all()
        
        # Années disponibles
        annees = db.session.query(func.extract('year', RapportHydro.date_creation)).distinct().all()
        annees = sorted([int(a[0]) for a in annees if a[0]], reverse=True)
        
        return render_template('admin/analytics.html',
                             title='Analyses Avancées',
                             analytics_data=analytics_data,
                             operateurs=operateurs,
                             annees=annees,
                             filters={'annee': annee, 'mois': mois, 'operateur_id': operateur_id})
    
    except Exception as e:
        current_app.logger.error(f"Erreur analytics: {e}")
        flash('Erreur lors du chargement des analyses.', 'error')
        return redirect(url_for('admin.dashboard'))


@admin.route('/backup', methods=['GET', 'POST'])
@login_required
@require_super_admin
def backup():
    """Gestion des sauvegardes"""
    form = BackupForm()
    
    if form.validate_on_submit():
        try:
            backup_type = form.backup_type.data
            include_files = form.include_files.data
            
            # Créer la sauvegarde
            backup_path = create_backup(backup_type, include_files)
            
            if backup_path:
                flash('Sauvegarde créée avec succès!', 'success')
                # Télécharger le fichier
                return send_file(backup_path, as_attachment=True)
            else:
                flash('Erreur lors de la création de la sauvegarde.', 'error')
        
        except Exception as e:
            current_app.logger.error(f"Erreur sauvegarde: {e}")
            flash('Erreur lors de la sauvegarde.', 'error')
    
    # Historique des sauvegardes
    backup_history = get_backup_history()
    
    return render_template('admin/backup.html',
                         title='Gestion des Sauvegardes',
                         form=form,
                         backup_history=backup_history)


@admin.route('/config', methods=['GET', 'POST'])
@login_required
@require_super_admin
def config():
    """Configuration système"""
    form = ConfigurationForm()
    
    if form.validate_on_submit():
        try:
            # Sauvegarder la configuration
            config_data = {
                'maintenance_mode': form.maintenance_mode.data,
                'backup_retention_days': form.backup_retention_days.data,
                'alert_email': form.alert_email.data,
                'max_file_size': form.max_file_size.data,
                'report_deadline_days': form.report_deadline_days.data,
                'auto_backup_enabled': form.auto_backup_enabled.data,
                'auto_backup_frequency': form.auto_backup_frequency.data
            }
            
            # Sauvegarder dans un fichier de configuration
            config_file = os.path.join(current_app.instance_path, 'admin_config.json')
            os.makedirs(os.path.dirname(config_file), exist_ok=True)
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            flash('Configuration sauvegardée avec succès!', 'success')
            
        except Exception as e:
            current_app.logger.error(f"Erreur config: {e}")
            flash('Erreur lors de la sauvegarde de la configuration.', 'error')
    
    # Charger la configuration existante
    try:
        config_file = os.path.join(current_app.instance_path, 'admin_config.json')
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                
            # Pré-remplir le formulaire
            form.maintenance_mode.data = config_data.get('maintenance_mode', False)
            form.backup_retention_days.data = config_data.get('backup_retention_days', 30)
            form.alert_email.data = config_data.get('alert_email', '')
            form.max_file_size.data = config_data.get('max_file_size', 16)
            form.report_deadline_days.data = config_data.get('report_deadline_days', 5)
            form.auto_backup_enabled.data = config_data.get('auto_backup_enabled', False)
            form.auto_backup_frequency.data = config_data.get('auto_backup_frequency', 'weekly')
    
    except Exception as e:
        current_app.logger.error(f"Erreur chargement config: {e}")
    
    return render_template('admin/config.html',
                         title='Configuration Système',
                         form=form)


@admin.route('/api/chart-data/<chart_type>')
@login_required
@require_super_admin
def api_chart_data(chart_type):
    """API pour les données des graphiques"""
    try:
        data = {}
        
        if chart_type == 'production_mensuelle':
            # Production par mois sur les 12 derniers mois
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            
            query = db.session.query(
                func.extract('year', RapportHydro.date_creation).label('annee'),
                func.extract('month', RapportHydro.date_creation).label('mois'),
                func.sum(RapportHydro.energie_produite).label('total_energie')
            ).filter(
                RapportHydro.date_creation >= start_date,
                RapportHydro.energie_produite.isnot(None)
            ).group_by('annee', 'mois').order_by('annee', 'mois').all()
            
            data = {
                'labels': [f"{int(r.mois):02d}/{int(r.annee)}" for r in query],
                'datasets': [{
                    'label': 'Production (MWh)',
                    'data': [float(r.total_energie or 0) for r in query],
                    'backgroundColor': 'rgba(54, 162, 235, 0.2)',
                    'borderColor': 'rgba(54, 162, 235, 1)',
                    'borderWidth': 2
                }]
            }
        
        elif chart_type == 'repartition_operateurs':
            # Répartition de la production par opérateur
            query = db.session.query(
                Operateur.nom,
                func.sum(RapportHydro.energie_produite).label('total_energie')
            ).join(
                CentraleHydro, Operateur.id == CentraleHydro.operateur_id
            ).join(
                RapportHydro, CentraleHydro.id == RapportHydro.centrale_id
            ).filter(
                RapportHydro.energie_produite.isnot(None)
            ).group_by(Operateur.nom).all()
            
            data = {
                'labels': [r.nom for r in query],
                'datasets': [{
                    'label': 'Production (MWh)',
                    'data': [float(r.total_energie or 0) for r in query],
                    'backgroundColor': [
                        'rgba(255, 99, 132, 0.2)',
                        'rgba(54, 162, 235, 0.2)',
                        'rgba(255, 205, 86, 0.2)',
                        'rgba(75, 192, 192, 0.2)',
                        'rgba(153, 102, 255, 0.2)',
                    ],
                    'borderColor': [
                        'rgba(255, 99, 132, 1)',
                        'rgba(54, 162, 235, 1)',
                        'rgba(255, 205, 86, 1)',
                        'rgba(75, 192, 192, 1)',
                        'rgba(153, 102, 255, 1)',
                    ],
                    'borderWidth': 1
                }]
            }
        
        elif chart_type == 'taux_remplissage':
            # Taux de remplissage des rapports par mois
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            
            # Nombre total de centrales actives
            total_centrales = CentraleHydro.query.filter_by(actif=True).count()
            
            query = db.session.query(
                func.extract('year', RapportHydro.date_creation).label('annee'),
                func.extract('month', RapportHydro.date_creation).label('mois'),
                func.count(RapportHydro.id).label('nb_rapports')
            ).filter(
                RapportHydro.date_creation >= start_date
            ).group_by('annee', 'mois').order_by('annee', 'mois').all()
            
            data = {
                'labels': [f"{int(r.mois):02d}/{int(r.annee)}" for r in query],
                'datasets': [{
                    'label': 'Taux de remplissage (%)',
                    'data': [round((r.nb_rapports / max(total_centrales, 1)) * 100, 1) for r in query],
                    'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                    'borderColor': 'rgba(75, 192, 192, 1)',
                    'borderWidth': 2
                }]
            }
        
        return jsonify(data)
    
    except Exception as e:
        current_app.logger.error(f"Erreur API chart data: {e}")
        return jsonify({'error': str(e)}), 500


@admin.route('/export/<export_type>')
@login_required
@require_super_admin
def export_data(export_type):
    """Export des données en différents formats"""
    try:
        if export_type == 'rapports_csv':
            # Export CSV de tous les rapports
            query = db.session.query(
                RapportHydro,
                CentraleHydro.nom.label('centrale_nom'),
                Operateur.nom.label('operateur_nom')
            ).join(
                CentraleHydro, RapportHydro.centrale_id == CentraleHydro.id
            ).join(
                Operateur, CentraleHydro.operateur_id == Operateur.id
            ).all()
            
            # Créer fichier temporaire
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'rapports_production_{timestamp}.csv'
            filepath = os.path.join(current_app.instance_path, 'exports', filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            if HAS_PANDAS:
                # Utiliser pandas si disponible
                data = []
                for rapport, centrale_nom, operateur_nom in query:
                    data.append({
                        'ID': rapport.id,
                        'Centrale': centrale_nom,
                        'Opérateur': operateur_nom,
                        'Année': rapport.annee,
                        'Mois': rapport.mois,
                        'Énergie Produite (MWh)': rapport.energie_produite,
                        'Facteur de Charge (%)': rapport.facteur_charge,
                        'Statut': rapport.statut,
                        'Date Création': rapport.date_creation.strftime('%Y-%m-%d %H:%M')
                    })
                
                df = pd.DataFrame(data)
                df.to_csv(filepath, index=False, encoding='utf-8-sig')
            else:
                # Utiliser CSV standard
                import csv
                with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
                    fieldnames = ['ID', 'Centrale', 'Opérateur', 'Année', 'Mois', 
                                'Énergie Produite (MWh)', 'Facteur de Charge (%)', 
                                'Statut', 'Date Création']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for rapport, centrale_nom, operateur_nom in query:
                        writer.writerow({
                            'ID': rapport.id,
                            'Centrale': centrale_nom,
                            'Opérateur': operateur_nom,
                            'Année': rapport.annee,
                            'Mois': rapport.mois,
                            'Énergie Produite (MWh)': rapport.energie_produite or '',
                            'Facteur de Charge (%)': rapport.facteur_charge or '',
                            'Statut': rapport.statut,
                            'Date Création': rapport.date_creation.strftime('%Y-%m-%d %H:%M')
                        })
            
            return send_file(filepath, as_attachment=True, download_name=filename)
        
        elif export_type == 'operateurs_excel':
            if not HAS_PANDAS:
                flash('Export Excel non disponible. Utilisez l\'export CSV.', 'warning')
                return redirect(url_for('admin.dashboard'))
                
            # Export Excel des opérateurs avec leurs centrales
            operateurs = Operateur.query.filter_by(actif=True).all()
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'operateurs_centrales_{timestamp}.xlsx'
            filepath = os.path.join(current_app.instance_path, 'exports', filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # Feuille opérateurs
                operateurs_data = []
                for op in operateurs:
                    operateurs_data.append({
                        'ID': op.id,
                        'Nom': op.nom,
                        'Type': op.type_operateur,
                        'Licence': op.numero_licence,
                        'Statut Licence': op.statut_licence,
                        'Province': op.province,
                        'Nombre Centrales': len(op.centrales_hydro),
                        'Date Création': op.date_creation.strftime('%Y-%m-%d')
                    })
                
                df_operateurs = pd.DataFrame(operateurs_data)
                df_operateurs.to_excel(writer, sheet_name='Opérateurs', index=False)
                
                # Feuille centrales
                centrales_data = []
                for centrale in CentraleHydro.query.filter_by(actif=True).all():
                    centrales_data.append({
                        'ID': centrale.id,
                        'Nom': centrale.nom,
                        'Code': centrale.code,
                        'Opérateur': centrale.operateur.nom if centrale.operateur else '',
                        'Province': centrale.province,
                        'Puissance Installée (MW)': centrale.puissance_installee,
                        'Type': centrale.type_centrale,
                        'Date Mise en Service': centrale.date_mise_service.strftime('%Y-%m-%d') if centrale.date_mise_service else '',
                        'Nombre Groupes': centrale.nombre_groupes
                    })
                
                df_centrales = pd.DataFrame(centrales_data)
                df_centrales.to_excel(writer, sheet_name='Centrales', index=False)
            
            return send_file(filepath, as_attachment=True, download_name=filename)
    
    except Exception as e:
        current_app.logger.error(f"Erreur export: {e}")
        flash('Erreur lors de l\'export des données.', 'error')
        return redirect(url_for('admin.dashboard'))


@admin.route('/api/stats')
@login_required
@require_super_admin
def api_stats():
    """API pour les statistiques en temps réel"""
    try:
        stats = get_dashboard_stats()
        return jsonify(stats)
    except Exception as e:
        current_app.logger.error(f"Erreur API stats: {e}")
        return jsonify({'error': str(e)}), 500