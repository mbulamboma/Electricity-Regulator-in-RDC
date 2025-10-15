"""
Modèles pour les statistiques complètes ARE
"""
from datetime import datetime
from enum import Enum
from app.extensions import db
from app.models.base import BaseModel


class TypeProjet(Enum):
    """Types de projets traités par l'ARE"""
    PRODUCTION_HYDRO = "production_hydro"
    PRODUCTION_THERMIQUE = "production_thermique"
    PRODUCTION_SOLAIRE = "production_solaire"
    TRANSPORT = "transport"
    DISTRIBUTION = "distribution"
    MINI_GRID = "mini_grid"


class StatutProjet(Enum):
    """Statuts des projets ARE"""
    AVIS_FAVORABLE = "avis_favorable"
    AVIS_DEFAVORABLE = "avis_defavorable"
    EN_ETUDE = "en_etude"
    APPROUVE = "approuve"
    REJETE = "rejete"


class TypeTension(Enum):
    """Types de tension électrique"""
    HT = "haute_tension"      # > 50 kV
    MT = "moyenne_tension"    # 1-50 kV
    BT = "basse_tension"      # < 1 kV


class PortfolioProjet(BaseModel):
    """Portfolio des projets traités par l'ARE depuis sa création"""
    __tablename__ = 'portfolio_projet'
    
    nom_projet = db.Column(db.String(200), nullable=False)
    type_projet = db.Column(db.Enum(TypeProjet), nullable=False)
    operateur_id = db.Column(db.Integer, db.ForeignKey('operateurs.id'), nullable=False)
    capacite_mw = db.Column(db.Float, nullable=False)  # Capacité en MW
    investissement_usd = db.Column(db.Float)  # Investissement en millions USD
    date_depot_demande = db.Column(db.Date, nullable=False)
    date_avis = db.Column(db.Date)
    statut = db.Column(db.Enum(StatutProjet), nullable=False)
    annee_avis = db.Column(db.Integer)  # Année de l'avis favorable
    province = db.Column(db.String(50))
    localisation = db.Column(db.String(200))
    
    # Relations
    operateur = db.relationship('Operateur', backref='projets_are', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'nom_projet': self.nom_projet,
            'type_projet': self.type_projet.value,
            'operateur': self.operateur.nom if self.operateur else None,
            'capacite_mw': self.capacite_mw,
            'investissement_usd': self.investissement_usd,
            'date_depot_demande': self.date_depot_demande.isoformat() if self.date_depot_demande else None,
            'date_avis': self.date_avis.isoformat() if self.date_avis else None,
            'statut': self.statut.value,
            'annee_avis': self.annee_avis,
            'province': self.province,
            'localisation': self.localisation
        }


class CapaciteInstallee(BaseModel):
    """Evolution de la capacité installée par source d'énergie"""
    __tablename__ = 'capacite_installee'
    
    annee = db.Column(db.Integer, nullable=False)
    type_source = db.Column(db.Enum(TypeProjet), nullable=False)
    operateur_id = db.Column(db.Integer, db.ForeignKey('operateurs.id'), nullable=True)
    capacite_installee_mw = db.Column(db.Float, nullable=False)  # MW installés
    capacite_disponible_mw = db.Column(db.Float)  # MW disponibles (peut être < installé)
    production_annuelle_gwh = db.Column(db.Float)  # Production annuelle en GWh
    facteur_charge = db.Column(db.Float)  # Facteur de charge %
    province = db.Column(db.String(50))
    
    # Relations
    operateur = db.relationship('Operateur', backref='capacites_installees', lazy=True)
    
    # Index pour les requêtes fréquentes
    __table_args__ = (
        db.Index('idx_capacite_annee_source', 'annee', 'type_source'),
        db.Index('idx_capacite_operateur', 'operateur_id'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'annee': self.annee,
            'type_source': self.type_source.value,
            'operateur': self.operateur.nom if self.operateur else 'National',
            'capacite_installee_mw': self.capacite_installee_mw,
            'capacite_disponible_mw': self.capacite_disponible_mw,
            'production_annuelle_gwh': self.production_annuelle_gwh,
            'facteur_charge': self.facteur_charge,
            'province': self.province
        }


class ProductionSolaire(BaseModel):
    """Données spécifiques à la production solaire (domestique et industrielle)"""
    __tablename__ = 'production_solaire_stats'
    
    annee = db.Column(db.Integer, nullable=False)
    type_installation = db.Column(db.String(50), nullable=False)  # 'domestique', 'industrielle', 'mini_grid'
    operateur_id = db.Column(db.Integer, db.ForeignKey('operateurs.id'), nullable=True)
    puissance_installee_mw = db.Column(db.Float, nullable=False)
    nombre_installations = db.Column(db.Integer)
    production_annuelle_gwh = db.Column(db.Float)
    province = db.Column(db.String(50))
    
    # Relations
    operateur = db.relationship('Operateur', backref='productions_solaires', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'annee': self.annee,
            'type_installation': self.type_installation,
            'operateur': self.operateur.nom if self.operateur else 'National',
            'puissance_installee_mw': self.puissance_installee_mw,
            'nombre_installations': self.nombre_installations,
            'production_annuelle_gwh': self.production_annuelle_gwh,
            'province': self.province
        }


class ClienteleElectricite(BaseModel):
    """Données sur la clientèle électrique en RDC"""
    __tablename__ = 'clientele_electricite'
    
    annee = db.Column(db.Integer, nullable=False)
    operateur_id = db.Column(db.Integer, db.ForeignKey('operateurs.id'), nullable=True)
    province = db.Column(db.String(50))
    
    # Clients par type de tension
    clients_ht = db.Column(db.Integer, default=0)  # Haute tension
    clients_mt = db.Column(db.Integer, default=0)  # Moyenne tension
    clients_bt = db.Column(db.Integer, default=0)  # Basse tension
    total_clients = db.Column(db.Integer, nullable=False)
    
    # Clients facturés
    clients_factures = db.Column(db.Integer, default=0)
    menages_factures = db.Column(db.Integer, default=0)
    menages_desservis = db.Column(db.Integer, default=0)
    
    # Taux de couverture et accès
    taux_couverture_geographique = db.Column(db.Float)  # %
    taux_electrification = db.Column(db.Float)  # %
    taux_acces_electricite = db.Column(db.Float)  # %
    
    # Relations
    operateur = db.relationship('Operateur', backref='clienteles', lazy=True)
    
    # Index pour les requêtes fréquentes
    __table_args__ = (
        db.Index('idx_clientele_annee_operateur', 'annee', 'operateur_id'),
        db.Index('idx_clientele_province', 'province'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'annee': self.annee,
            'operateur': self.operateur.nom if self.operateur else 'National',
            'province': self.province,
            'clients_ht': self.clients_ht,
            'clients_mt': self.clients_mt,
            'clients_bt': self.clients_bt,
            'total_clients': self.total_clients,
            'clients_factures': self.clients_factures,
            'menages_factures': self.menages_factures,
            'menages_desservis': self.menages_desservis,
            'taux_couverture_geographique': self.taux_couverture_geographique,
            'taux_electrification': self.taux_electrification,
            'taux_acces_electricite': self.taux_acces_electricite
        }


class StatistiqueNationale(BaseModel):
    """Statistiques agrégées au niveau national"""
    __tablename__ = 'statistique_nationale'
    
    annee = db.Column(db.Integer, nullable=False, unique=True)
    
    # Capacités totales
    capacite_totale_installee_mw = db.Column(db.Float, default=0)
    capacite_totale_disponible_mw = db.Column(db.Float, default=0)
    production_totale_annuelle_gwh = db.Column(db.Float, default=0)
    
    # Répartition par source
    capacite_hydro_mw = db.Column(db.Float, default=0)
    capacite_thermique_mw = db.Column(db.Float, default=0)
    capacite_solaire_mw = db.Column(db.Float, default=0)
    
    # Production par source
    production_hydro_gwh = db.Column(db.Float, default=0)
    production_thermique_gwh = db.Column(db.Float, default=0)
    production_solaire_gwh = db.Column(db.Float, default=0)
    
    # Clientèle nationale
    total_clients_nationaux = db.Column(db.Integer, default=0)
    clients_ht_nationaux = db.Column(db.Integer, default=0)
    clients_mt_nationaux = db.Column(db.Integer, default=0)
    clients_bt_nationaux = db.Column(db.Integer, default=0)
    
    # Taux nationaux
    taux_acces_national = db.Column(db.Float, default=0)  # %
    taux_electrification_national = db.Column(db.Float, default=0)  # %
    taux_couverture_national = db.Column(db.Float, default=0)  # %
    
    # Métadonnées
    nombre_operateurs_actifs = db.Column(db.Integer, default=0)
    date_calcul = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'annee': self.annee,
            'capacite_totale_installee_mw': self.capacite_totale_installee_mw,
            'capacite_totale_disponible_mw': self.capacite_totale_disponible_mw,
            'production_totale_annuelle_gwh': self.production_totale_annuelle_gwh,
            'capacite_hydro_mw': self.capacite_hydro_mw,
            'capacite_thermique_mw': self.capacite_thermique_mw,
            'capacite_solaire_mw': self.capacite_solaire_mw,
            'production_hydro_gwh': self.production_hydro_gwh,
            'production_thermique_gwh': self.production_thermique_gwh,
            'production_solaire_gwh': self.production_solaire_gwh,
            'total_clients_nationaux': self.total_clients_nationaux,
            'clients_ht_nationaux': self.clients_ht_nationaux,
            'clients_mt_nationaux': self.clients_mt_nationaux,
            'clients_bt_nationaux': self.clients_bt_nationaux,
            'taux_acces_national': self.taux_acces_national,
            'taux_electrification_national': self.taux_electrification_national,
            'taux_couverture_national': self.taux_couverture_national,
            'nombre_operateurs_actifs': self.nombre_operateurs_actifs,
            'date_calcul': self.date_calcul.isoformat() if self.date_calcul else None
        }
