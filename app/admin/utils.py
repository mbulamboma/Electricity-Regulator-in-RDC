"""
Utilitaires pour le module d'administration
"""
import os
import json
import sqlite3
import shutil
import zipfile
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from flask import current_app
from sqlalchemy import func, text

# Import optionnel de pandas
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

from app.extensions import db
from app.models.utilisateurs import User
from app.models.operateurs import Operateur
from app.models.production_hydro import CentraleHydro, RapportHydro, GroupeProduction


def get_dashboard_stats() -> Dict:
    """Récupérer les statistiques pour le dashboard"""
    try:
        stats = {}
        
        # Statistiques générales
        stats['total_operateurs'] = Operateur.query.filter_by(actif=True).count()
        stats['total_centrales'] = CentraleHydro.query.filter_by(actif=True).count()
        stats['total_utilisateurs'] = User.query.filter_by(actif=True).count()
        
        # Rapports
        stats['total_rapports'] = RapportHydro.query.count()
        stats['rapports_ce_mois'] = RapportHydro.query.filter(
            func.extract('month', RapportHydro.date_creation) == datetime.now().month,
            func.extract('year', RapportHydro.date_creation) == datetime.now().year
        ).count()
        
        # Production totale
        total_production = db.session.query(
            func.sum(RapportHydro.energie_produite)
        ).filter(
            RapportHydro.energie_produite.isnot(None)
        ).scalar()
        stats['total_production_gwh'] = round((total_production or 0) / 1000, 2)
        
        # Production ce mois
        production_mois = db.session.query(
            func.sum(RapportHydro.energie_produite)
        ).filter(
            RapportHydro.energie_produite.isnot(None),
            func.extract('month', RapportHydro.date_creation) == datetime.now().month,
            func.extract('year', RapportHydro.date_creation) == datetime.now().year
        ).scalar()
        stats['production_mois_mwh'] = round(production_mois or 0, 1)
        
        # Puissance installée totale
        puissance_totale = db.session.query(
            func.sum(CentraleHydro.puissance_installee)
        ).filter(
            CentraleHydro.puissance_installee.isnot(None),
            CentraleHydro.actif == True
        ).scalar()
        stats['puissance_installee_mw'] = round(puissance_totale or 0, 1)
        
        # Facteur de charge moyen
        facteur_charge_moy = db.session.query(
            func.avg(RapportHydro.facteur_charge)
        ).filter(
            RapportHydro.facteur_charge.isnot(None)
        ).scalar()
        stats['facteur_charge_moyen'] = round(facteur_charge_moy or 0, 1)
        
        # Évolution mensuelle (derniers 6 mois)
        six_mois_ago = datetime.now() - timedelta(days=180)
        evolution = db.session.query(
            func.extract('month', RapportHydro.date_creation).label('mois'),
            func.sum(RapportHydro.energie_produite).label('production')
        ).filter(
            RapportHydro.date_creation >= six_mois_ago,
            RapportHydro.energie_produite.isnot(None)
        ).group_by('mois').order_by('mois').all()
        
        if len(evolution) >= 2:
            derniere_production = evolution[-1].production or 0
            avant_derniere = evolution[-2].production or 0
            if avant_derniere > 0:
                variation = ((derniere_production - avant_derniere) / avant_derniere) * 100
                stats['variation_production'] = round(variation, 1)
            else:
                stats['variation_production'] = 0
        else:
            stats['variation_production'] = 0
        
        # Taux de remplissage des rapports
        mois_courant = datetime.now().month
        annee_courante = datetime.now().year
        
        rapports_mois = RapportHydro.query.filter(
            func.extract('month', RapportHydro.date_creation) == mois_courant,
            func.extract('year', RapportHydro.date_creation) == annee_courante
        ).count()
        
        centrales_actives = CentraleHydro.query.filter_by(actif=True).count()
        
        if centrales_actives > 0:
            stats['taux_remplissage'] = round((rapports_mois / centrales_actives) * 100, 1)
        else:
            stats['taux_remplissage'] = 0
        
        return stats
    
    except Exception as e:
        current_app.logger.error(f"Erreur get_dashboard_stats: {e}")
        return {}


def get_production_analytics() -> Dict:
    """Données d'analyse de production pour les graphiques"""
    try:
        data = {}
        
        # Production par mois (12 derniers mois)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        monthly_production = db.session.query(
            func.extract('year', RapportHydro.date_creation).label('annee'),
            func.extract('month', RapportHydro.date_creation).label('mois'),
            func.sum(RapportHydro.energie_produite).label('total_energie'),
            func.count(RapportHydro.id).label('nb_rapports')
        ).filter(
            RapportHydro.date_creation >= start_date,
            RapportHydro.energie_produite.isnot(None)
        ).group_by('annee', 'mois').order_by('annee', 'mois').all()
        
        data['monthly_labels'] = []
        data['monthly_production'] = []
        data['monthly_reports'] = []
        
        for row in monthly_production:
            label = f"{int(row.mois):02d}/{int(row.annee)}"
            data['monthly_labels'].append(label)
            data['monthly_production'].append(float(row.total_energie or 0))
            data['monthly_reports'].append(row.nb_rapports)
        
        # Production par opérateur
        operator_production = db.session.query(
            Operateur.nom,
            func.sum(RapportHydro.energie_produite).label('total_energie')
        ).join(
            CentraleHydro, Operateur.id == CentraleHydro.operateur_id
        ).join(
            RapportHydro, CentraleHydro.id == RapportHydro.centrale_id
        ).filter(
            RapportHydro.energie_produite.isnot(None)
        ).group_by(Operateur.nom).all()
        
        data['operator_labels'] = [row.nom for row in operator_production]
        data['operator_production'] = [float(row.total_energie or 0) for row in operator_production]
        
        # Production par province
        province_production = db.session.query(
            CentraleHydro.province,
            func.sum(RapportHydro.energie_produite).label('total_energie')
        ).join(
            RapportHydro, CentraleHydro.id == RapportHydro.centrale_id
        ).filter(
            RapportHydro.energie_produite.isnot(None),
            CentraleHydro.province.isnot(None)
        ).group_by(CentraleHydro.province).all()
        
        data['province_labels'] = [row.province for row in province_production]
        data['province_production'] = [float(row.total_energie or 0) for row in province_production]
        
        return data
    
    except Exception as e:
        current_app.logger.error(f"Erreur get_production_analytics: {e}")
        return {}


def generate_report_analytics(annee: Optional[int] = None, 
                            mois: Optional[int] = None,
                            operateur_id: Optional[int] = None) -> Dict:
    """Générer des analyses détaillées des rapports"""
    try:
        data = {}
        
        # Construire la requête de base
        query = db.session.query(RapportHydro).join(
            CentraleHydro, RapportHydro.centrale_id == CentraleHydro.id
        )
        
        # Appliquer les filtres
        if annee:
            query = query.filter(func.extract('year', RapportHydro.date_creation) == annee)
        if mois:
            query = query.filter(func.extract('month', RapportHydro.date_creation) == mois)
        if operateur_id:
            query = query.filter(CentraleHydro.operateur_id == operateur_id)
        
        rapports = query.all()
        
        if rapports:
            # Statistiques de base
            data['total_rapports'] = len(rapports)
            data['energie_totale'] = sum(r.energie_produite or 0 for r in rapports)
            data['energie_moyenne'] = data['energie_totale'] / len(rapports) if rapports else 0
            
            # Facteur de charge
            facteurs_charge = [r.facteur_charge for r in rapports if r.facteur_charge is not None]
            if facteurs_charge:
                data['facteur_charge_moyen'] = sum(facteurs_charge) / len(facteurs_charge)
                data['facteur_charge_min'] = min(facteurs_charge)
                data['facteur_charge_max'] = max(facteurs_charge)
            else:
                data['facteur_charge_moyen'] = 0
                data['facteur_charge_min'] = 0
                data['facteur_charge_max'] = 0
            
            # Répartition par statut
            statuts = {}
            for rapport in rapports:
                statuts[rapport.statut] = statuts.get(rapport.statut, 0) + 1
            data['repartition_statuts'] = statuts
            
            # Top 5 centrales par production
            centrales_production = {}
            for rapport in rapports:
                nom_centrale = rapport.centrale.nom
                if nom_centrale not in centrales_production:
                    centrales_production[nom_centrale] = 0
                centrales_production[nom_centrale] += rapport.energie_produite or 0
            
            top_centrales = sorted(centrales_production.items(), 
                                 key=lambda x: x[1], reverse=True)[:5]
            data['top_centrales'] = [{'nom': nom, 'production': prod} for nom, prod in top_centrales]
            
            # Incidents et maintenance
            total_incidents = sum(r.incidents_majeurs or 0 for r in rapports)
            total_maintenances = sum((r.maintenances_preventives or 0) + (r.maintenances_correctives or 0) for r in rapports)
            
            data['total_incidents'] = total_incidents
            data['total_maintenances'] = total_maintenances
            data['taux_incidents'] = (total_incidents / len(rapports)) if rapports else 0
            
        else:
            # Pas de données
            data = {
                'total_rapports': 0,
                'energie_totale': 0,
                'energie_moyenne': 0,
                'facteur_charge_moyen': 0,
                'facteur_charge_min': 0,
                'facteur_charge_max': 0,
                'repartition_statuts': {},
                'top_centrales': [],
                'total_incidents': 0,
                'total_maintenances': 0,
                'taux_incidents': 0
            }
        
        return data
    
    except Exception as e:
        current_app.logger.error(f"Erreur generate_report_analytics: {e}")
        return {}


def create_backup(backup_type: str, include_files: bool = True) -> Optional[str]:
    """Créer une sauvegarde"""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = os.path.join(current_app.instance_path, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        if backup_type == 'database':
            # Sauvegarde base de données uniquement
            db_path = os.path.join(current_app.instance_path, 'database.db')
            backup_filename = f'backup_database_{timestamp}.db'
            backup_path = os.path.join(backup_dir, backup_filename)
            
            if os.path.exists(db_path):
                shutil.copy2(db_path, backup_path)
                return backup_path
        
        elif backup_type == 'files':
            # Sauvegarde fichiers uniquement
            backup_filename = f'backup_files_{timestamp}.zip'
            backup_path = os.path.join(backup_dir, backup_filename)
            
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Inclure les fichiers statiques uploadés
                static_dir = os.path.join(current_app.root_path, 'static', 'uploads')
                if os.path.exists(static_dir):
                    for root, dirs, files in os.walk(static_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arc_name = os.path.relpath(file_path, static_dir)
                            zipf.write(file_path, arc_name)
            
            return backup_path
        
        elif backup_type == 'complete':
            # Sauvegarde complète
            backup_filename = f'backup_complete_{timestamp}.zip'
            backup_path = os.path.join(backup_dir, backup_filename)
            
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Base de données
                db_path = os.path.join(current_app.instance_path, 'database.db')
                if os.path.exists(db_path):
                    zipf.write(db_path, 'database.db')
                
                # Fichiers de configuration
                config_file = os.path.join(current_app.instance_path, 'admin_config.json')
                if os.path.exists(config_file):
                    zipf.write(config_file, 'admin_config.json')
                
                # Fichiers uploadés si demandé
                if include_files:
                    static_dir = os.path.join(current_app.root_path, 'static', 'uploads')
                    if os.path.exists(static_dir):
                        for root, dirs, files in os.walk(static_dir):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arc_name = os.path.join('uploads', os.path.relpath(file_path, static_dir))
                                zipf.write(file_path, arc_name)
            
            return backup_path
        
        return None
    
    except Exception as e:
        current_app.logger.error(f"Erreur create_backup: {e}")
        return None


def get_backup_history() -> List[Dict]:
    """Récupérer l'historique des sauvegardes"""
    try:
        backup_dir = os.path.join(current_app.instance_path, 'backups')
        if not os.path.exists(backup_dir):
            return []
        
        backups = []
        for filename in os.listdir(backup_dir):
            if filename.startswith('backup_'):
                filepath = os.path.join(backup_dir, filename)
                stat = os.stat(filepath)
                
                backups.append({
                    'filename': filename,
                    'size': round(stat.st_size / (1024 * 1024), 2),  # MB
                    'date': datetime.fromtimestamp(stat.st_mtime),
                    'type': 'Complète' if 'complete' in filename else 
                            'Base de données' if 'database' in filename else 'Fichiers'
                })
        
        # Trier par date décroissante
        backups.sort(key=lambda x: x['date'], reverse=True)
        return backups
    
    except Exception as e:
        current_app.logger.error(f"Erreur get_backup_history: {e}")
        return []


def cleanup_old_backups(retention_days: int = 30):
    """Nettoyer les anciennes sauvegardes"""
    try:
        backup_dir = os.path.join(current_app.instance_path, 'backups')
        if not os.path.exists(backup_dir):
            return
        
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        for filename in os.listdir(backup_dir):
            if filename.startswith('backup_'):
                filepath = os.path.join(backup_dir, filename)
                file_date = datetime.fromtimestamp(os.path.getmtime(filepath))
                
                if file_date < cutoff_date:
                    os.remove(filepath)
                    current_app.logger.info(f"Sauvegarde supprimée: {filename}")
    
    except Exception as e:
        current_app.logger.error(f"Erreur cleanup_old_backups: {e}")


def get_system_info() -> Dict:
    """Informations système pour le monitoring"""
    try:
        import psutil
        
        info = {
            'disk_usage': psutil.disk_usage('/').percent,
            'memory_usage': psutil.virtual_memory().percent,
            'cpu_usage': psutil.cpu_percent(interval=1),
            'uptime': datetime.now() - datetime.fromtimestamp(psutil.boot_time())
        }
        return info
    
    except ImportError:
        # psutil non disponible
        return {
            'disk_usage': 0,
            'memory_usage': 0,
            'cpu_usage': 0,
            'uptime': timedelta(0)
        }
    except Exception as e:
        current_app.logger.error(f"Erreur get_system_info: {e}")
        return {}