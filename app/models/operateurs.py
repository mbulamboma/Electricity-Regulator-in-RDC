"""
Modèle Operateur pour la gestion des opérateurs électriques
"""
from app.extensions import db
from app.models.base import BaseModel
from werkzeug.security import generate_password_hash, check_password_hash


class Operateur(BaseModel):
    """Modèle pour les opérateurs d'électricité"""
    __tablename__ = 'operateurs'
    
    nom = db.Column(db.String(200), nullable=False, index=True)
    sigle = db.Column(db.String(50))
    type_operateur = db.Column(db.String(50))  # Production, Transport, Distribution
    adresse = db.Column(db.Text)
    ville = db.Column(db.String(100))
    province = db.Column(db.String(100))
    telephone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    site_web = db.Column(db.String(200))
    
    # Informations légales
    numero_licence = db.Column(db.String(100), unique=True)
    date_licence = db.Column(db.Date)
    statut_licence = db.Column(db.String(20), default='active')  # active, suspendue, expirée
    
    # Informations techniques
    capacite_installee = db.Column(db.Float)  # en MW
    zone_couverture = db.Column(db.Text)
    nombre_clients = db.Column(db.Integer)
    
    # Notes et observations
    observations = db.Column(db.Text)
    
    # Relations avec d'autres modèles (utilisation de chaînes pour éviter les imports circulaires)
    centrales_hydro = db.relationship("CentraleHydro", back_populates="operateur", lazy=True)
    centrales_thermique = db.relationship("CentraleThermique", back_populates="operateur", lazy=True)
    centrales_solaire = db.relationship("CentraleSolaire", back_populates="operateur", lazy=True)
    lignes_transport = db.relationship("LigneTransport", back_populates="operateur", lazy=True)
    postes_transport = db.relationship("PosteTransport", back_populates="operateur", lazy=True)
    reseaux_distribution = db.relationship("ReseauDistribution", back_populates="operateur", lazy=True)
    
    def to_dict(self):
        """Convertir en dictionnaire"""
        data = super().to_dict()
        data.update({
            'nom': self.nom,
            'sigle': self.sigle,
            'type_operateur': self.type_operateur,
            'adresse': self.adresse,
            'ville': self.ville,
            'province': self.province,
            'telephone': self.telephone,
            'email': self.email,
            'site_web': self.site_web,
            'numero_licence': self.numero_licence,
            'date_licence': self.date_licence.isoformat() if self.date_licence else None,
            'statut_licence': self.statut_licence,
            'capacite_installee': self.capacite_installee,
            'zone_couverture': self.zone_couverture,
            'nombre_clients': self.nombre_clients,
            'observations': self.observations
        })
        return data
    
    def __repr__(self):
        return f'<Operateur {self.nom}>'


class Contact(BaseModel):
    """Modèle pour les contacts des opérateurs"""
    __tablename__ = 'contacts'
    
    operateur_id = db.Column(db.Integer, db.ForeignKey('operateurs.id'), nullable=False)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    telephone = db.Column(db.String(20))
    fonction = db.Column(db.String(100))  # Directeur, Responsable technique, etc.
    
    # Champs pour l'authentification
    username = db.Column(db.String(80), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    last_login = db.Column(db.DateTime)
    
    # Relations
    operateur = db.relationship('Operateur', backref=db.backref('contacts', lazy=True, cascade='all, delete-orphan'))
    
    def set_password(self, password):
        """Définir le mot de passe (hashé)"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Vérifier le mot de passe"""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    def is_authenticated(self):
        """Vérifier si l'utilisateur est authentifié"""
        return True
    
    def is_anonymous(self):
        """Vérifier si l'utilisateur est anonyme"""
        return False
    
    def get_id(self):
        """Obtenir l'ID de l'utilisateur pour Flask-Login avec préfixe"""
        return f"contact_{self.id}"
    
    def to_dict(self):
        """Convertir en dictionnaire"""
        data = super().to_dict()
        data.update({
            'operateur_id': self.operateur_id,
            'nom': self.nom,
            'prenom': self.prenom,
            'email': self.email,
            'telephone': self.telephone,
            'fonction': self.fonction,
            'username': self.username,
            'is_active': self.is_active,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'nom_complet': f"{self.prenom} {self.nom}"
        })
        return data
    
    def __repr__(self):
        return f'<Contact {self.prenom} {self.nom}>'
