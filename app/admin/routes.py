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


@admin.route('/export-database-excel')
@login_required
@require_super_admin
def export_database_excel():
    """Télécharger toute la base de données en format Excel"""
    if not HAS_PANDAS:
        flash('Pandas n\'est pas installé. Impossible d\'exporter en Excel.', 'error')
        return redirect(url_for('admin.backup'))
    
    try:
        # Créer un buffer en mémoire pour le fichier Excel
        output = BytesIO()
        
        # Créer un objet ExcelWriter
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            
            # Exporter les utilisateurs
            users_query = db.session.query(User).filter(User.actif == True)
            if users_query.count() > 0:
                users_df = pd.read_sql(users_query.statement, db.engine)
                # Supprimer la colonne mot de passe pour la sécurité
                if 'mot_de_passe_hash' in users_df.columns:
                    users_df = users_df.drop('mot_de_passe_hash', axis=1)
                users_df.to_excel(writer, sheet_name='Utilisateurs', index=False)
            
            # Exporter les opérateurs
            from app.models.operateurs import Operateur
            operators_query = db.session.query(Operateur).filter(Operateur.actif == True)
            if operators_query.count() > 0:
                operators_df = pd.read_sql(operators_query.statement, db.engine)
                operators_df.to_excel(writer, sheet_name='Operateurs', index=False)
            
            # Exporter les centrales hydro
            from app.models.production_hydro import CentraleHydro, RapportHydro
            centrales_query = db.session.query(CentraleHydro).filter(CentraleHydro.actif == True)
            if centrales_query.count() > 0:
                centrales_df = pd.read_sql(centrales_query.statement, db.engine)
                centrales_df.to_excel(writer, sheet_name='Centrales_Hydro', index=False)
            
            # Exporter les rapports hydro
            rapports_hydro_query = db.session.query(RapportHydro).filter(RapportHydro.actif == True)
            if rapports_hydro_query.count() > 0:
                rapports_df = pd.read_sql(rapports_hydro_query.statement, db.engine)
                rapports_df.to_excel(writer, sheet_name='Rapports_Hydro', index=False)
            
            # Exporter les centrales thermiques
            try:
                from app.models.production_thermique import CentraleThermique, RapportThermique
                centrales_therm_query = db.session.query(CentraleThermique).filter(CentraleThermique.actif == True)
                if centrales_therm_query.count() > 0:
                    centrales_therm_df = pd.read_sql(centrales_therm_query.statement, db.engine)
                    centrales_therm_df.to_excel(writer, sheet_name='Centrales_Thermique', index=False)
                
                rapports_therm_query = db.session.query(RapportThermique).filter(RapportThermique.actif == True)
                if rapports_therm_query.count() > 0:
                    rapports_therm_df = pd.read_sql(rapports_therm_query.statement, db.engine)
                    rapports_therm_df.to_excel(writer, sheet_name='Rapports_Thermique', index=False)
            except ImportError:
                pass
            
            # Exporter les centrales solaires
            try:
                from app.models.production_solaire import CentraleSolaire, RapportSolaire
                centrales_sol_query = db.session.query(CentraleSolaire).filter(CentraleSolaire.actif == True)
                if centrales_sol_query.count() > 0:
                    centrales_sol_df = pd.read_sql(centrales_sol_query.statement, db.engine)
                    centrales_sol_df.to_excel(writer, sheet_name='Centrales_Solaire', index=False)
                
                rapports_sol_query = db.session.query(RapportSolaire).filter(RapportSolaire.actif == True)
                if rapports_sol_query.count() > 0:
                    rapports_sol_df = pd.read_sql(rapports_sol_query.statement, db.engine)
                    rapports_sol_df.to_excel(writer, sheet_name='Rapports_Solaire', index=False)
            except ImportError:
                pass
            
            # Exporter les données de distribution
            try:
                from app.models.distribution import ReseauDistribution, PosteDistribution, FeederDistribution, RapportDistribution
                
                reseaux_query = db.session.query(ReseauDistribution).filter(ReseauDistribution.actif == True)
                if reseaux_query.count() > 0:
                    reseaux_df = pd.read_sql(reseaux_query.statement, db.engine)
                    reseaux_df.to_excel(writer, sheet_name='Reseaux_Distribution', index=False)
                
                postes_query = db.session.query(PosteDistribution).filter(PosteDistribution.actif == True)
                if postes_query.count() > 0:
                    postes_df = pd.read_sql(postes_query.statement, db.engine)
                    postes_df.to_excel(writer, sheet_name='Postes_Distribution', index=False)
                
                feeders_query = db.session.query(FeederDistribution).filter(FeederDistribution.actif == True)
                if feeders_query.count() > 0:
                    feeders_df = pd.read_sql(feeders_query.statement, db.engine)
                    feeders_df.to_excel(writer, sheet_name='Feeders_Distribution', index=False)
                
                rapports_dist_query = db.session.query(RapportDistribution).filter(RapportDistribution.actif == True)
                if rapports_dist_query.count() > 0:
                    rapports_dist_df = pd.read_sql(rapports_dist_query.statement, db.engine)
                    rapports_dist_df.to_excel(writer, sheet_name='Rapports_Distribution', index=False)
            except ImportError:
                pass
            
            # Exporter les données de transport
            try:
                from app.models.transport import LigneTransport, PosteTransport, RapportTransport
                
                lignes_query = db.session.query(LigneTransport).filter(LigneTransport.actif == True)
                if lignes_query.count() > 0:
                    lignes_df = pd.read_sql(lignes_query.statement, db.engine)
                    lignes_df.to_excel(writer, sheet_name='Lignes_Transport', index=False)
                
                postes_trans_query = db.session.query(PosteTransport).filter(PosteTransport.actif == True)
                if postes_trans_query.count() > 0:
                    postes_trans_df = pd.read_sql(postes_trans_query.statement, db.engine)
                    postes_trans_df.to_excel(writer, sheet_name='Postes_Transport', index=False)
                
                rapports_trans_query = db.session.query(RapportTransport).filter(RapportTransport.actif == True)
                if rapports_trans_query.count() > 0:
                    rapports_trans_df = pd.read_sql(rapports_trans_query.statement, db.engine)
                    rapports_trans_df.to_excel(writer, sheet_name='Rapports_Transport', index=False)
            except ImportError:
                pass
            
            # Exporter les données de collecte
            try:
                from app.models.collecte_donnees import CollecteDonneesMensuelles, CollecteProjetNouveau
                
                collecte_query = db.session.query(CollecteDonneesMensuelles).filter(CollecteDonneesMensuelles.actif == True)
                if collecte_query.count() > 0:
                    collecte_df = pd.read_sql(collecte_query.statement, db.engine)
                    collecte_df.to_excel(writer, sheet_name='Collecte_Donnees', index=False)
                
                projets_query = db.session.query(CollecteProjetNouveau).filter(CollecteProjetNouveau.actif == True)
                if projets_query.count() > 0:
                    projets_df = pd.read_sql(projets_query.statement, db.engine)
                    projets_df.to_excel(writer, sheet_name='Nouveaux_Projets', index=False)
            except ImportError:
                pass
            
            # Exporter les notifications
            try:
                from app.models.notifications import Notification
                
                notifications_query = db.session.query(Notification).filter(Notification.actif == True)
                if notifications_query.count() > 0:
                    notifications_df = pd.read_sql(notifications_query.statement, db.engine)
                    notifications_df.to_excel(writer, sheet_name='Notifications', index=False)
            except ImportError:
                pass
        
        # Préparer le fichier pour téléchargement
        output.seek(0)
        
        # Générer nom de fichier avec timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'base_donnees_complete_{timestamp}.xlsx'
        
        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    
    except Exception as e:
        current_app.logger.error(f"Erreur export Excel: {e}")
        flash(f'Erreur lors de l\'export Excel: {str(e)}', 'error')
        return redirect(url_for('admin.backup'))


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