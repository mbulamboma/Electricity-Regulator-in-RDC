"""
Modèles pour le transport d'électricité
"""
from app.extensions import db
from app.models.base import BaseModel
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime


class LigneTransport(BaseModel):
    """Modèle pour les lignes de transport électrique"""
    __tablename__ = 'lignes_transport'
    
    # Relations
    operateur_id = Column(Integer, ForeignKey('operateurs.id'), nullable=False)
    
    # Informations de base
    nom = Column(String(200), nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False)
    designation = Column(String(300))
    
    # Caractéristiques électriques
    tension_nominale = Column(Float, nullable=False)  # kV
    longueur_totale = Column(Float)  # km
    nombre_circuits = Column(Integer, default=1)
    type_ligne = Column(String(50))  # aérienne, souterraine, mixte
    
    # Points de connexion
    poste_depart = Column(String(200))
    poste_arrivee = Column(String(200))
    
    # Coordonnées géographiques (points de passage)
    coordonnees_tracé = Column(JSON)  # Liste de points [lat, lng]
    
    # Caractéristiques techniques
    type_conducteur = Column(String(100))  # ACSR, AAAC, etc.
    section_conducteur = Column(Float)  # mm²
    nombre_conducteurs_par_phase = Column(Integer, default=1)
    capacite_thermique = Column(Float)  # A
    capacite_transport = Column(Float)  # MVA
    
    # Support et isolation
    type_supports = Column(String(100))  # treillis, béton, bois
    hauteur_moyenne_supports = Column(Float)  # m
    portee_moyenne = Column(Float)  # m
    type_isolateurs = Column(String(100))
    
    # Protection et terre
    conducteur_terre = Column(Boolean, default=True)
    cable_garde = Column(Boolean, default=False)
    systeme_protection = Column(String(200))
    
    # Exploitation
    date_mise_service = Column(DateTime)
    statut = Column(String(50), default='en_service')  # en_service, hors_service, maintenance
    proprietaire = Column(String(200))
    exploitant = Column(String(200))
    
    # Performance
    taux_indisponibilite = Column(Float, default=0.0)  # %
    nombre_defauts_annuels = Column(Integer, default=0)
    duree_moyenne_coupures = Column(Float, default=0.0)  # minutes
    
    # Maintenance
    date_derniere_inspection = Column(DateTime)
    periodicite_inspection = Column(Integer, default=12)  # mois
    date_derniere_maintenance = Column(DateTime)
    
    # Observations
    observations = Column(Text)
    
    # Relations
    operateur = relationship("Operateur", back_populates="lignes_transport")
    rapports = relationship("RapportTransport", back_populates="ligne", cascade="all, delete-orphan")
    postes_depart = relationship("PosteTransport", foreign_keys="PosteTransport.ligne_depart_id", back_populates="lignes_depart")
    postes_arrivee = relationship("PosteTransport", foreign_keys="PosteTransport.ligne_arrivee_id", back_populates="lignes_arrivee")
    
    def __repr__(self):
        return f'<LigneTransport {self.nom} - {self.tension_nominale}kV>'
    
    def to_dict(self):
        """Convertir en dictionnaire"""
        data = super().to_dict()
        data.update({
            'operateur_id': self.operateur_id,
            'nom': self.nom,
            'code': self.code,
            'designation': self.designation,
            'tension_nominale': self.tension_nominale,
            'longueur_totale': self.longueur_totale,
            'nombre_circuits': self.nombre_circuits,
            'type_ligne': self.type_ligne,
            'poste_depart': self.poste_depart,
            'poste_arrivee': self.poste_arrivee,
            'coordonnees_tracé': self.coordonnees_tracé,
            'type_conducteur': self.type_conducteur,
            'section_conducteur': self.section_conducteur,
            'capacite_transport': self.capacite_transport,
            'statut': self.statut,
            'taux_indisponibilite': self.taux_indisponibilite,
            'observations': self.observations,
            'operateur_nom': self.operateur.nom if self.operateur else None
        })
        return data


class PosteTransport(BaseModel):
    """Modèle pour les postes de transformation et de répartition"""
    __tablename__ = 'postes_transport'
    
    # Relations
    operateur_id = Column(Integer, ForeignKey('operateurs.id'), nullable=False)
    ligne_depart_id = Column(Integer, ForeignKey('lignes_transport.id'))
    ligne_arrivee_id = Column(Integer, ForeignKey('lignes_transport.id'))
    
    # Informations de base
    nom = Column(String(200), nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False)
    type_poste = Column(String(50))  # transformation, répartition, distribution
    
    # Localisation
    localisation = Column(String(200))
    province = Column(String(100))
    latitude = Column(Float)
    longitude = Column(Float)
    altitude = Column(Float)
    
    # Niveaux de tension
    tension_primaire = Column(Float)  # kV
    tension_secondaire = Column(Float)  # kV
    tension_tertiaire = Column(Float)  # kV (optionnel)
    
    # Configuration
    nombre_transformateurs = Column(Integer, default=0)
    puissance_installee = Column(Float)  # MVA
    puissance_disponible = Column(Float)  # MVA
    schéma_unifilaire = Column(String(100))  # simple barre, double barre, etc.
    
    # Équipements de protection
    systeme_protection = Column(JSON)  # Liste des protections
    nombre_disjoncteurs = Column(Integer, default=0)
    nombre_sectionneurs = Column(Integer, default=0)
    parafoudres = Column(Boolean, default=True)
    
    # Surveillance et contrôle
    systeme_scada = Column(Boolean, default=False)
    telecommande = Column(Boolean, default=False)
    telemesure = Column(Boolean, default=False)
    
    # Exploitation
    date_mise_service = Column(DateTime)
    statut = Column(String(50), default='en_service')
    regime_neutre = Column(String(50))  # direct, résistance, bobine
    
    # Performance
    taux_disponibilite = Column(Float, default=100.0)  # %
    nombre_incidents_annuels = Column(Integer, default=0)
    duree_moyenne_indisponibilite = Column(Float, default=0.0)  # heures
    
    # Maintenance
    date_derniere_maintenance = Column(DateTime)
    periodicite_maintenance = Column(Integer, default=6)  # mois
    
    # Sécurité et environnement
    cloture_securite = Column(Boolean, default=True)
    systeme_incendie = Column(Boolean, default=False)
    bac_retention_huile = Column(Boolean, default=False)
    
    # Observations
    description = Column(Text)
    observations = Column(Text)
    
    # Relations
    operateur = relationship("Operateur", back_populates="postes_transport")
    lignes_depart = relationship("LigneTransport", foreign_keys=[ligne_depart_id], back_populates="postes_depart")
    lignes_arrivee = relationship("LigneTransport", foreign_keys=[ligne_arrivee_id], back_populates="postes_arrivee")
    transformateurs = relationship("TransformateurTransport", back_populates="poste", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<PosteTransport {self.nom} - {self.tension_primaire}/{self.tension_secondaire}kV>'
    
    def to_dict(self):
        """Convertir en dictionnaire"""
        data = super().to_dict()
        data.update({
            'operateur_id': self.operateur_id,
            'nom': self.nom,
            'code': self.code,
            'type_poste': self.type_poste,
            'localisation': self.localisation,
            'province': self.province,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'tension_primaire': self.tension_primaire,
            'tension_secondaire': self.tension_secondaire,
            'puissance_installee': self.puissance_installee,
            'puissance_disponible': self.puissance_disponible,
            'nombre_transformateurs': self.nombre_transformateurs,
            'statut': self.statut,
            'taux_disponibilite': self.taux_disponibilite,
            'observations': self.observations,
            'operateur_nom': self.operateur.nom if self.operateur else None
        })
        return data


class TransformateurTransport(BaseModel):
    """Modèle pour les transformateurs de transport"""
    __tablename__ = 'transformateurs_transport'
    
    # Relations
    poste_id = Column(Integer, ForeignKey('postes_transport.id'), nullable=False)
    
    # Identification
    nom = Column(String(200), nullable=False)
    numero_serie = Column(String(100))
    constructeur = Column(String(100))
    annee_fabrication = Column(Integer)
    
    # Caractéristiques électriques
    puissance_nominale = Column(Float, nullable=False)  # MVA
    tension_primaire = Column(Float, nullable=False)  # kV
    tension_secondaire = Column(Float, nullable=False)  # kV
    tension_tertiaire = Column(Float)  # kV (optionnel)
    couplage = Column(String(20))  # Dy11, Yd11, etc.
    
    # Caractéristiques techniques
    type_refroidissement = Column(String(50))  # ONAN, ONAF, OFAF
    poids_total = Column(Float)  # tonnes
    volume_huile = Column(Float)  # litres
    type_huile = Column(String(100))
    
    # Impédances et pertes
    impedance_cc = Column(Float)  # %
    pertes_vide = Column(Float)  # kW
    pertes_charge = Column(Float)  # kW
    courant_vide = Column(Float)  # %
    
    # Réglage
    changeur_prises = Column(Boolean, default=False)
    nombre_prises = Column(Integer, default=0)
    plage_reglage = Column(Float)  # %
    pas_reglage = Column(Float)  # %
    
    # État et maintenance
    statut = Column(String(50), default='en_service')
    date_mise_service = Column(DateTime)
    date_derniere_maintenance = Column(DateTime)
    type_derniere_maintenance = Column(String(100))
    prochaine_maintenance = Column(DateTime)
    
    # Surveillance
    temperature_huile = Column(Float)  # °C
    temperature_enroulements = Column(Float)  # °C
    niveau_huile = Column(String(50))  # normal, bas, critique
    pression_huile = Column(Float)  # bar
    
    # Tests et analyses
    date_derniere_analyse_huile = Column(DateTime)
    resultat_analyse_huile = Column(Text)
    date_dernier_test_isolement = Column(DateTime)
    resistance_isolement = Column(Float)  # MΩ
    
    # Observations
    observations = Column(Text)
    
    # Relations
    poste = relationship("PosteTransport", back_populates="transformateurs")
    
    def __repr__(self):
        return f'<TransformateurTransport {self.nom} - {self.puissance_nominale}MVA>'
    
    def to_dict(self):
        """Convertir en dictionnaire"""
        data = super().to_dict()
        data.update({
            'poste_id': self.poste_id,
            'nom': self.nom,
            'numero_serie': self.numero_serie,
            'constructeur': self.constructeur,
            'puissance_nominale': self.puissance_nominale,
            'tension_primaire': self.tension_primaire,
            'tension_secondaire': self.tension_secondaire,
            'couplage': self.couplage,
            'type_refroidissement': self.type_refroidissement,
            'statut': self.statut,
            'temperature_huile': self.temperature_huile,
            'niveau_huile': self.niveau_huile,
            'observations': self.observations
        })
        return data


class RapportTransport(BaseModel):
    """Modèle pour les rapports de transport d'électricité"""
    __tablename__ = 'rapports_transport'
    
    # Relations
    ligne_id = Column(Integer, ForeignKey('lignes_transport.id'), nullable=False)
    
    # Période
    annee = Column(Integer, nullable=False)
    mois = Column(Integer, nullable=False)
    periode_debut = Column(DateTime, nullable=False)
    periode_fin = Column(DateTime, nullable=False)
    
    # Énergie transitée
    energie_transitee = Column(Float)  # MWh
    energie_maximale = Column(Float)  # MW (puissance max)
    heure_pointe = Column(String(10))  # HH:MM
    energie_minimale = Column(Float)  # MW (puissance min)
    heure_creuse = Column(String(10))  # HH:MM
    
    # Facteur de charge et utilisation
    facteur_charge = Column(Float)  # %
    taux_utilisation = Column(Float)  # %
    charge_moyenne = Column(Float)  # MW
    
    # Qualité et fiabilité
    nombre_incidents = Column(Integer, default=0)
    duree_total_incidents = Column(Float, default=0.0)  # heures
    energie_non_fournie = Column(Float, default=0.0)  # MWh
    saidi = Column(Float, default=0.0)  # minutes
    saifi = Column(Float, default=0.0)  # interruptions/client
    
    # Maintenance
    maintenances_programmees = Column(Integer, default=0)
    duree_maintenances_programmees = Column(Float, default=0.0)  # heures
    maintenances_urgentes = Column(Integer, default=0)
    duree_maintenances_urgentes = Column(Float, default=0.0)  # heures
    
    # Pertes techniques
    pertes_ligne = Column(Float, default=0.0)  # %
    pertes_transformateurs = Column(Float, default=0.0)  # %
    pertes_totales = Column(Float, default=0.0)  # %
    
    # Conditions de fonctionnement
    temperature_moyenne = Column(Float)  # °C
    temperature_maximale = Column(Float)  # °C
    humidite_moyenne = Column(Float)  # %
    vitesse_vent_moyenne = Column(Float)  # m/s
    
    # Incidents et événements
    description_incidents = Column(Text)
    causes_incidents = Column(Text)
    actions_correctives = Column(Text)
    
    # Performance environnementale
    emissions_sf6 = Column(Float, default=0.0)  # kg eq CO2
    consommation_auxiliaires = Column(Float, default=0.0)  # kWh
    
    # Validation
    statut = Column(String(50), default='brouillon')  # brouillon, validé, transmis
    date_validation = Column(DateTime)
    date_transmission = Column(DateTime)
    validé_par = Column(String(100))
    observations = Column(Text)
    
    # Relations
    ligne = relationship("LigneTransport", back_populates="rapports")
    données_quotidiennes = relationship("DonneesTransportQuotidiennes", back_populates="rapport", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<RapportTransport {self.ligne.nom if self.ligne else "N/A"} - {self.mois}/{self.annee}>'
    
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
            'ligne_id': self.ligne_id,
            'annee': self.annee,
            'mois': self.mois,
            'periode_debut': self.periode_debut.isoformat() if self.periode_debut else None,
            'periode_fin': self.periode_fin.isoformat() if self.periode_fin else None,
            'energie_transitee': self.energie_transitee,
            'energie_maximale': self.energie_maximale,
            'facteur_charge': self.facteur_charge,
            'taux_utilisation': self.taux_utilisation,
            'nombre_incidents': self.nombre_incidents,
            'duree_total_incidents': self.duree_total_incidents,
            'saidi': self.saidi,
            'saifi': self.saifi,
            'pertes_totales': self.pertes_totales,
            'statut': self.statut,
            'observations': self.observations,
            'ligne_nom': self.ligne.nom if self.ligne else None,
            'ligne_code': self.ligne.code if self.ligne else None,
            'periode_str': self.get_periode_str()
        })
        return data


class DonneesTransportQuotidiennes(BaseModel):
    """Modèle pour les données quotidiennes de transport"""
    __tablename__ = 'donnees_transport_quotidiennes'
    
    # Relations
    rapport_id = Column(Integer, ForeignKey('rapports_transport.id'), nullable=False)
    
    # Date
    date = Column(DateTime, nullable=False)
    
    # Énergie et puissance
    energie_transitee = Column(Float)  # MWh
    puissance_maximale = Column(Float)  # MW
    heure_puissance_max = Column(String(10))  # HH:MM
    puissance_minimale = Column(Float)  # MW
    heure_puissance_min = Column(String(10))  # HH:MM
    puissance_moyenne = Column(Float)  # MW
    
    # Qualité
    nombre_incidents = Column(Integer, default=0)
    duree_incidents = Column(Float, default=0.0)  # minutes
    type_incidents = Column(String(200))
    
    # Conditions
    temperature_max = Column(Float)  # °C
    humidite = Column(Float)  # %
    
    # Relations
    rapport = relationship("RapportTransport", back_populates="données_quotidiennes")
    
    def __repr__(self):
        return f'<DonneesTransportQuotidiennes {self.date.strftime("%d/%m/%Y") if self.date else "N/A"}>'