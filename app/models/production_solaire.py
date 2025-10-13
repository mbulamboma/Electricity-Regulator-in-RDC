"""
Modèles pour la production solaire
"""
from app.extensions import db
from app.models.base import BaseModel
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime


class CentraleSolaire(BaseModel):
    """Modèle pour les centrales solaires"""
    __tablename__ = 'centrales_solaire'
    
    # Relations
    operateur_id = Column(Integer, ForeignKey('operateurs.id'), nullable=False)
    
    # Informations de base
    nom = Column(String(200), nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False)
    localisation = Column(String(200))
    province = Column(String(100))
    
    # Caractéristiques techniques
    puissance_installee = Column(Float)  # MWc (Mégawatt-crête)
    puissance_disponible = Column(Float)  # MW
    type_centrale = Column(String(50))  # fixe, tracker, flottante, agrovoltaïque
    technologie_modules = Column(String(50))  # silicium cristallin, couches minces, etc.
    
    # Coordonnées GPS et orientation
    latitude = Column(Float)
    longitude = Column(Float)
    altitude = Column(Float)  # mètres
    orientation_azimut = Column(Float)  # degrés (0=Nord, 180=Sud)
    inclinaison_modules = Column(Float)  # degrés
    
    # Modules photovoltaïques
    nombre_modules = Column(Integer)
    puissance_unitaire_module = Column(Float)  # Wc
    marque_modules = Column(String(100))
    modele_modules = Column(String(100))
    technologie_cellules = Column(String(50))  # monocristallin, polycristallin
    
    # Systèmes de conversion
    nombre_onduleurs = Column(Integer)
    puissance_unitaire_onduleur = Column(Float)  # kW
    marque_onduleurs = Column(String(100))
    type_onduleur = Column(String(50))  # string, central, micro
    rendement_onduleur = Column(Float)  # %
    
    # Systèmes de stockage (si applicable)
    stockage_batterie = Column(Boolean, default=False)
    capacite_stockage = Column(Float)  # kWh
    type_batterie = Column(String(50))  # lithium-ion, plomb-acide, etc.
    nombre_batteries = Column(Integer)
    marque_batteries = Column(String(100))
    
    # Système de suivi (tracking)
    systeme_suivi = Column(Boolean, default=False)
    type_suivi = Column(String(50))  # monoaxial, biaxial
    precision_suivi = Column(Float)  # degrés
    
    # Infrastructure électrique
    niveau_tension = Column(Float)  # kV
    tension_evacuation = Column(String(50))  # kV
    nombre_transformateurs = Column(Integer)
    puissance_transformateurs = Column(Float)  # MVA
    
    # Données météorologiques et performance
    irradiation_annuelle_estimee = Column(Float)  # kWh/m²/an
    temperature_fonctionnement_nominale = Column(Float)  # °C
    coefficient_temperature = Column(Float)  # %/°C
    facteur_degradation_annuelle = Column(Float)  # %/an
    
    # Système de monitoring
    systeme_monitoring = Column(Boolean, default=False)
    fournisseur_monitoring = Column(String(100))
    precision_mesure = Column(Float)  # %
    
    # Statut et état
    statut = Column(String(50), default='operationnelle')  # operationnelle, maintenance, arret
    mode_fonctionnement = Column(String(50))  # grid-tied, off-grid, hybride
    superficie_totale = Column(Float)  # hectares
    description = Column(Text)
    
    # Dates importantes
    date_mise_service = Column(DateTime)
    date_derniere_revision = Column(DateTime)
    prochaine_maintenance = Column(DateTime)
    
    # Informations complémentaires
    constructeur = Column(String(100))
    installateur = Column(String(100))
    annee_construction = Column(Integer)
    duree_vie_estimee = Column(Integer)  # années
    garantie_modules = Column(Integer)  # années
    garantie_onduleurs = Column(Integer)  # années
    observations = Column(Text)
    
    # Relations
    operateur = relationship("Operateur", back_populates="centrales_solaire")
    rapports = relationship("RapportSolaire", back_populates="centrale", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<CentraleSolaire {self.nom}>'
    
    def to_dict(self):
        """Convertir en dictionnaire"""
        data = super().to_dict()
        data.update({
            'operateur_id': self.operateur_id,
            'nom': self.nom,
            'code': self.code,
            'localisation': self.localisation,
            'province': self.province,
            'puissance_installee': self.puissance_installee,
            'puissance_disponible': self.puissance_disponible,
            'type_centrale': self.type_centrale,
            'technologie_modules': self.technologie_modules,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'altitude': self.altitude,
            'orientation_azimut': self.orientation_azimut,
            'inclinaison_modules': self.inclinaison_modules,
            'nombre_modules': self.nombre_modules,
            'puissance_unitaire_module': self.puissance_unitaire_module,
            'nombre_onduleurs': self.nombre_onduleurs,
            'stockage_batterie': self.stockage_batterie,
            'capacite_stockage': self.capacite_stockage,
            'systeme_suivi': self.systeme_suivi,
            'niveau_tension': self.niveau_tension,
            'irradiation_annuelle_estimee': self.irradiation_annuelle_estimee,
            'statut': self.statut,
            'mode_fonctionnement': self.mode_fonctionnement,
            'superficie_totale': self.superficie_totale,
            'date_mise_service': self.date_mise_service.isoformat() if self.date_mise_service else None,
            'date_derniere_revision': self.date_derniere_revision.isoformat() if self.date_derniere_revision else None,
            'constructeur': self.constructeur,
            'installateur': self.installateur,
            'annee_construction': self.annee_construction,
            'observations': self.observations,
            'operateur_nom': self.operateur.nom if self.operateur else None,
            'nombre_rapports': len(self.rapports) if self.rapports else 0
        })
        return data


class RapportSolaire(BaseModel):
    """Modèle pour les rapports de production solaire"""
    __tablename__ = 'rapports_solaire'
    
    # Relations
    centrale_id = Column(Integer, ForeignKey('centrales_solaire.id'), nullable=False)
    
    # Période de rapport
    annee = Column(Integer, nullable=False)
    mois = Column(Integer, nullable=False)
    periode_debut = Column(DateTime, nullable=False)
    periode_fin = Column(DateTime, nullable=False)
    
    # Production
    energie_produite = Column(Float)  # MWh
    energie_disponible = Column(Float)  # MWh théorique
    facteur_charge = Column(Float)  # %
    productible_theorique = Column(Float)  # MWh basé sur l'irradiation
    performance_ratio = Column(Float)  # % (rapport production réelle/théorique)
    
    # Données météorologiques
    irradiation_totale = Column(Float)  # kWh/m²
    irradiation_moyenne_quotidienne = Column(Float)  # kWh/m²/jour
    temperature_ambiante_moyenne = Column(Float)  # °C
    temperature_modules_moyenne = Column(Float)  # °C
    humidite_relative_moyenne = Column(Float)  # %
    vitesse_vent_moyenne = Column(Float)  # m/s
    heures_ensoleillement = Column(Float)  # heures
    
    # Performance du système
    rendement_global = Column(Float)  # %
    rendement_modules = Column(Float)  # %
    rendement_onduleurs = Column(Float)  # %
    pertes_ombrages = Column(Float)  # %
    pertes_cables = Column(Float)  # %
    pertes_poussiere = Column(Float)  # %
    pertes_thermiques = Column(Float)  # %
    
    # Fonctionnement onduleurs
    temps_fonctionnement_onduleurs = Column(Float)  # heures
    nombre_demarrages_onduleurs = Column(Integer)
    nombre_arrets_onduleurs = Column(Integer)
    alarmes_onduleurs = Column(Integer)
    
    # Système de stockage (si applicable)
    energie_stockee = Column(Float)  # MWh
    energie_destockee = Column(Float)  # MWh
    rendement_stockage = Column(Float)  # %
    cycles_charge_decharge = Column(Integer)
    etat_sante_batteries = Column(Float)  # % (State of Health)
    
    # Système de suivi (tracking)
    precision_suivi_moyenne = Column(Float)  # degrés
    defauts_suivi = Column(Integer)
    maintenance_systeme_suivi = Column(Integer)
    
    # Maintenance et incidents
    maintenances_preventives = Column(Integer, default=0)
    maintenances_correctives = Column(Integer, default=0)
    nettoyage_modules = Column(Integer, default=0)
    incidents_majeurs = Column(Integer, default=0)
    description_incidents = Column(Text)
    modules_defectueux = Column(Integer, default=0)
    onduleurs_defectueux = Column(Integer, default=0)
    
    # Données de surveillance
    defauts_systeme_monitoring = Column(Integer, default=0)
    disponibilite_donnees = Column(Float)  # %
    precision_mesures = Column(Float)  # %
    
    # Données environnementales
    reduction_emissions_co2 = Column(Float)  # tonnes CO2 évitées
    impact_environnemental = Column(Text)
    gestion_fin_vie_composants = Column(Text)
    
    # Données économiques
    cout_maintenance = Column(Float)  # USD
    cout_nettoyage = Column(Float)  # USD
    recettes_vente = Column(Float)  # USD
    economie_carburant = Column(Float)  # USD (pour systèmes hybrides)
    rentabilite = Column(Float)  # %
    
    # Indicateurs de performance
    degradation_observee = Column(Float)  # %
    disponibilite_systeme = Column(Float)  # %
    taux_defaillance = Column(Float)  # %
    
    # Validation et statut
    statut = Column(String(50), default='brouillon')  # brouillon, validé, transmis
    date_validation = Column(DateTime)
    date_transmission = Column(DateTime)
    validé_par = Column(String(100))
    observations = Column(Text)
    
    # Relations
    centrale = relationship("CentraleSolaire", back_populates="rapports")
    donnees_quotidiennes = relationship("DonneesSolaireQuotidiennes", back_populates="rapport", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<RapportSolaire {self.centrale.nom if self.centrale else "N/A"} - {self.mois}/{self.annee}>'
    
    def get_periode_str(self):
        """Obtenir la période sous forme de chaîne"""
        mois_noms = [
            '', 'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
            'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
        ]
        return f"{mois_noms[self.mois]} {self.annee}"
    
    def to_dict(self):
        """Convertir en dictionnaire"""
        data = super().to_dict()
        data.update({
            'centrale_id': self.centrale_id,
            'annee': self.annee,
            'mois': self.mois,
            'periode_debut': self.periode_debut.isoformat() if self.periode_debut else None,
            'periode_fin': self.periode_fin.isoformat() if self.periode_fin else None,
            'energie_produite': self.energie_produite,
            'energie_disponible': self.energie_disponible,
            'facteur_charge': self.facteur_charge,
            'productible_theorique': self.productible_theorique,
            'performance_ratio': self.performance_ratio,
            'irradiation_totale': self.irradiation_totale,
            'temperature_ambiante_moyenne': self.temperature_ambiante_moyenne,
            'rendement_global': self.rendement_global,
            'temps_fonctionnement_onduleurs': self.temps_fonctionnement_onduleurs,
            'energie_stockee': self.energie_stockee,
            'maintenances_preventives': self.maintenances_preventives,
            'maintenances_correctives': self.maintenances_correctives,
            'incidents_majeurs': self.incidents_majeurs,
            'reduction_emissions_co2': self.reduction_emissions_co2,
            'cout_maintenance': self.cout_maintenance,
            'statut': self.statut,
            'observations': self.observations,
            'centrale_nom': self.centrale.nom if self.centrale else None,
            'centrale_code': self.centrale.code if self.centrale else None,
            'periode_str': self.get_periode_str()
        })
        return data


class DonneesSolaireQuotidiennes(BaseModel):
    """Modèle pour les données quotidiennes de production solaire"""
    __tablename__ = 'donnees_solaire_quotidiennes'
    
    # Relations
    rapport_id = Column(Integer, ForeignKey('rapports_solaire.id'), nullable=False)
    
    # Date
    date_production = Column(DateTime, nullable=False)
    
    # Production
    energie_produite = Column(Float)  # kWh
    puissance_max = Column(Float)  # kW
    heure_puissance_max = Column(String(10))  # HH:MM
    
    # Météorologie
    irradiation = Column(Float)  # kWh/m²
    temperature_ambiante_max = Column(Float)  # °C
    temperature_ambiante_min = Column(Float)  # °C
    temperature_modules_max = Column(Float)  # °C
    humidite_relative = Column(Float)  # %
    vitesse_vent_max = Column(Float)  # m/s
    
    # Performance
    performance_ratio = Column(Float)  # %
    rendement_quotidien = Column(Float)  # %
    
    # Incidents
    duree_arrets = Column(Float, default=0.0)  # heures
    cause_arrets = Column(String(200))
    
    # Relations
    rapport = relationship("RapportSolaire", back_populates="donnees_quotidiennes")
    
    def __repr__(self):
        return f'<DonneesSolaireQuotidiennes {self.date_production.strftime("%d/%m/%Y") if self.date_production else "N/A"}>'