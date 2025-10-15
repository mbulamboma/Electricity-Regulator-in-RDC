"""
Service pour calculer les statistiques ARE basées sur les données réelles
au lieu d'utiliser des données fictives
"""
from datetime import datetime, date
from sqlalchemy import func, and_, or_
from app.extensions import db
from app.models.operateurs import Operateur
from app.models.production_hydro import CentraleHydro, RapportHydro
from app.models.production_thermique import CentraleThermique, RapportThermique
from app.models.production_solaire import CentraleSolaire, RapportSolaire
from app.models.transport import LigneTransport, PosteTransport
from app.models.distribution import ReseauDistribution, PosteDistribution
from app.models.collecte_donnees import CollecteDonneesMensuelles, CollecteProjetNouveau
from app.models.statistiques_are import (
    CapaciteInstallee, StatistiqueNationale, ClienteleElectricite, 
    ProductionSolaire as ProductionSolaireStats
)


class CalculStatistiquesReellesService:
    """Service de calcul des statistiques basées sur les données réelles"""

    @staticmethod
    def calculer_capacites_installees_reelles(annee):
        """
        Calcule les capacités installées basées sur les centrales déclarées
        au lieu de données fictives
        """
        print(f"📊 Calcul des capacités installées réelles pour {annee}...")
        
        try:
            # Supprimer les données fictives existantes
            CapaciteInstallee.query.filter_by(annee=annee).delete()
            
            # 1. CAPACITÉS HYDRAULIQUES RÉELLES
            capacites_hydro = db.session.query(
                CentraleHydro.operateur_id,
                func.sum(CentraleHydro.puissance_installee).label('capacite_totale'),
                func.count(CentraleHydro.id).label('nb_centrales')
            ).filter(
                CentraleHydro.actif == True,
                or_(
                    CentraleHydro.date_mise_service <= date(annee, 12, 31),
                    CentraleHydro.date_mise_service.is_(None)
                )
            ).group_by(CentraleHydro.operateur_id).all()
            
            for capacite in capacites_hydro:
                # Production réelle basée sur les rapports
                production_reelle = db.session.query(
                    func.sum(RapportHydro.production_totale_kwh)
                ).filter(
                    RapportHydro.operateur_id == capacite.operateur_id,
                    func.extract('year', RapportHydro.date_debut) == annee
                ).scalar() or 0
                
                production_gwh = production_reelle / 1000000  # kWh -> GWh
                
                capacite_obj = CapaciteInstallee(
                    annee=annee,
                    type_source='production_hydro',
                    operateur_id=capacite.operateur_id,
                    capacite_installee_mw=capacite.capacite_totale or 0,
                    capacite_disponible_mw=(capacite.capacite_totale or 0) * 0.90,  # 90% disponible
                    production_annuelle_gwh=production_gwh,
                    facteur_charge=CalculStatistiquesReellesService._calculer_facteur_charge_reel(
                        capacite.capacite_totale, production_gwh
                    )
                )
                capacite_obj.save()
                print(f"  ✅ Hydro {capacite.operateur_id}: {capacite.capacite_totale} MW, {production_gwh:.2f} GWh")
            
            # 2. CAPACITÉS THERMIQUES RÉELLES
            capacites_thermiques = db.session.query(
                CentraleThermique.operateur_id,
                func.sum(CentraleThermique.puissance_installee).label('capacite_totale')
            ).filter(
                CentraleThermique.actif == True,
                or_(
                    CentraleThermique.date_mise_service <= date(annee, 12, 31),
                    CentraleThermique.date_mise_service.is_(None)
                )
            ).group_by(CentraleThermique.operateur_id).all()
            
            for capacite in capacites_thermiques:
                production_reelle = db.session.query(
                    func.sum(RapportThermique.production_totale_kwh)
                ).filter(
                    RapportThermique.operateur_id == capacite.operateur_id,
                    func.extract('year', RapportThermique.date_debut) == annee
                ).scalar() or 0
                
                production_gwh = production_reelle / 1000000
                
                capacite_obj = CapaciteInstallee(
                    annee=annee,
                    type_source='production_thermique',
                    operateur_id=capacite.operateur_id,
                    capacite_installee_mw=capacite.capacite_totale or 0,
                    capacite_disponible_mw=(capacite.capacite_totale or 0) * 0.85,  # 85% disponible
                    production_annuelle_gwh=production_gwh,
                    facteur_charge=CalculStatistiquesReellesService._calculer_facteur_charge_reel(
                        capacite.capacite_totale, production_gwh
                    )
                )
                capacite_obj.save()
                print(f"  ✅ Thermique {capacite.operateur_id}: {capacite.capacite_totale} MW, {production_gwh:.2f} GWh")
            
            # 3. CAPACITÉS SOLAIRES RÉELLES
            capacites_solaires = db.session.query(
                CentraleSolaire.operateur_id,
                func.sum(CentraleSolaire.puissance_installee).label('capacite_totale')
            ).filter(
                CentraleSolaire.actif == True,
                or_(
                    CentraleSolaire.date_mise_service <= date(annee, 12, 31),
                    CentraleSolaire.date_mise_service.is_(None)
                )
            ).group_by(CentraleSolaire.operateur_id).all()
            
            for capacite in capacites_solaires:
                production_reelle = db.session.query(
                    func.sum(RapportSolaire.production_totale_kwh)
                ).filter(
                    RapportSolaire.operateur_id == capacite.operateur_id,
                    func.extract('year', RapportSolaire.date_debut) == annee
                ).scalar() or 0
                
                production_gwh = production_reelle / 1000000
                
                capacite_obj = CapaciteInstallee(
                    annee=annee,
                    type_source='production_solaire',
                    operateur_id=capacite.operateur_id,
                    capacite_installee_mw=capacite.capacite_totale or 0,
                    capacite_disponible_mw=(capacite.capacite_totale or 0) * 0.80,  # 80% disponible
                    production_annuelle_gwh=production_gwh,
                    facteur_charge=CalculStatistiquesReellesService._calculer_facteur_charge_reel(
                        capacite.capacite_totale, production_gwh
                    )
                )
                capacite_obj.save()
                print(f"  ✅ Solaire {capacite.operateur_id}: {capacite.capacite_totale} MW, {production_gwh:.2f} GWh")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erreur calcul capacités: {e}")
            return False

    @staticmethod
    def calculer_clientele_reelle_depuis_collecte(annee):
        """
        Calcule les statistiques de clientèle basées sur les collectes mensuelles
        des opérateurs au lieu de données fictives
        """
        print(f"👥 Calcul de la clientèle réelle pour {annee}...")
        
        try:
            # Supprimer les données fictives existantes
            ClienteleElectricite.query.filter_by(annee=annee).delete()
            
            # Agrégation des données de collecte par opérateur
            operateurs = Operateur.query.filter_by(actif=True).all()
            
            for operateur in operateurs:
                # Récupérer toutes les collectes validées de l'opérateur pour cette année
                collectes = CollecteDonneesMensuelles.query.filter(
                    CollecteDonneesMensuelles.operateur_id == operateur.id,
                    CollecteDonneesMensuelles.annee == annee,
                    CollecteDonneesMensuelles.statut == 'valide'
                ).all()
                
                if not collectes:
                    print(f"  ⚠️  Aucune collecte validée pour {operateur.nom} en {annee}")
                    continue
                
                # Calculer les totaux à partir des collectes mensuelles
                total_nouveaux_clients_ht = sum(c.nouveaux_clients_ht_mois or 0 for c in collectes)
                total_nouveaux_clients_mt = sum(c.nouveaux_clients_mt_mois or 0 for c in collectes)
                total_nouveaux_clients_bt = sum(c.nouveaux_clients_bt_mois or 0 for c in collectes)
                
                total_deconnexions_ht = sum(c.clients_deconnectes_ht_mois or 0 for c in collectes)
                total_deconnexions_mt = sum(c.clients_deconnectes_mt_mois or 0 for c in collectes)
                total_deconnexions_bt = sum(c.clients_deconnectes_bt_mois or 0 for c in collectes)
                
                # Clients nets (nouveaux - déconnectés)
                clients_ht_nets = total_nouveaux_clients_ht - total_deconnexions_ht
                clients_mt_nets = total_nouveaux_clients_mt - total_deconnexions_mt
                clients_bt_nets = total_nouveaux_clients_bt - total_deconnexions_bt
                
                total_clients = clients_ht_nets + clients_mt_nets + clients_bt_nets
                
                # Moyenne des autres indicateurs sur l'année
                nouvelles_localites = sum(c.nouvelles_localites_desservies or 0 for c in collectes)
                nouveaux_reseaux_km = sum(c.longueur_nouveaux_reseaux_km or 0 for c in collectes)
                nouvelle_population = sum(c.population_nouvelle_couverte or 0 for c in collectes)
                
                # Créer l'enregistrement de clientèle
                clientele = ClienteleElectricite(
                    annee=annee,
                    operateur_id=operateur.id,
                    clients_ht=max(0, clients_ht_nets),
                    clients_mt=max(0, clients_mt_nets),
                    clients_bt=max(0, clients_bt_nets),
                    total_clients=max(0, total_clients),
                    clients_factures=int(total_clients * 0.85) if total_clients > 0 else 0,  # Estimation 85%
                    menages_factures=int(total_clients * 0.75) if total_clients > 0 else 0,  # Estimation 75%
                    menages_desservis=int(total_clients * 0.90) if total_clients > 0 else 0,  # Estimation 90%
                    # Taux calculés selon la couverture géographique
                    taux_couverture_geographique=min(100, nouvelles_localites * 2),  # Estimation
                    taux_electrification=min(100, (nouvelle_population / 1000) if nouvelle_population else 0),
                    taux_acces_electricite=min(100, (total_clients / 1000) if total_clients else 0)
                )
                clientele.save()
                
                print(f"  ✅ {operateur.nom}: {total_clients} clients, {nouvelles_localites} nouvelles localités")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erreur calcul clientèle: {e}")
            return False

    @staticmethod
    def calculer_statistiques_nationales_reelles(annee):
        """
        Calcule les statistiques nationales basées sur les données réelles collectées
        """
        print(f"🇨🇩 Calcul des statistiques nationales réelles pour {annee}...")
        
        try:
            # Supprimer les données fictives existantes
            StatistiqueNationale.query.filter_by(annee=annee).delete()
            
            # Agrégation des capacités installées réelles
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
                
                if capacite.type_source == 'production_hydro':
                    stats['capacite_hydro_mw'] = capacite.total_installee or 0
                    stats['production_hydro_gwh'] = capacite.total_production or 0
                elif capacite.type_source == 'production_thermique':
                    stats['capacite_thermique_mw'] = capacite.total_installee or 0
                    stats['production_thermique_gwh'] = capacite.total_production or 0
                elif capacite.type_source == 'production_solaire':
                    stats['capacite_solaire_mw'] = capacite.total_installee or 0
                    stats['production_solaire_gwh'] = capacite.total_production or 0
            
            # Agrégation de la clientèle réelle
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
            
            # Nombre d'opérateurs actifs réels
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
            
            print(f"  ✅ Stats nationales: {stats['capacite_totale_installee_mw']} MW, {stats['total_clients_nationaux']} clients")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erreur calcul stats nationales: {e}")
            return False

    @staticmethod
    def _calculer_facteur_charge_reel(capacite_mw, production_gwh):
        """Calcule le facteur de charge réel basé sur les données de production"""
        if not capacite_mw or capacite_mw == 0:
            return 0
        
        # Production théorique maximale = capacité * 8760 heures * 1000 (MW->kW) / 1000000 (kW->GW)
        production_theorique_max_gwh = capacite_mw * 8.760  # MW * 8760h / 1000
        
        if production_theorique_max_gwh == 0:
            return 0
        
        facteur_charge = min(100, (production_gwh / production_theorique_max_gwh) * 100)
        return round(facteur_charge, 2)

    @staticmethod
    def calculer_toutes_statistiques_reelles(annee):
        """
        Lance tous les calculs de statistiques basées sur les données réelles
        au lieu des données fictives
        """
        print(f"🔄 Calcul de toutes les statistiques RÉELLES pour {annee}...")
        print("📋 Basé sur les données des opérateurs (centrales, rapports, collectes)")
        
        try:
            # 1. Calculer les capacités basées sur les centrales déclarées
            if not CalculStatistiquesReellesService.calculer_capacites_installees_reelles(annee):
                print("❌ Échec calcul capacités")
                return False
            
            # 2. Calculer la clientèle basée sur les collectes mensuelles
            if not CalculStatistiquesReellesService.calculer_clientele_reelle_depuis_collecte(annee):
                print("❌ Échec calcul clientèle")
                return False
            
            # 3. Calculer les statistiques nationales agrégées
            if not CalculStatistiquesReellesService.calculer_statistiques_nationales_reelles(annee):
                print("❌ Échec calcul stats nationales")
                return False
            
            print(f"✅ Toutes les statistiques RÉELLES calculées pour {annee}")
            print("📊 Les données fictives ont été remplacées par des calculs basés sur:")
            print("   - Centrales déclarées par les opérateurs")
            print("   - Rapports de production soumis")
            print("   - Collectes mensuelles validées")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur générale: {e}")
            return False