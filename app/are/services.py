"""
Services pour les calculs des indicateurs ARE
"""
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
from app.extensions import db
from app.models.dashboard_are import (
    KPIStrategic, IndicateurSectoriel, AlerteRegulateur, 
    DonneesProvince, CategorieIndicateur, TendanceKPI, TypeAlerte, SeveriteAlerte
)
from app.models.operateurs import Operateur
from app.models.production_hydro import CentraleHydro, RapportHydro
from app.models.production_thermique import CentraleThermique, RapportThermique
from app.models.production_solaire import CentraleSolaire, RapportSolaire
from app.models.transport import LigneTransport, RapportTransport
from app.models.distribution import ReseauDistribution, RapportDistribution


class IndicateursAREService:
    """Service pour calculer les indicateurs stratégiques ARE"""
    
    @staticmethod
    def calculer_taux_acces_province(province, annee):
        """Calcule le taux d'accès à l'électricité par province"""
        # Récupérer les données de distribution pour la province
        reseaux = ReseauDistribution.query.filter_by(province=province, actif=True).all()
        
        if not reseaux:
            return 0.0
        
        # Calculer la population desservie (approximation basée sur les données de distribution)
        population_desservie = 0
        for reseau in reseaux:
            # Utiliser les derniers rapports de distribution
            dernier_rapport = RapportDistribution.query.filter(
                RapportDistribution.reseau_id == reseau.id,
                RapportDistribution.annee == annee
            ).order_by(RapportDistribution.date_creation.desc()).first()
            
            if dernier_rapport and dernier_rapport.nombre_clients_fin:
                # Approximation: 1 client = 4 personnes en moyenne
                population_desservie += dernier_rapport.nombre_clients_fin * 4
        
        # Récupérer la population totale de la province depuis DonneesProvince
        donnees_province = DonneesProvince.query.filter_by(
            province=province, 
            annee=annee
        ).first()
        
        if donnees_province and donnees_province.population:
            taux_acces = (population_desservie / donnees_province.population) * 100
            return min(taux_acces, 100.0)  # Limiter à 100%
        
        return 0.0
    
    @staticmethod
    def calculer_mix_energetique(annee, operateur_id=None):
        """Calcule le mix énergétique pour une année donnée"""
        mix = {
            'hydro': 0.0,
            'thermique': 0.0,
            'solaire': 0.0,
            'total': 0.0
        }
        
        # Filtre par opérateur si spécifié
        operateur_filter = {'operateur_id': operateur_id} if operateur_id else {}
        
        # Production hydroélectrique
        hydro_query = RapportHydro.query.join(CentraleHydro).filter(
            RapportHydro.annee == annee,
            RapportHydro.actif == True
        )
        if operateur_id:
            hydro_query = hydro_query.filter(CentraleHydro.operateur_id == operateur_id)
        
        production_hydro = hydro_query.with_entities(
            func.sum(RapportHydro.energie_produite)
        ).scalar() or 0.0
        
        # Production thermique
        thermique_query = RapportThermique.query.join(CentraleThermique).filter(
            RapportThermique.annee == annee,
            RapportThermique.actif == True
        )
        if operateur_id:
            thermique_query = thermique_query.filter(CentraleThermique.operateur_id == operateur_id)
        
        production_thermique = thermique_query.with_entities(
            func.sum(RapportThermique.energie_produite)
        ).scalar() or 0.0
        
        # Production solaire
        solaire_query = RapportSolaire.query.join(CentraleSolaire).filter(
            RapportSolaire.annee == annee,
            RapportSolaire.actif == True
        )
        if operateur_id:
            solaire_query = solaire_query.filter(CentraleSolaire.operateur_id == operateur_id)
        
        production_solaire = solaire_query.with_entities(
            func.sum(RapportSolaire.energie_produite)
        ).scalar() or 0.0
        
        # Calculer le mix
        production_totale = production_hydro + production_thermique + production_solaire
        
        if production_totale > 0:
            mix['hydro'] = (production_hydro / production_totale) * 100
            mix['thermique'] = (production_thermique / production_totale) * 100
            mix['solaire'] = (production_solaire / production_totale) * 100
            mix['total'] = production_totale
        
        return mix
    
    @staticmethod
    def calculer_performance_operateurs(annee):
        """Calcule les indicateurs de performance des opérateurs"""
        operateurs = Operateur.query.filter_by(actif=True).all()
        performances = []
        
        for operateur in operateurs:
            # Puissance installée totale
            puissance_hydro = CentraleHydro.query.filter_by(
                operateur_id=operateur.id, 
                actif=True
            ).with_entities(func.sum(CentraleHydro.puissance_installee)).scalar() or 0.0
            
            puissance_thermique = CentraleThermique.query.filter_by(
                operateur_id=operateur.id, 
                actif=True
            ).with_entities(func.sum(CentraleThermique.puissance_installee)).scalar() or 0.0
            
            puissance_solaire = CentraleSolaire.query.filter_by(
                operateur_id=operateur.id, 
                actif=True
            ).with_entities(func.sum(CentraleSolaire.puissance_installee)).scalar() or 0.0
            
            puissance_totale = puissance_hydro + puissance_thermique + puissance_solaire
            
            # Production totale
            mix = IndicateursAREService.calculer_mix_energetique(annee, operateur.id)
            production_totale = mix['total']
            
            # Facteur de charge moyen
            facteur_charge = 0.0
            if puissance_totale > 0:
                heures_annee = 8760
                production_theorique_max = puissance_totale * heures_annee
                if production_theorique_max > 0:
                    facteur_charge = (production_totale / production_theorique_max) * 100
            
            # Nombre de clients (distribution)
            clients_total = 0
            reseaux = ReseauDistribution.query.filter_by(
                operateur_id=operateur.id, 
                actif=True
            ).all()
            
            for reseau in reseaux:
                dernier_rapport = RapportDistribution.query.filter(
                    RapportDistribution.reseau_id == reseau.id,
                    RapportDistribution.annee == annee
                ).order_by(RapportDistribution.date_creation.desc()).first()
                
                if dernier_rapport and dernier_rapport.nombre_clients_fin:
                    clients_total += dernier_rapport.nombre_clients_fin
            
            performances.append({
                'operateur': operateur.nom,
                'operateur_id': operateur.id,
                'puissance_installee': puissance_totale,
                'production_annuelle': production_totale,
                'facteur_charge': facteur_charge,
                'clients_total': clients_total,
                'mix_energetique': mix
            })
        
        return performances
    
    @staticmethod
    def generer_alertes_automatiques():
        """Génère des alertes automatiques basées sur les seuils"""
        alertes_generees = []
        
        # Vérifier les KPIs avec seuils d'alerte
        kpis_critiques = KPIStrategic.query.filter(
            KPIStrategic.seuil_alerte.isnot(None),
            KPIStrategic.actif == True
        ).all()
        
        for kpi in kpis_critiques:
            if kpi.valeur < kpi.seuil_alerte:
                # Vérifier si une alerte existe déjà
                alerte_existante = AlerteRegulateur.query.filter(
                    AlerteRegulateur.type == TypeAlerte.TECHNIQUE,
                    AlerteRegulateur.entite_concernee.like(f'%{kpi.code}%'),
                    AlerteRegulateur.statut == 'active'
                ).first()
                
                if not alerte_existante:
                    alerte = AlerteRegulateur(
                        type=TypeAlerte.TECHNIQUE,
                        severite=SeveriteAlerte.ELEVEE,
                        entite_concernee=f"KPI {kpi.code}",
                        titre=f"Alerte KPI: {kpi.nom}",
                        description=f"Le KPI {kpi.nom} a une valeur de {kpi.valeur} {kpi.unite}, "
                                  f"inférieure au seuil d'alerte de {kpi.seuil_alerte} {kpi.unite}.",
                        operateur_id=kpi.operateur_id,
                        createur_id=1,  # Système automatique
                        priorite=2
                    )
                    alerte.save()
                    alertes_generees.append(alerte)
        
        # Alertes pour retards de rapports
        operateurs = Operateur.query.filter_by(actif=True).all()
        date_limite = datetime.now() - timedelta(days=30)
        
        for operateur in operateurs:
            # Vérifier les retards de rapports
            derniers_rapports = {
                'hydro': RapportHydro.query.join(CentraleHydro).filter(
                    CentraleHydro.operateur_id == operateur.id
                ).order_by(RapportHydro.date_creation.desc()).first(),
                'thermique': RapportThermique.query.join(CentraleThermique).filter(
                    CentraleThermique.operateur_id == operateur.id
                ).order_by(RapportThermique.date_creation.desc()).first(),
                'transport': RapportTransport.query.join(LigneTransport).filter(
                    LigneTransport.operateur_id == operateur.id
                ).order_by(RapportTransport.date_creation.desc()).first()
            }
            
            for type_rapport, dernier_rapport in derniers_rapports.items():
                if dernier_rapport and dernier_rapport.date_creation < date_limite:
                    alerte_existante = AlerteRegulateur.query.filter(
                        AlerteRegulateur.type == TypeAlerte.ADMINISTRATIF,
                        AlerteRegulateur.entite_concernee == operateur.nom_commercial,
                        AlerteRegulateur.description.like(f'%{type_rapport}%'),
                        AlerteRegulateur.statut == 'active'
                    ).first()
                    
                    if not alerte_existante:
                        alerte = AlerteRegulateur(
                            type=TypeAlerte.ADMINISTRATIF,
                            severite=SeveriteAlerte.MOYENNE,
                            entite_concernee=operateur.nom_commercial,
                            titre=f"Retard rapport {type_rapport}",
                            description=f"Aucun rapport {type_rapport} reçu depuis plus de 30 jours "
                                      f"pour l'opérateur {operateur.nom_commercial}.",
                            operateur_id=operateur.id,
                            createur_id=1,
                            priorite=2
                        )
                        alerte.save()
                        alertes_generees.append(alerte)
        
        return alertes_generees
    
    @staticmethod
    def mettre_a_jour_kpis_strategiques(annee):
        """Met à jour tous les KPIs stratégiques pour une année"""
        kpis_mis_a_jour = []
        
        # KPI 1: Taux d'accès national à l'électricité
        provinces_rdc = [
            'Kinshasa', 'Bas-Congo', 'Bandundu', 'Équateur', 'Orientale', 
            'Nord-Kivu', 'Sud-Kivu', 'Maniema', 'Katanga', 'Kasaï-Oriental', 'Kasaï-Occidental'
        ]
        
        taux_acces_total = 0
        provinces_avec_donnees = 0
        
        for province in provinces_rdc:
            taux = IndicateursAREService.calculer_taux_acces_province(province, annee)
            if taux > 0:
                taux_acces_total += taux
                provinces_avec_donnees += 1
        
        if provinces_avec_donnees > 0:
            taux_acces_national = taux_acces_total / provinces_avec_donnees
            
            kpi_acces = KPIStrategic.query.filter_by(
                code='TAUX_ACCES_NATIONAL',
                annee=annee
            ).first()
            
            if not kpi_acces:
                kpi_acces = KPIStrategic(
                    code='TAUX_ACCES_NATIONAL',
                    nom='Taux d\'accès national à l\'électricité',
                    valeur=taux_acces_national,
                    unite='%',
                    periode=str(annee),
                    annee=annee,
                    objectif=85.0,
                    seuil_alerte=70.0,
                    source_donnees='Rapports distribution'
                )
            else:
                kpi_acces.valeur = taux_acces_national
                kpi_acces.date_modification = datetime.utcnow()
            
            kpi_acces.save()
            kpis_mis_a_jour.append(kpi_acces)
        
        # KPI 2: Production totale nationale
        mix_national = IndicateursAREService.calculer_mix_energetique(annee)
        
        kpi_production = KPIStrategic.query.filter_by(
            code='PRODUCTION_NATIONALE',
            annee=annee
        ).first()
        
        if not kpi_production:
            kpi_production = KPIStrategic(
                code='PRODUCTION_NATIONALE',
                nom='Production électrique nationale',
                valeur=mix_national['total'],
                unite='MWh',
                periode=str(annee),
                annee=annee,
                objectif=15000000,  # 15 GWh objectif
                seuil_alerte=8000000,  # 8 GWh seuil alerte
                source_donnees='Rapports production'
            )
        else:
            kpi_production.valeur = mix_national['total']
            kpi_production.date_modification = datetime.utcnow()
        
        kpi_production.save()
        kpis_mis_a_jour.append(kpi_production)
        
        # KPI 3: Nombre d'opérateurs actifs
        nb_operateurs = Operateur.query.filter_by(actif=True).count()
        
        kpi_operateurs = KPIStrategic.query.filter_by(
            code='OPERATEURS_ACTIFS',
            annee=annee
        ).first()
        
        if not kpi_operateurs:
            kpi_operateurs = KPIStrategic(
                code='OPERATEURS_ACTIFS',
                nom='Nombre d\'opérateurs actifs',
                valeur=nb_operateurs,
                unite='opérateurs',
                periode=str(annee),
                annee=annee,
                source_donnees='Base opérateurs'
            )
        else:
            kpi_operateurs.valeur = nb_operateurs
            kpi_operateurs.date_modification = datetime.utcnow()
        
        kpi_operateurs.save()
        kpis_mis_a_jour.append(kpi_operateurs)
        
        # Calcul automatique du statut "atteint" pour tous les KPIs avec objectif
        for kpi in kpis_mis_a_jour:
            if kpi.objectif is not None:
                kpi.atteint = kpi.valeur >= kpi.objectif
                kpi.save()
        
        return kpis_mis_a_jour