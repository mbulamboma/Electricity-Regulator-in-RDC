"""
Modèles pour la distribution d'électricité
"""
from app.extensions import db
from app.models.base import BaseModel
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime


class ReseauDistribution(BaseModel):
    """Modèle pour les réseaux de distribution électrique"""
    __tablename__ = 'reseaux_distribution'
    
    # Relations
    operateur_id = Column(Integer, ForeignKey('operateurs.id'), nullable=False)
    
    # Informations de base
    nom = Column(String(200), nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False)
    type_reseau = Column(String(50))  # urbain, rural, industriel
    
    # Zone de desserte
    zone_desserte = Column(String(200))
    province = Column(String(100))
    commune = Column(String(100))
    superficie = Column(Float)  # km²
    
    # Coordonnées de la zone
    coordonnees_zone = Column(JSON)  # Polygone de la zone
    centre_latitude = Column(Float)
    centre_longitude = Column(Float)
    
    # Caractéristiques du réseau
    tension_distribution = Column(Float, nullable=False)  # kV (MT)
    tension_basse = Column(Float, default=0.4)  # kV (BT)
    schema_exploitation = Column(String(50))  # radial, bouclé, maillé
    
    # Lignes et infrastructure
    longueur_reseau_mt = Column(Float)  # km (moyenne tension)
    longueur_reseau_bt = Column(Float)  # km (basse tension)
    nombre_postes_source = Column(Integer, default=0)
    nombre_postes_distribution = Column(Integer, default=0)
    nombre_transformateurs_mt_bt = Column(Integer, default=0)
    
    # Type de réseau
    type_construction = Column(String(50))  # aérien, souterrain, mixte
    pourcentage_aerien = Column(Float, default=100.0)  # %
    pourcentage_souterrain = Column(Float, default=0.0)  # %
    
    # Clientèle
    nombre_clients_total = Column(Integer, default=0)
    nombre_clients_domestiques = Column(Integer, default=0)
    nombre_clients_commerciaux = Column(Integer, default=0)
    nombre_clients_industriels = Column(Integer, default=0)
    nombre_clients_autres = Column(Integer, default=0)
    
    # Puissance et énergie
    puissance_installee = Column(Float)  # MVA
    puissance_souscrite = Column(Float)  # MVA
    puissance_maximale = Column(Float)  # MW
    demande_moyenne = Column(Float)  # MW
    
    # Performance
    taux_electrification = Column(Float, default=0.0)  # %
    densite_clientele = Column(Float, default=0.0)  # clients/km²
    charge_lineique = Column(Float, default=0.0)  # kVA/km
    
    # Qualité de service
    saidi_objectif = Column(Float, default=0.0)  # minutes/an
    saifi_objectif = Column(Float, default=0.0)  # coupures/an
    taux_disponibilite_objectif = Column(Float, default=99.0)  # %
    
    # Exploitation
    date_mise_service = Column(DateTime)
    statut = Column(String(50), default='en_service')
    gestionnaire = Column(String(200))
    
    # Observations
    description = Column(Text)
    observations = Column(Text)
    
    # Relations
    operateur = relationship("Operateur", back_populates="reseaux_distribution")
    rapports = relationship("RapportDistribution", back_populates="reseau", cascade="all, delete-orphan")
    postes_distribution = relationship("PosteDistribution", back_populates="reseau", cascade="all, delete-orphan")
    feeders = relationship("FeederDistribution", back_populates="reseau", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<ReseauDistribution {self.nom} - {self.tension_distribution}kV>'
    
    def to_dict(self):
        """Convertir en dictionnaire"""
        data = super().to_dict()
        data.update({
            'operateur_id': self.operateur_id,
            'nom': self.nom,
            'code': self.code,
            'type_reseau': self.type_reseau,
            'zone_desserte': self.zone_desserte,
            'province': self.province,
            'commune': self.commune,
            'superficie': self.superficie,
            'tension_distribution': self.tension_distribution,
            'longueur_reseau_mt': self.longueur_reseau_mt,
            'longueur_reseau_bt': self.longueur_reseau_bt,
            'nombre_clients_total': self.nombre_clients_total,
            'puissance_installee': self.puissance_installee,
            'taux_electrification': self.taux_electrification,
            'statut': self.statut,
            'observations': self.observations,
            'operateur_nom': self.operateur.nom if self.operateur else None
        })
        return data


class PosteDistribution(BaseModel):
    """Modèle pour les postes de distribution (postes sources et HTA/BT)"""
    __tablename__ = 'postes_distribution'
    
    # Relations
    reseau_id = Column(Integer, ForeignKey('reseaux_distribution.id'), nullable=False)
    
    # Informations de base
    nom = Column(String(200), nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False)
    type_poste = Column(String(50))  # source, distribution, client
    
    # Localisation
    localisation = Column(String(200))
    quartier = Column(String(100))
    latitude = Column(Float)
    longitude = Column(Float)
    
    # Caractéristiques électriques
    tension_primaire = Column(Float)  # kV
    tension_secondaire = Column(Float)  # kV
    puissance_installee = Column(Float)  # kVA
    puissance_souscrite = Column(Float)  # kVA
    
    # Configuration
    nombre_transformateurs = Column(Integer, default=1)
    nombre_departs = Column(Integer, default=0)
    schema_exploitation = Column(String(50))  # normal ouvert, normal fermé
    
    # Protection
    protection_primaire = Column(String(100))  # disjoncteur, fusible
    protection_secondaire = Column(String(100))
    mise_terre = Column(String(50))  # TT, TN, IT
    
    # Clientèle desservie
    nombre_clients_raccordes = Column(Integer, default=0)
    types_clients = Column(JSON)  # Répartition par type
    
    # Performance
    taux_charge = Column(Float, default=0.0)  # %
    facteur_puissance = Column(Float, default=0.9)
    pertes_transformateur = Column(Float, default=0.0)  # %
    
    # État et maintenance
    statut = Column(String(50), default='en_service')
    date_mise_service = Column(DateTime)
    date_derniere_maintenance = Column(DateTime)
    
    # Observations
    observations = Column(Text)
    
    # Relations
    reseau = relationship("ReseauDistribution", back_populates="postes_distribution")
    transformateurs = relationship("TransformateurDistribution", back_populates="poste_distribution", cascade="all, delete-orphan", foreign_keys="TransformateurDistribution.poste_distribution_id")
    
    def __repr__(self):
        return f'<PosteDistribution {self.nom} - {self.puissance_installee}kVA>'
    
    def to_dict(self):
        """Convertir en dictionnaire"""
        data = super().to_dict()
        data.update({
            'reseau_id': self.reseau_id,
            'nom': self.nom,
            'code': self.code,
            'type_poste': self.type_poste,
            'localisation': self.localisation,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'tension_primaire': self.tension_primaire,
            'tension_secondaire': self.tension_secondaire,
            'puissance_installee': self.puissance_installee,
            'nombre_clients_raccordes': self.nombre_clients_raccordes,
            'taux_charge': self.taux_charge,
            'statut': self.statut,
            'observations': self.observations
        })
        return data


class TransformateurDistribution(BaseModel):
    """Modèle pour les transformateurs de distribution"""
    __tablename__ = 'transformateurs_distribution'
    
    # Relations
    poste_distribution_id = Column(Integer, ForeignKey('postes_distribution.id'), nullable=False)
    
    # Identification
    nom = Column(String(200), nullable=False)
    type_transformateur = Column(String(50))  # monophase, triphase, distribution, puissance
    numero_serie = Column(String(100))
    constructeur = Column(String(100))
    modele = Column(String(100))
    annee_fabrication = Column(Integer)
    date_installation = Column(DateTime)
    
    # Caractéristiques électriques
    puissance_nominale = Column(Float, nullable=False)  # kVA
    tension_primaire = Column(Float, nullable=False)  # kV
    tension_secondaire = Column(Float, nullable=False)  # V
    couplage = Column(String(20))  # Dyn11, Yzn11, etc.
    
    # Caractéristiques techniques
    type_refroidissement = Column(String(50))  # ONAN, AN, AF
    type_installation = Column(String(50))  # poteau, cabine, sol
    indice_protection = Column(String(10))  # IP23, IP54, etc.
    classe_isolation = Column(String(10))  # A, B, F, H
    
    # Impédances et pertes
    impedance_cc = Column(Float)  # %
    pertes_vide = Column(Float)  # W
    pertes_charge = Column(Float)  # W
    courant_vide = Column(Float)  # %
    
    # Réglage
    prises_reglage = Column(Integer, default=0)
    plage_reglage = Column(Float, default=0.0)  # %
    position_prise = Column(Integer, default=0)
    
    # Charge et utilisation
    charge_actuelle = Column(Float, default=0.0)  # %
    charge_maximale = Column(Float, default=0.0)  # %
    heures_fonctionnement = Column(Float, default=0.0)
    
    # État et maintenance
    statut = Column(String(50), default='en_service')
    date_mise_service = Column(DateTime)
    date_derniere_maintenance = Column(DateTime)
    type_derniere_maintenance = Column(String(100))
    prochaine_maintenance = Column(DateTime)
    
    # Surveillance
    temperature_huile = Column(Float)  # °C
    niveau_huile = Column(String(50))  # normal, bas, critique
    
    # Position géographique
    latitude = Column(Float)
    longitude = Column(Float)
    
    # Observations
    observations = Column(Text)
    
    # Relations
    poste_distribution = relationship("PosteDistribution", back_populates="transformateurs", foreign_keys=[poste_distribution_id])
    
    def __repr__(self):
        return f'<TransformateurDistribution {self.nom} - {self.puissance_nominale}kVA>'
    
    def to_dict(self):
        """Convertir en dictionnaire"""
        data = super().to_dict()
        data.update({
            'poste_distribution_id': self.poste_distribution_id,
            'nom': self.nom,
            'numero_serie': self.numero_serie,
            'constructeur': self.constructeur,
            'puissance_nominale': self.puissance_nominale,
            'tension_primaire': self.tension_primaire,
            'tension_secondaire': self.tension_secondaire,
            'couplage': self.couplage,
            'type_installation': self.type_installation,
            'charge_actuelle': self.charge_actuelle,
            'statut': self.statut,
            'observations': self.observations
        })
        return data


class FeederDistribution(BaseModel):
    """Modèle pour les feeders (départs) de distribution"""
    __tablename__ = 'feeders_distribution'
    
    # Relations
    reseau_id = Column(Integer, ForeignKey('reseaux_distribution.id'), nullable=False)
    poste_source_id = Column(Integer, ForeignKey('postes_distribution.id'))
    
    # Informations de base
    nom = Column(String(200), nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False)
    type_feeder = Column(String(50))  # urbain, rural, industriel
    
    # Caractéristiques électriques
    tension_nominale = Column(Float, nullable=False)  # kV
    longueur_totale = Column(Float)  # km
    section_conducteur = Column(Float)  # mm²
    type_conducteur = Column(String(100))  # Al, Cu, ACSR
    
    # Topologie
    type_reseau = Column(String(50))  # radial, bouclé
    nombre_branches = Column(Integer, default=1)
    coordonnees_tracé = Column(JSON)  # Tracé du feeder
    
    # Protection
    protection_tete = Column(String(100))  # disjoncteur, réenclencheur
    reglage_protection = Column(JSON)  # Paramètres de protection
    automatisation = Column(Boolean, default=False)
    
    # Clientèle
    nombre_clients = Column(Integer, default=0)
    puissance_souscrite = Column(Float, default=0.0)  # kVA
    charge_maximale = Column(Float, default=0.0)  # kW
    
    # Performance
    taux_charge = Column(Float, default=0.0)  # %
    pertes_techniques = Column(Float, default=0.0)  # %
    facteur_puissance = Column(Float, default=0.9)
    
    # Fiabilité
    saidi_annuel = Column(Float, default=0.0)  # minutes
    saifi_annuel = Column(Float, default=0.0)  # coupures
    nombre_defauts_annuels = Column(Integer, default=0)
    
    # État
    statut = Column(String(50), default='en_service')
    date_mise_service = Column(DateTime)
    
    # Observations
    observations = Column(Text)
    
    # Relations
    reseau = relationship("ReseauDistribution", back_populates="feeders")
    poste_source = relationship("PosteDistribution", foreign_keys=[poste_source_id])
    
    def __repr__(self):
        return f'<FeederDistribution {self.nom} - {self.tension_nominale}kV>'
    
    def to_dict(self):
        """Convertir en dictionnaire"""
        data = super().to_dict()
        data.update({
            'reseau_id': self.reseau_id,
            'nom': self.nom,
            'code': self.code,
            'type_feeder': self.type_feeder,
            'tension_nominale': self.tension_nominale,
            'longueur_totale': self.longueur_totale,
            'nombre_clients': self.nombre_clients,
            'puissance_souscrite': self.puissance_souscrite,
            'taux_charge': self.taux_charge,
            'saidi_annuel': self.saidi_annuel,
            'saifi_annuel': self.saifi_annuel,
            'statut': self.statut,
            'observations': self.observations
        })
        return data


class RapportDistribution(BaseModel):
    """Modèle pour les rapports de distribution d'électricité"""
    __tablename__ = 'rapports_distribution'
    
    # Relations
    reseau_id = Column(Integer, ForeignKey('reseaux_distribution.id'), nullable=False)
    
    # Période
    annee = Column(Integer, nullable=False)
    mois = Column(Integer, nullable=False)
    periode_debut = Column(DateTime, nullable=False)
    periode_fin = Column(DateTime, nullable=False)
    
    # Énergie et approvisionnement
    energie_achetee = Column(Float)  # MWh
    energie_distribuee = Column(Float)  # MWh
    energie_vendue = Column(Float)  # MWh
    pointe_distribution = Column(Float)  # MW
    heure_pointe = Column(String(10))  # HH:MM
    
    # Clientèle
    nombre_clients_debut = Column(Integer, default=0)
    nouveaux_raccordements = Column(Integer, default=0)
    resiliations = Column(Integer, default=0)
    nombre_clients_fin = Column(Integer, default=0)
    
    # Répartition clientèle
    clients_domestiques = Column(Integer, default=0)
    clients_commerciaux = Column(Integer, default=0)
    clients_industriels = Column(Integer, default=0)
    clients_autres = Column(Integer, default=0)
    
    # Consommation par catégorie
    energie_domestique = Column(Float, default=0.0)  # MWh
    energie_commerciale = Column(Float, default=0.0)  # MWh
    energie_industrielle = Column(Float, default=0.0)  # MWh
    energie_autres = Column(Float, default=0.0)  # MWh
    
    # Qualité de fourniture
    nombre_coupures = Column(Integer, default=0)
    duree_total_coupures = Column(Float, default=0.0)  # minutes
    saidi_realise = Column(Float, default=0.0)  # minutes
    saifi_realise = Column(Float, default=0.0)  # coupures/client
    energie_non_distribuee = Column(Float, default=0.0)  # MWh
    
    # Causes des coupures
    coupures_programmees = Column(Integer, default=0)
    coupures_incidents = Column(Integer, default=0)
    coupures_climatiques = Column(Integer, default=0)
    coupures_tiers = Column(Integer, default=0)
    
    # Pertes
    pertes_techniques = Column(Float, default=0.0)  # %
    pertes_non_techniques = Column(Float, default=0.0)  # %
    pertes_totales = Column(Float, default=0.0)  # %
    energie_pertes = Column(Float, default=0.0)  # MWh
    
    # Maintenance
    maintenances_preventives = Column(Integer, default=0)
    maintenances_correctives = Column(Integer, default=0)
    travaux_extension = Column(Integer, default=0)
    investissements = Column(Float, default=0.0)  # USD
    
    # Performance technique
    taux_disponibilite = Column(Float, default=0.0)  # %
    facteur_charge = Column(Float, default=0.0)  # %
    facteur_puissance_moyen = Column(Float, default=0.0)
    
    # Qualité tension
    variations_tension = Column(Integer, default=0)
    harmoniques_depassement = Column(Integer, default=0)
    desequilibres_tension = Column(Integer, default=0)
    
    # Réclamations et satisfaction
    nombre_reclamations = Column(Integer, default=0)
    reclamations_qualite = Column(Integer, default=0)
    reclamations_facturation = Column(Integer, default=0)
    taux_satisfaction = Column(Float, default=0.0)  # %
    
    # Aspects environnementaux
    emissions_evitees = Column(Float, default=0.0)  # tonnes CO2
    consommation_auxiliaires = Column(Float, default=0.0)  # MWh
    
    # Validation
    statut = Column(String(50), default='brouillon')  # brouillon, validé, transmis
    date_validation = Column(DateTime)
    date_transmission = Column(DateTime)
    validé_par = Column(String(100))
    observations = Column(Text)
    
    # Relations
    reseau = relationship("ReseauDistribution", back_populates="rapports")
    donnees_quotidiennes = relationship("DonneesDistributionQuotidiennes", back_populates="rapport", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<RapportDistribution {self.reseau.nom if self.reseau else "N/A"} - {self.mois}/{self.annee}>'
    
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
            'reseau_id': self.reseau_id,
            'annee': self.annee,
            'mois': self.mois,
            'periode_debut': self.periode_debut.isoformat() if self.periode_debut else None,
            'periode_fin': self.periode_fin.isoformat() if self.periode_fin else None,
            'energie_achetee': self.energie_achetee,
            'energie_distribuee': self.energie_distribuee,
            'energie_vendue': self.energie_vendue,
            'nombre_clients_fin': self.nombre_clients_fin,
            'saidi_realise': self.saidi_realise,
            'saifi_realise': self.saifi_realise,
            'pertes_totales': self.pertes_totales,
            'taux_disponibilite': self.taux_disponibilite,
            'statut': self.statut,
            'observations': self.observations,
            'reseau_nom': self.reseau.nom if self.reseau else None,
            'reseau_code': self.reseau.code if self.reseau else None,
            'periode_str': self.get_periode_str()
        })
        return data


class DonneesDistributionQuotidiennes(BaseModel):
    """Modèle pour les données quotidiennes de distribution"""
    __tablename__ = 'donnees_distribution_quotidiennes'
    
    # Relations
    rapport_id = Column(Integer, ForeignKey('rapports_distribution.id'), nullable=False)
    
    # Date
    date = Column(DateTime, nullable=False)
    
    # Énergie
    energie_distribuee = Column(Float)  # MWh
    pointe_journaliere = Column(Float)  # MW
    heure_pointe = Column(String(10))  # HH:MM
    
    # Qualité
    nombre_coupures = Column(Integer, default=0)
    duree_coupures = Column(Float, default=0.0)  # minutes
    clients_affectes = Column(Integer, default=0)
    
    # Conditions
    temperature_max = Column(Float)  # °C
    temperature_min = Column(Float)  # °C
    
    # Relations
    rapport = relationship("RapportDistribution", back_populates="donnees_quotidiennes")
    
    def __repr__(self):
        return f'<DonneesDistributionQuotidiennes {self.date.strftime("%d/%m/%Y") if self.date else "N/A"}>'


class DonneesDistributionMensuelles(BaseModel):
    """
    Modèle pour les données mensuelles de distribution
    Clientèle, énergie distribuée, revenus, qualité de service
    """
    __tablename__ = 'donnees_distribution_mensuelles'
    
    # Relations
    reseau_id = Column(Integer, ForeignKey('reseaux_distribution.id'), nullable=False)
    operateur_id = Column(Integer, ForeignKey('operateurs.id'), nullable=False)
    
    # Période
    annee = Column(Integer, nullable=False)
    mois = Column(Integer, nullable=False)
    
    # === CLIENTÈLE ===
    clients_ht_debut_mois = Column(Integer, default=0)
    clients_mt_debut_mois = Column(Integer, default=0)
    clients_bt_debut_mois = Column(Integer, default=0)
    
    nouveaux_raccordements_ht = Column(Integer, default=0)
    nouveaux_raccordements_mt = Column(Integer, default=0)
    nouveaux_raccordements_bt = Column(Integer, default=0)
    
    deconnexions_ht = Column(Integer, default=0)
    deconnexions_mt = Column(Integer, default=0)
    deconnexions_bt = Column(Integer, default=0)
    
    # === ÉNERGIE DISTRIBUÉE ===
    energie_distribuee_ht_mwh = Column(Float, default=0.0)
    energie_distribuee_mt_mwh = Column(Float, default=0.0)
    energie_distribuee_bt_mwh = Column(Float, default=0.0)
    
    energie_achetee_mwh = Column(Float, default=0.0)
    pertes_techniques_mwh = Column(Float, default=0.0)
    pertes_commerciales_mwh = Column(Float, default=0.0)
    
    # === REVENUS ET FACTURES ===
    revenus_ht_usd = Column(Float, default=0.0)
    revenus_mt_usd = Column(Float, default=0.0)
    revenus_bt_usd = Column(Float, default=0.0)
    
    factures_emises = Column(Integer, default=0)
    factures_payees = Column(Integer, default=0)
    impayes_usd = Column(Float, default=0.0)
    
    # === QUALITÉ DE SERVICE ===
    duree_coupures_heures = Column(Float, default=0.0)
    nombre_pannes = Column(Integer, default=0)
    temps_retablissement_moyen_heures = Column(Float, default=0.0)
    plaintes_clients = Column(Integer, default=0)
    
    # === MAINTENANCE ===
    cout_maintenance_usd = Column(Float, default=0.0)
    interventions_maintenance = Column(Integer, default=0)
    
    # === OBSERVATIONS ===
    observations = Column(Text)
    
    # Contrainte d'unicité : un seul enregistrement par réseau/mois/année
    __table_args__ = (
        db.UniqueConstraint('reseau_id', 'annee', 'mois', name='uq_donnees_distrib_periode'),
    )
    
    # Relations
    reseau = relationship("ReseauDistribution", backref="donnees_mensuelles")
    operateur = relationship("Operateur")
    
    @property
    def clients_ht_fin_mois(self):
        """Calcul automatique des clients HT en fin de mois"""
        return (self.clients_ht_debut_mois or 0) + (self.nouveaux_raccordements_ht or 0) - (self.deconnexions_ht or 0)
    
    @property
    def clients_mt_fin_mois(self):
        """Calcul automatique des clients MT en fin de mois"""
        return (self.clients_mt_debut_mois or 0) + (self.nouveaux_raccordements_mt or 0) - (self.deconnexions_mt or 0)
    
    @property
    def clients_bt_fin_mois(self):
        """Calcul automatique des clients BT en fin de mois"""
        return (self.clients_bt_debut_mois or 0) + (self.nouveaux_raccordements_bt or 0) - (self.deconnexions_bt or 0)
    
    @property
    def total_clients_fin_mois(self):
        """Total des clients en fin de mois"""
        return self.clients_ht_fin_mois + self.clients_mt_fin_mois + self.clients_bt_fin_mois
    
    @property
    def energie_totale_distribuee_mwh(self):
        """Énergie totale distribuée tous niveaux confondus"""
        return (self.energie_distribuee_ht_mwh or 0) + (self.energie_distribuee_mt_mwh or 0) + (self.energie_distribuee_bt_mwh or 0)
    
    @property
    def revenus_totaux_usd(self):
        """Revenus totaux tous niveaux confondus"""
        return (self.revenus_ht_usd or 0) + (self.revenus_mt_usd or 0) + (self.revenus_bt_usd or 0)
    
    @property
    def taux_paiement(self):
        """Taux de paiement des factures en %"""
        if not self.factures_emises or self.factures_emises == 0:
            return 0
        return round((self.factures_payees or 0) / self.factures_emises * 100, 2)
    
    @property
    def taux_pertes_techniques(self):
        """Taux de pertes techniques en %"""
        if not self.energie_achetee_mwh or self.energie_achetee_mwh == 0:
            return 0
        return round((self.pertes_techniques_mwh or 0) / self.energie_achetee_mwh * 100, 2)
    
    @property
    def taux_pertes_commerciales(self):
        """Taux de pertes commerciales en %"""
        if not self.energie_achetee_mwh or self.energie_achetee_mwh == 0:
            return 0
        return round((self.pertes_commerciales_mwh or 0) / self.energie_achetee_mwh * 100, 2)
    
    @property
    def taux_pertes_totales(self):
        """Taux de pertes totales en %"""
        return self.taux_pertes_techniques + self.taux_pertes_commerciales
    
    def get_periode_str(self):
        """Retourne la période sous forme de chaîne"""
        mois_noms = [
            '', 'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
            'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
        ]
        mois_nom = mois_noms[self.mois] if 1 <= self.mois <= 12 else str(self.mois)
        return f"{mois_nom} {self.annee}"
    
    def to_dict(self):
        """Conversion en dictionnaire pour l'API"""
        data = super().to_dict()
        data.update({
            'reseau_id': self.reseau_id,
            'operateur_id': self.operateur_id,
            'annee': self.annee,
            'mois': self.mois,
            'periode_str': self.get_periode_str(),
            
            # Clientèle
            'clients_ht_debut_mois': self.clients_ht_debut_mois,
            'clients_mt_debut_mois': self.clients_mt_debut_mois,
            'clients_bt_debut_mois': self.clients_bt_debut_mois,
            'clients_ht_fin_mois': self.clients_ht_fin_mois,
            'clients_mt_fin_mois': self.clients_mt_fin_mois,
            'clients_bt_fin_mois': self.clients_bt_fin_mois,
            'total_clients_fin_mois': self.total_clients_fin_mois,
            
            # Énergie
            'energie_totale_distribuee_mwh': self.energie_totale_distribuee_mwh,
            'energie_achetee_mwh': self.energie_achetee_mwh,
            'taux_pertes_totales': self.taux_pertes_totales,
            
            # Revenus
            'revenus_totaux_usd': self.revenus_totaux_usd,
            'taux_paiement': self.taux_paiement,
            
            # Qualité
            'duree_coupures_heures': self.duree_coupures_heures,
            'nombre_pannes': self.nombre_pannes,
            'plaintes_clients': self.plaintes_clients,
            
            # Relations
            'reseau_nom': self.reseau.nom if self.reseau else None,
            'operateur_nom': self.operateur.nom if self.operateur else None
        })
        return data
    
    def __repr__(self):
        return f'<DonneesDistributionMensuelles {self.get_periode_str()} - {self.reseau.nom if self.reseau else "N/A"}>'