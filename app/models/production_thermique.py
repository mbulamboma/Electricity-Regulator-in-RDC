"""
Modèles pour la production thermique
"""
from app.extensions import db
from app.models.base import BaseModel
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime


class CentraleThermique(BaseModel):
    """Modèle pour les centrales thermiques"""
    __tablename__ = 'centrales_thermique'
    
    # Relations
    operateur_id = Column(Integer, ForeignKey('operateurs.id'), nullable=False)
    
    # Informations de base
    nom = Column(String(200), nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False)
    localisation = Column(String(200))
    province = Column(String(100))
    
    # Caractéristiques techniques
    puissance_installee = Column(Float)  # MW
    puissance_disponible = Column(Float)  # MW
    type_centrale = Column(String(50))  # diesel, gaz, charbon, fuel lourd, biomasse
    type_combustible = Column(String(50))  # Principal type de combustible
    consommation_specifique = Column(Float)  # g/kWh - Consommation spécifique
    
    # Coordonnées GPS
    latitude = Column(Float)
    longitude = Column(Float)
    
    # Équipements spécifiques thermique
    nombre_groupes = Column(Integer, default=0)
    type_moteur = Column(String(50))  # diesel, turbine gaz, turbine vapeur
    refroidissement = Column(String(50))  # air, eau, mixte
    niveau_tension = Column(Float)  # kV
    tension_evacuation = Column(String(50))  # kV
    
    # Systèmes auxiliaires
    systeme_demarrage = Column(String(50))  # manuel, automatique
    systeme_refroidissement = Column(String(100))
    capacite_stockage_combustible = Column(Float)  # litres ou tonnes
    autonomie_combustible = Column(Float)  # heures
    
    # Caractéristiques environnementales
    systeme_traitement_fumees = Column(Boolean, default=False)
    niveau_emission_nox = Column(Float)  # mg/Nm³
    niveau_emission_co = Column(Float)  # mg/Nm³
    certification_environnementale = Column(String(100))
    
    # Statut et état
    statut = Column(String(50), default='operationnelle')  # operationnelle, maintenance, arret
    mode_fonctionnement = Column(String(50))  # base, pointe, secours
    description = Column(Text)
    
    # Dates importantes
    date_mise_service = Column(DateTime)
    date_derniere_revision = Column(DateTime)
    prochaine_maintenance = Column(DateTime)
    
    # Informations complémentaires
    constructeur = Column(String(100))
    fournisseur_combustible = Column(String(100))
    annee_construction = Column(Integer)
    duree_vie_estimee = Column(Integer)  # années
    observations = Column(Text)
    
    # Relations
    operateur = relationship("Operateur", back_populates="centrales_thermique")
    rapports = relationship("RapportThermique", back_populates="centrale", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<CentraleThermique {self.nom}>'
    
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
            'type_combustible': self.type_combustible,
            'consommation_specifique': self.consommation_specifique,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'nombre_groupes': self.nombre_groupes,
            'type_moteur': self.type_moteur,
            'refroidissement': self.refroidissement,
            'niveau_tension': self.niveau_tension,
            'tension_evacuation': self.tension_evacuation,
            'capacite_stockage_combustible': self.capacite_stockage_combustible,
            'autonomie_combustible': self.autonomie_combustible,
            'statut': self.statut,
            'mode_fonctionnement': self.mode_fonctionnement,
            'date_mise_service': self.date_mise_service.isoformat() if self.date_mise_service else None,
            'date_derniere_revision': self.date_derniere_revision.isoformat() if self.date_derniere_revision else None,
            'constructeur': self.constructeur,
            'fournisseur_combustible': self.fournisseur_combustible,
            'annee_construction': self.annee_construction,
            'observations': self.observations,
            'operateur_nom': self.operateur.nom if self.operateur else None,
            'nombre_rapports': len(self.rapports) if self.rapports else 0
        })
        return data


class RapportThermique(BaseModel):
    """Modèle pour les rapports de production thermique"""
    __tablename__ = 'rapports_thermique'
    
    # Relations
    centrale_id = Column(Integer, ForeignKey('centrales_thermique.id'), nullable=False)
    
    # Période de rapport
    annee = Column(Integer, nullable=False)
    mois = Column(Integer, nullable=False)
    periode_debut = Column(DateTime, nullable=False)
    periode_fin = Column(DateTime, nullable=False)
    
    # Production
    energie_produite = Column(Float)  # MWh
    energie_disponible = Column(Float)  # MWh
    facteur_charge = Column(Float)  # %
    temps_fonctionnement = Column(Float)  # heures
    nombre_demarrages = Column(Integer, default=0)
    nombre_arrets = Column(Integer, default=0)
    duree_arrets = Column(Float, default=0.0)  # heures
    
    # Consommation combustible
    consommation_combustible = Column(Float)  # litres ou tonnes
    type_combustible_utilise = Column(String(50))
    cout_combustible = Column(Float)  # USD
    prix_unitaire_combustible = Column(Float)  # USD/litre ou USD/tonne
    consommation_specifique_reelle = Column(Float)  # g/kWh
    
    # Performance thermique
    rendement_global = Column(Float)  # %
    rendement_thermique = Column(Float)  # %
    rendement_electrique = Column(Float)  # %
    temperature_fumees = Column(Float)  # °C
    pression_admission = Column(Float)  # bar
    
    # Données d'exploitation
    charge_moyenne = Column(Float)  # %
    charge_maximale = Column(Float)  # %
    charge_minimale = Column(Float)  # %
    temperature_ambiante_moyenne = Column(Float)  # °C
    humidite_relative_moyenne = Column(Float)  # %
    
    # Maintenance et incidents
    maintenances_preventives = Column(Integer, default=0)
    maintenances_correctives = Column(Integer, default=0)
    incidents_majeurs = Column(Integer, default=0)
    description_incidents = Column(Text)
    duree_maintenance = Column(Float, default=0.0)  # heures
    
    # Consommables et lubrifiants
    consommation_huile_moteur = Column(Float)  # litres
    consommation_liquide_refroidissement = Column(Float)  # litres
    remplacement_filtres = Column(Integer, default=0)
    autres_consommables = Column(Text)
    
    # Données environnementales
    emissions_co2 = Column(Float)  # tonnes
    emissions_nox = Column(Float)  # kg
    emissions_co = Column(Float)  # kg
    gestion_dechets = Column(Text)
    impact_environnemental = Column(Text)
    
    # Données économiques
    cout_exploitation = Column(Float)  # USD
    cout_maintenance = Column(Float)  # USD
    recettes_vente = Column(Float)  # USD
    rentabilite = Column(Float)  # %
    
    # Validation et statut
    statut = Column(String(50), default='brouillon')  # brouillon, validé, transmis
    date_validation = Column(DateTime)
    date_transmission = Column(DateTime)
    validé_par = Column(String(100))
    observations = Column(Text)
    
    # Relations
    centrale = relationship("CentraleThermique", back_populates="rapports")
    groupes_production = relationship("GroupeProductionThermique", back_populates="rapport", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<RapportThermique {self.centrale.nom if self.centrale else "N/A"} - {self.mois}/{self.annee}>'
    
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
            'temps_fonctionnement': self.temps_fonctionnement,
            'consommation_combustible': self.consommation_combustible,
            'type_combustible_utilise': self.type_combustible_utilise,
            'cout_combustible': self.cout_combustible,
            'rendement_global': self.rendement_global,
            'charge_moyenne': self.charge_moyenne,
            'maintenances_preventives': self.maintenances_preventives,
            'maintenances_correctives': self.maintenances_correctives,
            'incidents_majeurs': self.incidents_majeurs,
            'emissions_co2': self.emissions_co2,
            'cout_exploitation': self.cout_exploitation,
            'statut': self.statut,
            'observations': self.observations,
            'centrale_nom': self.centrale.nom if self.centrale else None,
            'centrale_code': self.centrale.code if self.centrale else None,
            'periode_str': self.get_periode_str()
        })
        return data


class GroupeProductionThermique(BaseModel):
    """Modèle pour les données détaillées par groupe de production thermique"""
    __tablename__ = 'groupes_production_thermique'
    
    # Relations
    rapport_id = Column(Integer, ForeignKey('rapports_thermique.id'), nullable=False)
    
    # Identification du groupe
    numero_groupe = Column(Integer, nullable=False)
    nom_groupe = Column(String(100))
    type_groupe = Column(String(50))  # diesel, gaz, etc.
    
    # Production
    energie_produite = Column(Float)  # MWh
    temps_fonctionnement = Column(Float)  # heures
    nombre_demarrages = Column(Integer, default=0)
    facteur_charge = Column(Float)  # %
    
    # Consommation
    consommation_combustible = Column(Float)  # litres ou tonnes
    consommation_specifique = Column(Float)  # g/kWh
    
    # Performance
    rendement = Column(Float)  # %
    puissance_moyenne = Column(Float)  # MW
    temperature_echappement = Column(Float)  # °C
    
    # État et maintenance
    etat_general = Column(String(50))  # bon, moyen, defaillant
    heures_fonctionnement_totales = Column(Float)
    prochaine_maintenance = Column(DateTime)
    observations = Column(Text)
    
    # Relations
    rapport = relationship("RapportThermique", back_populates="groupes_production")
    
    def __repr__(self):
        return f'<GroupeProductionThermique {self.nom_groupe} - Rapport {self.rapport_id}>'