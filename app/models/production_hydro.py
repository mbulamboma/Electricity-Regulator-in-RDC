"""
Modèles pour la production hydroélectrique
"""
from app.extensions import db
from app.models.base import BaseModel
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime


class CentraleHydro(BaseModel):
    """Modèle pour les centrales hydroélectriques"""
    __tablename__ = 'centrales_hydro'
    
    # Relations
    operateur_id = Column(Integer, ForeignKey('operateurs.id'), nullable=False)
    
    # Informations de base
    nom = Column(String(200), nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False)
    localisation = Column(String(200))
    province = Column(String(100))
    cours_eau = Column(String(100))
    
    # Caractéristiques techniques
    puissance_installee = Column(Float)  # MW
    puissance_disponible = Column(Float)  # MW
    hauteur_chute = Column(Float)  # mètres
    debit_equipement = Column(Float)  # m³/s
    type_centrale = Column(String(50))  # au fil de l'eau, réservoir, etc.
    
    # Ajout des champs manquants pour l'interface
    latitude = Column(Float)  # Coordonnées GPS
    longitude = Column(Float)
    type_turbine = Column(String(50))  # Type principal de turbine
    type_barrage = Column(String(50))  # Type de barrage
    niveau_tension = Column(Float)  # Niveau de tension principal
    superficie_bassin = Column(Float)  # Superficie du bassin versant en km²
    volume_retenue = Column(Float)  # Volume de retenue en millions m³
    statut = Column(String(50), default='operationnelle')  # operationnelle, maintenance, arret
    description = Column(Text)  # Description générale
    
    # Équipements
    nombre_groupes = Column(Integer, default=0)
    nombre_transformateurs = Column(Integer, default=0)
    tension_evacuation = Column(String(50))  # kV
    
    # Dates importantes
    date_mise_service = Column(DateTime)
    date_derniere_revision = Column(DateTime)
    
    # Informations complémentaires
    constructeur = Column(String(100))
    annee_construction = Column(Integer)
    observations = Column(Text)
    
    # Relations
    operateur = relationship("Operateur", back_populates="centrales_hydro")
    rapports = relationship("RapportHydro", back_populates="centrale", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<CentraleHydro {self.nom}>'
    
    def to_dict(self):
        """Convertir en dictionnaire"""
        data = super().to_dict()
        data.update({
            'operateur_id': self.operateur_id,
            'nom': self.nom,
            'code': self.code,
            'localisation': self.localisation,
            'province': self.province,
            'cours_eau': self.cours_eau,
            'puissance_installee': self.puissance_installee,
            'puissance_disponible': self.puissance_disponible,
            'hauteur_chute': self.hauteur_chute,
            'debit_equipement': self.debit_equipement,
            'type_centrale': self.type_centrale,
            'nombre_groupes': self.nombre_groupes,
            'nombre_transformateurs': self.nombre_transformateurs,
            'tension_evacuation': self.tension_evacuation,
            'date_mise_service': self.date_mise_service.isoformat() if self.date_mise_service else None,
            'date_derniere_revision': self.date_derniere_revision.isoformat() if self.date_derniere_revision else None,
            'constructeur': self.constructeur,
            'annee_construction': self.annee_construction,
            'observations': self.observations,
            'operateur_nom': self.operateur.nom if self.operateur else None,
            'nombre_rapports': len(self.rapports) if self.rapports else 0
        })
        return data


class RapportHydro(BaseModel):
    """Modèle pour les rapports de production hydroélectrique"""
    __tablename__ = 'rapports_hydro'
    
    # Relations
    centrale_id = Column(Integer, ForeignKey('centrales_hydro.id'), nullable=False)
    
    # Période de rapport
    annee = Column(Integer, nullable=False)
    mois = Column(Integer, nullable=False)
    periode_debut = Column(DateTime, nullable=False)
    periode_fin = Column(DateTime, nullable=False)
    
    # Données hydrologiques
    niveau_retenue_moyen = Column(Float)  # mètres
    niveau_retenue_min = Column(Float)
    niveau_retenue_max = Column(Float)
    debit_moyen = Column(Float)  # m³/s
    debit_min = Column(Float)
    debit_max = Column(Float)
    volume_turbiné = Column(Float)  # millions m³
    debit_reserve = Column(Float)  # m³/s - Débit réservé environnemental
    
    # Production
    energie_produite = Column(Float)  # MWh
    energie_disponible = Column(Float)  # MWh
    facteur_charge = Column(Float)  # %
    temps_fonctionnement = Column(Float)  # heures
    nombre_arrets = Column(Integer, default=0)
    duree_arrets = Column(Float, default=0.0)  # heures
    
    # Rendements
    rendement_global = Column(Float)  # %
    rendement_turbine = Column(Float)  # %
    rendement_alternateur = Column(Float)  # %
    
    # Maintenance et incidents
    maintenances_preventives = Column(Integer, default=0)
    maintenances_correctives = Column(Integer, default=0)
    incidents_majeurs = Column(Integer, default=0)
    description_incidents = Column(Text)
    
    # Données environnementales
    impact_environnemental = Column(Text)
    
    # Validation et statut
    statut = Column(String(50), default='brouillon')  # brouillon, validé, transmis
    date_validation = Column(DateTime)
    date_transmission = Column(DateTime)  # Date de transmission du rapport
    validé_par = Column(String(100))
    observations = Column(Text)
    
    # Relations
    centrale = relationship("CentraleHydro", back_populates="rapports")
    groupes_production = relationship("GroupeProduction", back_populates="rapport", cascade="all, delete-orphan")
    transformateurs = relationship("TransformateurRapport", back_populates="rapport", cascade="all, delete-orphan")
    donnees_mensuelles = relationship("DonneesMensuelles", back_populates="rapport", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<RapportHydro {self.centrale.nom if self.centrale else "N/A"} {self.mois}/{self.annee}>'
    
    def get_periode_str(self):
        """Obtenir la période sous forme de chaîne"""
        mois_noms = [
            '', 'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
            'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
        ]
        return f"{mois_noms[self.mois]} {self.annee}"
    
    def calcul_disponibilite(self):
        """Calculer la disponibilité en %"""
        if not self.temps_fonctionnement:
            return 0
        heures_mois = 24 * 30  # Approximation
        return min(100, (self.temps_fonctionnement / heures_mois) * 100)
    
    def to_dict(self):
        """Convertir en dictionnaire"""
        data = super().to_dict()
        data.update({
            'centrale_id': self.centrale_id,
            'annee': self.annee,
            'mois': self.mois,
            'periode_debut': self.periode_debut.isoformat() if self.periode_debut else None,
            'periode_fin': self.periode_fin.isoformat() if self.periode_fin else None,
            'niveau_retenue_moyen': self.niveau_retenue_moyen,
            'niveau_retenue_min': self.niveau_retenue_min,
            'niveau_retenue_max': self.niveau_retenue_max,
            'debit_moyen': self.debit_moyen,
            'debit_min': self.debit_min,
            'debit_max': self.debit_max,
            'volume_turbiné': self.volume_turbiné,
            'energie_produite': self.energie_produite,
            'energie_disponible': self.energie_disponible,
            'facteur_charge': self.facteur_charge,
            'temps_fonctionnement': self.temps_fonctionnement,
            'nombre_arrets': self.nombre_arrets,
            'duree_arrets': self.duree_arrets,
            'rendement_global': self.rendement_global,
            'rendement_turbine': self.rendement_turbine,
            'rendement_alternateur': self.rendement_alternateur,
            'maintenances_preventives': self.maintenances_preventives,
            'maintenances_correctives': self.maintenances_correctives,
            'incidents_majeurs': self.incidents_majeurs,
            'description_incidents': self.description_incidents,
            'debit_reserve': self.debit_reserve,
            'impact_environnemental': self.impact_environnemental,
            'statut': self.statut,
            'date_validation': self.date_validation.isoformat() if self.date_validation else None,
            'validé_par': self.validé_par,
            'observations': self.observations,
            'centrale_nom': self.centrale.nom if self.centrale else None,
            'periode_str': self.get_periode_str(),
            'disponibilite': self.calcul_disponibilite(),
            'nombre_groupes': len(self.groupes_production) if self.groupes_production else 0,
            'nombre_transformateurs': len(self.transformateurs) if self.transformateurs else 0
        })
        return data


class GroupeProduction(BaseModel):
    """Modèle pour les groupes de production d'une centrale"""
    __tablename__ = 'groupes_production'
    
    # Relations
    rapport_id = Column(Integer, ForeignKey('rapports_hydro.id'), nullable=False)
    
    # Identification
    numero_groupe = Column(String(10), nullable=False)
    nom_groupe = Column(String(100))
    
    # Caractéristiques techniques
    puissance_nominale = Column(Float)  # MW
    tension_nominale = Column(Float)  # kV
    vitesse_rotation = Column(Float)  # tr/min
    type_turbine = Column(String(50))  # Pelton, Francis, Kaplan, etc.
    
    # Données de fonctionnement
    heures_fonctionnement = Column(Float, default=0.0)
    energie_produite = Column(Float, default=0.0)  # MWh
    puissance_moyenne = Column(Float, default=0.0)  # MW
    puissance_max = Column(Float, default=0.0)  # MW
    
    # Arrêts et maintenance
    nombre_arrets_programme = Column(Integer, default=0)
    nombre_arrets_force = Column(Integer, default=0)
    duree_arrets_programme = Column(Float, default=0.0)  # heures
    duree_arrets_force = Column(Float, default=0.0)  # heures
    
    # Rendement et performance
    rendement_moyen = Column(Float)  # %
    facteur_charge = Column(Float)  # %
    disponibilite = Column(Float)  # %
    
    # Maintenance
    date_derniere_revision = Column(DateTime)
    type_derniere_revision = Column(String(100))
    prochaine_revision = Column(DateTime)
    
    # Observations
    incidents = Column(Text)
    travaux_realises = Column(Text)
    observations = Column(Text)
    
    # Relations
    rapport = relationship("RapportHydro", back_populates="groupes_production")
    
    def __repr__(self):
        return f'<GroupeProduction {self.numero_groupe}>'
    
    def calcul_facteur_charge(self):
        """Calculer le facteur de charge automatiquement"""
        if self.puissance_nominale and self.heures_fonctionnement and self.energie_produite:
            energie_theorique = self.puissance_nominale * self.heures_fonctionnement
            if energie_theorique > 0:
                return (self.energie_produite / energie_theorique) * 100
        return 0
    
    def calcul_disponibilite(self):
        """Calculer la disponibilité automatiquement"""
        heures_periode = 24 * 30  # Approximation pour un mois
        heures_indisponibles = (self.duree_arrets_programme or 0) + (self.duree_arrets_force or 0)
        if heures_periode > 0:
            return ((heures_periode - heures_indisponibles) / heures_periode) * 100
        return 0
    
    def to_dict(self):
        """Convertir en dictionnaire"""
        data = super().to_dict()
        data.update({
            'rapport_id': self.rapport_id,
            'numero_groupe': self.numero_groupe,
            'nom_groupe': self.nom_groupe,
            'puissance_nominale': self.puissance_nominale,
            'tension_nominale': self.tension_nominale,
            'vitesse_rotation': self.vitesse_rotation,
            'type_turbine': self.type_turbine,
            'heures_fonctionnement': self.heures_fonctionnement,
            'energie_produite': self.energie_produite,
            'puissance_moyenne': self.puissance_moyenne,
            'puissance_max': self.puissance_max,
            'nombre_arrets_programme': self.nombre_arrets_programme,
            'nombre_arrets_force': self.nombre_arrets_force,
            'duree_arrets_programme': self.duree_arrets_programme,
            'duree_arrets_force': self.duree_arrets_force,
            'rendement_moyen': self.rendement_moyen,
            'facteur_charge': self.facteur_charge or self.calcul_facteur_charge(),
            'disponibilite': self.disponibilite or self.calcul_disponibilite(),
            'date_derniere_revision': self.date_derniere_revision.isoformat() if self.date_derniere_revision else None,
            'type_derniere_revision': self.type_derniere_revision,
            'prochaine_revision': self.prochaine_revision.isoformat() if self.prochaine_revision else None,
            'incidents': self.incidents,
            'travaux_realises': self.travaux_realises,
            'observations': self.observations
        })
        return data


class TransformateurRapport(BaseModel):
    """Modèle pour les transformateurs dans un rapport"""
    __tablename__ = 'transformateurs_rapport'
    
    # Relations
    rapport_id = Column(Integer, ForeignKey('rapports_hydro.id'), nullable=False)
    
    # Identification
    numero_transformateur = Column(String(10), nullable=False)
    nom_transformateur = Column(String(100))
    
    # Caractéristiques
    puissance_nominale = Column(Float)  # MVA
    tension_primaire = Column(Float)  # kV
    tension_secondaire = Column(Float)  # kV
    type_refroidissement = Column(String(50))
    
    # Fonctionnement
    energie_transferee = Column(Float, default=0.0)  # MWh
    heures_service = Column(Float, default=0.0)
    charge_moyenne = Column(Float, default=0.0)  # %
    charge_max = Column(Float, default=0.0)  # %
    
    # Températures
    temperature_huile_moyenne = Column(Float)  # °C
    temperature_huile_max = Column(Float)  # °C
    temperature_enroulements_max = Column(Float)  # °C
    
    # Maintenance et état
    etat_general = Column(String(50), default='bon')  # bon, moyen, mauvais
    date_derniere_maintenance = Column(DateTime)
    type_maintenance = Column(String(100))
    prochaine_maintenance = Column(DateTime)
    
    # Incidents et observations
    incidents = Column(Text)
    travaux_realises = Column(Text)
    observations = Column(Text)
    
    # Relations
    rapport = relationship("RapportHydro", back_populates="transformateurs")
    
    def __repr__(self):
        return f'<TransformateurRapport {self.numero_transformateur}>'
    
    def to_dict(self):
        """Convertir en dictionnaire"""
        data = super().to_dict()
        data.update({
            'rapport_id': self.rapport_id,
            'numero_transformateur': self.numero_transformateur,
            'nom_transformateur': self.nom_transformateur,
            'puissance_nominale': self.puissance_nominale,
            'tension_primaire': self.tension_primaire,
            'tension_secondaire': self.tension_secondaire,
            'type_refroidissement': self.type_refroidissement,
            'energie_transferee': self.energie_transferee,
            'heures_service': self.heures_service,
            'charge_moyenne': self.charge_moyenne,
            'charge_max': self.charge_max,
            'temperature_huile_moyenne': self.temperature_huile_moyenne,
            'temperature_huile_max': self.temperature_huile_max,
            'temperature_enroulements_max': self.temperature_enroulements_max,
            'etat_general': self.etat_general,
            'date_derniere_maintenance': self.date_derniere_maintenance.isoformat() if self.date_derniere_maintenance else None,
            'type_maintenance': self.type_maintenance,
            'prochaine_maintenance': self.prochaine_maintenance.isoformat() if self.prochaine_maintenance else None,
            'incidents': self.incidents,
            'travaux_realises': self.travaux_realises,
            'observations': self.observations
        })
        return data


class DonneesMensuelles(BaseModel):
    """Modèle pour les données techniques mensuelles détaillées"""
    __tablename__ = 'donnees_mensuelles'
    
    # Relations
    rapport_id = Column(Integer, ForeignKey('rapports_hydro.id'), nullable=False)
    
    # Jour du mois (1-31)
    jour = Column(Integer, nullable=False)
    
    # Données hydrologiques journalières
    niveau_retenue = Column(Float)  # mètres
    debit_turbiné = Column(Float)  # m³/s
    debit_déversé = Column(Float)  # m³/s
    cote_aval = Column(Float)  # mètres
    
    # Production journalière
    energie_produite = Column(Float)  # MWh
    puissance_moyenne = Column(Float)  # MW
    puissance_max = Column(Float)  # MW
    heures_fonctionnement = Column(Float)  # heures
    
    # Météorologie
    temperature_moyenne = Column(Float)  # °C
    pluviometrie = Column(Float)  # mm
    
    # Événements particuliers
    evenements = Column(Text)  # Arrêts, incidents, etc.
    
    # Relations
    rapport = relationship("RapportHydro", back_populates="donnees_mensuelles")
    
    def __repr__(self):
        return f'<DonneesMensuelles Jour {self.jour}>'
    
    def to_dict(self):
        """Convertir en dictionnaire"""
        data = super().to_dict()
        data.update({
            'rapport_id': self.rapport_id,
            'jour': self.jour,
            'niveau_retenue': self.niveau_retenue,
            'debit_turbiné': self.debit_turbiné,
            'debit_déversé': self.debit_déversé,
            'cote_aval': self.cote_aval,
            'energie_produite': self.energie_produite,
            'puissance_moyenne': self.puissance_moyenne,
            'puissance_max': self.puissance_max,
            'heures_fonctionnement': self.heures_fonctionnement,
            'temperature_moyenne': self.temperature_moyenne,
            'pluviometrie': self.pluviometrie,
            'evenements': self.evenements
        })
        return data