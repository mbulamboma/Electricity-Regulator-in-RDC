"""
Services pour les statistiques complètes ARE
Calculs automatiques basés sur les données des opérateurs
"""
from datetime import datetime, date
from sqlalchemy import func, and_, or_
from app.extensions import db
from app.models.operateurs import Operateur
from app.models.production_hydro import CentraleHydro, RapportHydro
from app.models.production_thermique import CentraleThermique, RapportThermique
from app.models.production_solaire import CentraleSolaire, RapportSolaire
from app.models.transport import LigneTransport, PosteTransport, RapportTransport
from app.models.distribution import ReseauDistribution, PosteDistribution, RapportDistribution
from app.models.statistiques_are import (
    PortfolioProjet, CapaciteInstallee, ProductionSolaire, 
    ClienteleElectricite, StatistiqueNationale, TypeProjet
)


class StatistiquesAREService:
    """Service principal pour les calculs statistiques ARE"""

    @staticmethod
    def calculer_capacite_installee_annuelle(annee):
        """Calcule la capacité installée par source pour une année donnée"""
        try:
            # Supprimer les données existantes pour cette année
            CapaciteInstallee.query.filter_by(annee=annee).delete()
            
            # Calculer capacités hydrauliques
            capacites_hydro = db.session.query(
                CentraleHydro.operateur_id,
                func.sum(CentraleHydro.puissance_installee).label('capacite_totale'),
                func.sum(CentraleHydro.puissance_installee * 0.9).label('capacite_disponible')  # Estimation 90%
            ).filter(
                CentraleHydro.actif == True,
                CentraleHydro.date_mise_service <= date(annee, 12, 31)
            ).group_by(CentraleHydro.operateur_id).all()
            
            for capacite in capacites_hydro:
                # Production annuelle estimée (energie_produite est déjà en MWh)
                production_gwh = db.session.query(
                    func.sum(RapportHydro.energie_produite)
                ).join(CentraleHydro).filter(
                    CentraleHydro.operateur_id == capacite.operateur_id,
                    RapportHydro.annee == annee
                ).scalar() or 0
                production_gwh = production_gwh / 1000  # Conversion MWh -> GWh
                
                capacite_obj = CapaciteInstallee(
                    annee=annee,
                    type_source=TypeProjet.PRODUCTION_HYDRO,
                    operateur_id=capacite.operateur_id,
                    capacite_installee_mw=capacite.capacite_totale or 0,
                    capacite_disponible_mw=capacite.capacite_disponible or 0,
                    production_annuelle_gwh=production_gwh,
                    facteur_charge=StatistiquesAREService._calculer_facteur_charge(
                        capacite.capacite_totale, production_gwh
                    )
                )
                capacite_obj.save()
            
            # Calculer capacités thermiques
            capacites_thermiques = db.session.query(
                CentraleThermique.operateur_id,
                func.sum(CentraleThermique.puissance_installee).label('capacite_totale')
            ).filter(
                CentraleThermique.actif == True,
                CentraleThermique.date_mise_service <= date(annee, 12, 31)
            ).group_by(CentraleThermique.operateur_id).all()
            
            for capacite in capacites_thermiques:
                production_gwh = db.session.query(
                    func.sum(RapportThermique.energie_produite)
                ).join(CentraleThermique).filter(
                    CentraleThermique.operateur_id == capacite.operateur_id,
                    RapportThermique.annee == annee
                ).scalar() or 0
                production_gwh = production_gwh / 1000  # Conversion MWh -> GWh
                
                capacite_obj = CapaciteInstallee(
                    annee=annee,
                    type_source=TypeProjet.PRODUCTION_THERMIQUE,
                    operateur_id=capacite.operateur_id,
                    capacite_installee_mw=capacite.capacite_totale or 0,
                    capacite_disponible_mw=capacite.capacite_totale * 0.85 or 0,  # Estimation 85%
                    production_annuelle_gwh=production_gwh,
                    facteur_charge=StatistiquesAREService._calculer_facteur_charge(
                        capacite.capacite_totale, production_gwh
                    )
                )
                capacite_obj.save()
            
            # Calculer capacités solaires
            capacites_solaires = db.session.query(
                CentraleSolaire.operateur_id,
                func.sum(CentraleSolaire.puissance_installee).label('capacite_totale')
            ).filter(
                CentraleSolaire.actif == True,
                CentraleSolaire.date_mise_service <= date(annee, 12, 31)
            ).group_by(CentraleSolaire.operateur_id).all()
            
            for capacite in capacites_solaires:
                production_gwh = db.session.query(
                    func.sum(RapportSolaire.energie_produite)
                ).join(CentraleSolaire).filter(
                    CentraleSolaire.operateur_id == capacite.operateur_id,
                    RapportSolaire.annee == annee
                ).scalar() or 0
                production_gwh = production_gwh / 1000  # Conversion MWh -> GWh
                
                capacite_obj = CapaciteInstallee(
                    annee=annee,
                    type_source=TypeProjet.PRODUCTION_SOLAIRE,
                    operateur_id=capacite.operateur_id,
                    capacite_installee_mw=capacite.capacite_totale or 0,
                    capacite_disponible_mw=capacite.capacite_totale * 0.80 or 0,  # Estimation 80%
                    production_annuelle_gwh=production_gwh,
                    facteur_charge=StatistiquesAREService._calculer_facteur_charge(
                        capacite.capacite_totale, production_gwh
                    )
                )
                capacite_obj.save()
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"Erreur lors du calcul des capacités installées: {e}")
            return False

    @staticmethod
    def calculer_statistiques_nationales(annee):
        """Calcule les statistiques agrégées au niveau national"""
        try:
            # Supprimer les données existantes pour cette année
            StatistiqueNationale.query.filter_by(annee=annee).delete()
            
            # Calculer les totaux par source
            capacites = db.session.query(
                CapaciteInstallee.type_source,
                func.sum(CapaciteInstallee.capacite_installee_mw).label('total_installee'),
                func.sum(CapaciteInstallee.capacite_disponible_mw).label('total_disponible'),
                func.sum(CapaciteInstallee.production_annuelle_gwh).label('total_production')
            ).filter(
                CapaciteInstallee.annee == annee
            ).group_by(CapaciteInstallee.type_source).all()
            
            # Initialiser les totaux
            stats = {
                'capacite_totale_installee_mw': 0,
                'capacite_totale_disponible_mw': 0,
                'production_totale_annuelle_gwh': 0,
                'capacite_hydro_mw': 0,
                'capacite_thermique_mw': 0,
                'capacite_solaire_mw': 0,
                'production_hydro_gwh': 0,
                'production_thermique_gwh': 0,
                'production_solaire_gwh': 0,
            }
            
            for capacite in capacites:
                stats['capacite_totale_installee_mw'] += capacite.total_installee or 0
                stats['capacite_totale_disponible_mw'] += capacite.total_disponible or 0
                stats['production_totale_annuelle_gwh'] += capacite.total_production or 0
                
                if capacite.type_source == TypeProjet.PRODUCTION_HYDRO:
                    stats['capacite_hydro_mw'] = capacite.total_installee or 0
                    stats['production_hydro_gwh'] = capacite.total_production or 0
                elif capacite.type_source == TypeProjet.PRODUCTION_THERMIQUE:
                    stats['capacite_thermique_mw'] = capacite.total_installee or 0
                    stats['production_thermique_gwh'] = capacite.total_production or 0
                elif capacite.type_source == TypeProjet.PRODUCTION_SOLAIRE:
                    stats['capacite_solaire_mw'] = capacite.total_installee or 0
                    stats['production_solaire_gwh'] = capacite.total_production or 0
            
            # Calculer les statistiques de clientèle
            clientele = db.session.query(
                func.sum(ClienteleElectricite.total_clients).label('total_clients'),
                func.sum(ClienteleElectricite.clients_ht).label('clients_ht'),
                func.sum(ClienteleElectricite.clients_mt).label('clients_mt'),
                func.sum(ClienteleElectricite.clients_bt).label('clients_bt'),
                func.avg(ClienteleElectricite.taux_acces_electricite).label('taux_acces_moy'),
                func.avg(ClienteleElectricite.taux_electrification).label('taux_electrification_moy'),
                func.avg(ClienteleElectricite.taux_couverture_geographique).label('taux_couverture_moy')
            ).filter(
                ClienteleElectricite.annee == annee
            ).first()
            
            if clientele:
                stats.update({
                    'total_clients_nationaux': clientele.total_clients or 0,
                    'clients_ht_nationaux': clientele.clients_ht or 0,
                    'clients_mt_nationaux': clientele.clients_mt or 0,
                    'clients_bt_nationaux': clientele.clients_bt or 0,
                    'taux_acces_national': clientele.taux_acces_moy or 0,
                    'taux_electrification_national': clientele.taux_electrification_moy or 0,
                    'taux_couverture_national': clientele.taux_couverture_moy or 0,
                })
            
            # Compter les opérateurs actifs
            nb_operateurs = Operateur.query.filter(
                Operateur.actif == True,
                Operateur.statut_licence == 'active'
            ).count()
            
            stats['nombre_operateurs_actifs'] = nb_operateurs
            
            # Créer l'enregistrement de statistiques nationales
            stat_nationale = StatistiqueNationale(
                annee=annee,
                **stats,
                date_calcul=datetime.utcnow()
            )
            stat_nationale.save()
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"Erreur lors du calcul des statistiques nationales: {e}")
            return False

    @staticmethod
    def generer_donnees_tableau_solaire():
        """Génère les données pour le tableau solaire basé sur les attachements"""
        try:
            # Données exemple basées sur l'attachment fourni
            donnees_2024 = [
                {
                    'operateur': 'NURU',
                    'type_installation': 'Champs solaires',
                    'production_2024_mwh': 2918.60,
                    'capacite_2024_mw': 1.90
                },
                {
                    'operateur': 'ALTECH',
                    'type_installation': 'Kits solaires',
                    'production_2024_mwh': 0.20,
                    'capacite_2024_mw': 0.20
                },
                {
                    'operateur': 'BBOXX',
                    'type_installation': 'Kits Solaires',
                    'production_2024_mwh': 618.10,
                    'capacite_2024_mw': 1.16
                }
            ]
            
            # Supprimer les données solaires existantes pour 2024
            ProductionSolaire.query.filter_by(annee=2024).delete()
            
            for donnee in donnees_2024:
                # Trouver l'opérateur
                operateur = Operateur.query.filter_by(nom=donnee['operateur']).first()
                
                production = ProductionSolaire(
                    annee=2024,
                    type_installation=donnee['type_installation'].lower().replace(' ', '_'),
                    operateur_id=operateur.id if operateur else None,
                    puissance_installee_mw=donnee['capacite_2024_mw'],
                    production_annuelle_gwh=donnee['production_2024_mwh'] / 1000,  # MWh -> GWh
                    nombre_installations=1  # Valeur par défaut
                )
                production.save()
            
            # Données d'évolution 2020-2024
            evolution_data = [
                {'annee': 2020, 'production_totale_kwh': 253462},
                {'annee': 2021, 'production_totale_kwh': 1074312.72},
                {'annee': 2022, 'production_totale_kwh': 1895163.43},
                {'annee': 2023, 'production_totale_kwh': 2716014.145},
                {'annee': 2024, 'production_totale_kwh': 3536864.86}
            ]
            
            for data in evolution_data:
                if data['annee'] != 2024:  # 2024 déjà traité ci-dessus
                    production = ProductionSolaire(
                        annee=data['annee'],
                        type_installation='nationale',
                        operateur_id=None,  # Données nationales
                        puissance_installee_mw=0,  # À calculer séparément
                        production_annuelle_gwh=data['production_totale_kwh'] / 1000000  # kWh -> GWh
                    )
                    production.save()
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"Erreur lors de la génération des données solaires: {e}")
            return False

    @staticmethod
    def _calculer_facteur_charge(capacite_mw, production_gwh):
        """Calcule le facteur de charge en %"""
        if not capacite_mw or capacite_mw == 0:
            return 0
        # Facteur de charge = Production réelle / Production théorique max
        production_theorique_max_gwh = capacite_mw * 8760 / 1000  # MW * heures/an / 1000
        if production_theorique_max_gwh == 0:
            return 0
        return min(100, (production_gwh / production_theorique_max_gwh) * 100)

    @staticmethod
    def calculer_toutes_statistiques(annee):
        """Lance tous les calculs statistiques pour une année"""
        try:
            print(f"🔄 Calcul des statistiques ARE pour l'année {annee}...")
            
            # 1. Calculer les capacités installées
            print("📊 Calcul des capacités installées...")
            if not StatistiquesAREService.calculer_capacite_installee_annuelle(annee):
                print("❌ Erreur lors du calcul des capacités")
                return False
            
            # 2. Générer les données solaires
            print("☀️ Génération des données solaires...")
            if not StatistiquesAREService.generer_donnees_tableau_solaire():
                print("❌ Erreur lors de la génération des données solaires")
                return False
            
            # 3. Calculer les statistiques nationales
            print("🇨🇩 Calcul des statistiques nationales...")
            if not StatistiquesAREService.calculer_statistiques_nationales(annee):
                print("❌ Erreur lors du calcul des statistiques nationales")
                return False
            
            print(f"✅ Calculs terminés avec succès pour l'année {annee}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur générale lors des calculs: {e}")
            return False


class DashboardAREService:
    """Service pour générer les données du dashboard ARE"""

    @staticmethod
    def get_portfolio_projets():
        """Récupère le portfolio des projets ARE"""
        projets = PortfolioProjet.query.filter_by(actif=True).all()
        return [projet.to_dict() for projet in projets]

    @staticmethod
    def get_evolution_capacite(annee_debut=2020, annee_fin=2024):
        """Récupère l'évolution de la capacité installée"""
        capacites = CapaciteInstallee.query.filter(
            and_(
                CapaciteInstallee.annee >= annee_debut,
                CapaciteInstallee.annee <= annee_fin
            )
        ).order_by(CapaciteInstallee.annee, CapaciteInstallee.type_source).all()
        
        return [capacite.to_dict() for capacite in capacites]

    @staticmethod
    def get_statistiques_nationales_periode(annee_debut=2020, annee_fin=2024):
        """Récupère les statistiques nationales pour une période"""
        stats = StatistiqueNationale.query.filter(
            and_(
                StatistiqueNationale.annee >= annee_debut,
                StatistiqueNationale.annee <= annee_fin
            )
        ).order_by(StatistiqueNationale.annee).all()
        
        return [stat.to_dict() for stat in stats]

    @staticmethod
    def get_donnees_solaires():
        """Récupère les données spécifiques au solaire"""
        productions = ProductionSolaire.query.order_by(
            ProductionSolaire.annee.desc()
        ).all()
        
        return [prod.to_dict() for prod in productions]

    @staticmethod
    def get_statistiques_clientele(annee_debut=2020, annee_fin=2024):
        """Récupère les statistiques de clientèle"""
        clienteles = ClienteleElectricite.query.filter(
            and_(
                ClienteleElectricite.annee >= annee_debut,
                ClienteleElectricite.annee <= annee_fin
            )
        ).order_by(ClienteleElectricite.annee).all()
        
        return [clientele.to_dict() for clientele in clienteles]