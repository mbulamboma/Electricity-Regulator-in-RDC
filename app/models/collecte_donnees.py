"""
Modèles pour la collecte de données mensuelles des opérateurs
Collecte uniquement les données qui ne peuvent pas être calculées automatiquement
"""
from datetime import datetime, date
from enum import Enum
from app.extensions import db
from app.models.base import BaseModel


class TypeSource(Enum):
    """Types de sources d'énergie"""
    HYDRO = "hydro"
    THERMIQUE = "thermique"
    SOLAIRE = "solaire"


class TypeTension(Enum):
    """Types de tension"""
    HAUTE_TENSION = "HT"
    MOYENNE_TENSION = "MT" 
    BASSE_TENSION = "BT"


class StatutCollecte(Enum):
    """Statuts de collecte des données"""
    BROUILLON = "brouillon"
    SOUMIS = "soumis"
    VALIDE = "valide"
    REJETE = "rejete"


class CollecteDonneesMensuelles(BaseModel):
    """
    Collecte des données mensuelles qui ne peuvent pas être calculées automatiquement
    à partir des rapports existants (production, transport, distribution)
    """
    __tablename__ = 'collecte_donnees_mensuelles'
    
    # Identification
    operateur_id = db.Column(db.Integer, db.ForeignKey('operateurs.id'), nullable=False)
    mois = db.Column(db.Integer, nullable=False)  # 1-12
    annee = db.Column(db.Integer, nullable=False)
    statut = db.Column(db.Enum(StatutCollecte), default=StatutCollecte.BROUILLON)
    
    # === DONNÉES FINANCIÈRES (non calculables automatiquement) ===
    investissements_mois_millions_usd = db.Column(db.Float)  # Nouveaux investissements du mois
    revenus_ventes_electricite_millions_usd = db.Column(db.Float)  # Revenus des ventes
    cout_exploitation_millions_usd = db.Column(db.Float)  # Coûts d'exploitation
    cout_maintenance_millions_usd = db.Column(db.Float)  # Coûts de maintenance
    
    # === DONNÉES CLIENTÈLE (complémentaires aux données calculables) ===
    nouveaux_clients_ht_mois = db.Column(db.Integer, default=0)  # Nouveaux clients HT ce mois
    nouveaux_clients_mt_mois = db.Column(db.Integer, default=0)  # Nouveaux clients MT ce mois
    nouveaux_clients_bt_mois = db.Column(db.Integer, default=0)  # Nouveaux clients BT ce mois
    clients_deconnectes_ht_mois = db.Column(db.Integer, default=0)  # Clients déconnectés HT
    clients_deconnectes_mt_mois = db.Column(db.Integer, default=0)  # Clients déconnectés MT
    clients_deconnectes_bt_mois = db.Column(db.Integer, default=0)  # Clients déconnectés BT
    
    # === DONNÉES GÉOGRAPHIQUES ===
    nouvelles_localites_desservies = db.Column(db.Integer, default=0)  # Nouvelles localités connectées
    longueur_nouveaux_reseaux_km = db.Column(db.Float, default=0)  # Nouveaux km de réseau
    population_nouvelle_couverte = db.Column(db.Integer, default=0)  # Nouvelle population couverte
    
    # === DONNÉES ENVIRONNEMENTALES ===
    emissions_co2_tonnes = db.Column(db.Float)  # Émissions CO2 du mois (pour thermique)
    consommation_eau_m3 = db.Column(db.Float)  # Consommation d'eau (pour hydro/thermique)
    
    # === INCIDENTS ET QUALITÉ ===
    nombre_pannes_majeures = db.Column(db.Integer, default=0)  # Pannes > 4h
    duree_totale_pannes_heures = db.Column(db.Float, default=0)  # Durée totale des pannes
    nombre_plaintes_clients = db.Column(db.Integer, default=0)  # Plaintes clients
    
    # === MÉTADONNÉES ===
    commentaires = db.Column(db.Text)  # Commentaires sur les données du mois
    soumis_par_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    date_soumission = db.Column(db.DateTime)
    valide_par_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    date_validation = db.Column(db.DateTime)
    
    # Relations
    operateur = db.relationship('Operateur', backref='collectes_mensuelles', lazy=True)
    soumis_par = db.relationship('User', foreign_keys=[soumis_par_user_id], backref='collectes_soumises', lazy=True)
    valide_par = db.relationship('User', foreign_keys=[valide_par_user_id], backref='collectes_validees', lazy=True)
    
    # Contrainte unique : un seul enregistrement par opérateur/mois/année
    __table_args__ = (
        db.UniqueConstraint('operateur_id', 'mois', 'annee', name='uq_collecte_operateur_mois_annee'),
        db.Index('idx_collecte_periode', 'annee', 'mois'),
        db.Index('idx_collecte_statut', 'statut'),
    )
    
    def __repr__(self):
        return f'<CollecteDonneesMensuelles {self.operateur.nom if self.operateur else "N/A"} - {self.mois:02d}/{self.annee}>'
    
    @property
    def periode_str(self):
        """Retourne la période sous forme de chaîne"""
        mois_noms = {
            1: 'Janvier', 2: 'Février', 3: 'Mars', 4: 'Avril',
            5: 'Mai', 6: 'Juin', 7: 'Juillet', 8: 'Août',
            9: 'Septembre', 10: 'Octobre', 11: 'Novembre', 12: 'Décembre'
        }
        return f"{mois_noms.get(self.mois, 'Mois')} {self.annee}"
    
    @property
    def peut_etre_modifie(self):
        """Vérifie si la collecte peut être modifiée"""
        return self.statut in [StatutCollecte.BROUILLON, StatutCollecte.REJETE]
    
    @property
    def total_nouveaux_clients(self):
        """Total des nouveaux clients ce mois"""
        return (self.nouveaux_clients_ht_mois or 0) + \
               (self.nouveaux_clients_mt_mois or 0) + \
               (self.nouveaux_clients_bt_mois or 0)
    
    @property
    def total_clients_deconnectes(self):
        """Total des clients déconnectés ce mois"""
        return (self.clients_deconnectes_ht_mois or 0) + \
               (self.clients_deconnectes_mt_mois or 0) + \
               (self.clients_deconnectes_bt_mois or 0)
    
    def to_dict(self):
        return {
            'id': self.id,
            'operateur': self.operateur.nom if self.operateur else None,
            'periode': self.periode_str,
            'mois': self.mois,
            'annee': self.annee,
            'statut': self.statut.value if self.statut else None,
            
            # Financier
            'investissements_millions_usd': self.investissements_mois_millions_usd,
            'revenus_millions_usd': self.revenus_ventes_electricite_millions_usd,
            'cout_exploitation_millions_usd': self.cout_exploitation_millions_usd,
            'cout_maintenance_millions_usd': self.cout_maintenance_millions_usd,
            
            # Clientèle
            'nouveaux_clients_total': self.total_nouveaux_clients,
            'clients_deconnectes_total': self.total_clients_deconnectes,
            
            # Géographique
            'nouvelles_localites': self.nouvelles_localites_desservies,
            'nouveaux_reseaux_km': self.longueur_nouveaux_reseaux_km,
            'nouvelle_population': self.population_nouvelle_couverte,
            
            # Environnemental
            'emissions_co2_tonnes': self.emissions_co2_tonnes,
            'consommation_eau_m3': self.consommation_eau_m3,
            
            # Qualité
            'pannes_majeures': self.nombre_pannes_majeures,
            'duree_pannes_heures': self.duree_totale_pannes_heures,
            'plaintes_clients': self.nombre_plaintes_clients,
            
            'commentaires': self.commentaires,
            'soumis_par': self.soumis_par.username if self.soumis_par else None,
            'date_soumission': self.date_soumission.isoformat() if self.date_soumission else None,
            'peut_etre_modifie': self.peut_etre_modifie
        }


class CollecteProjetNouveau(BaseModel):
    """
    Collecte des nouveaux projets soumis à l'ARE pour avis
    Données non calculables car dépendent de projets futurs
    """
    __tablename__ = 'collecte_projet_nouveau'
    
    # Identification du projet
    nom_projet = db.Column(db.String(200), nullable=False)
    operateur_id = db.Column(db.Integer, db.ForeignKey('operateurs.id'), nullable=False)
    type_projet = db.Column(db.Enum(TypeSource), nullable=False)
    
    # Caractéristiques techniques
    capacite_prevue_mw = db.Column(db.Float, nullable=False)
    investissement_prevu_millions_usd = db.Column(db.Float)
    localisation = db.Column(db.String(200), nullable=False)
    province = db.Column(db.String(50), nullable=False)
    
    # Planning
    date_depot_are = db.Column(db.Date, nullable=False)
    date_prevue_debut_travaux = db.Column(db.Date)
    date_prevue_mise_service = db.Column(db.Date)
    duree_prevue_construction_mois = db.Column(db.Integer)
    
    # Statut administratif
    statut_are = db.Column(db.String(50), default='en_attente')  # en_attente, avis_favorable, avis_defavorable
    date_avis_are = db.Column(db.Date)
    reference_dossier_are = db.Column(db.String(100))
    
    # Impact prévu
    emplois_crees_prevus = db.Column(db.Integer)
    population_beneficiaire_prevue = db.Column(db.Integer)
    nombre_clients_supplementaires_prevus = db.Column(db.Integer)
    
    # Documents et suivi
    documents_joints = db.Column(db.Text)  # Liste des documents fournis
    observations_are = db.Column(db.Text)  # Observations de l'ARE
    
    # Métadonnées
    soumis_par_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date_soumission = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    operateur = db.relationship('Operateur', backref='nouveaux_projets', lazy=True)
    soumis_par = db.relationship('User', backref='projets_soumis', lazy=True)
    
    def __repr__(self):
        return f'<CollecteProjetNouveau {self.nom_projet} - {self.operateur.nom if self.operateur else "N/A"}>'
    
    @property
    def statut_display(self):
        """Affichage du statut"""
        statuts = {
            'en_attente': 'En attente d\'avis ARE',
            'avis_favorable': 'Avis favorable ARE',
            'avis_defavorable': 'Avis défavorable ARE'
        }
        return statuts.get(self.statut_are, self.statut_are)
    
    def to_dict(self):
        return {
            'id': self.id,
            'nom_projet': self.nom_projet,
            'operateur': self.operateur.nom if self.operateur else None,
            'type_projet': self.type_projet.value if self.type_projet else None,
            'capacite_prevue_mw': self.capacite_prevue_mw,
            'investissement_prevu_millions_usd': self.investissement_prevu_millions_usd,
            'localisation': self.localisation,
            'province': self.province,
            'date_depot_are': self.date_depot_are.isoformat() if self.date_depot_are else None,
            'statut_are': self.statut_are,
            'statut_display': self.statut_display,
            'soumis_par': self.soumis_par.username if self.soumis_par else None,
            'date_soumission': self.date_soumission.isoformat() if self.date_soumission else None
        }
