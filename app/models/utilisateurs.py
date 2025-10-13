"""
Modèle User pour l'authentification
"""
from datetime import datetime
from flask_login import UserMixin
from app.extensions import db, bcrypt
from app.models.base import BaseModel


class User(UserMixin, BaseModel):
    """Modèle utilisateur pour l'authentification"""
    __tablename__ = 'users'
    
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    nom = db.Column(db.String(100))
    prenom = db.Column(db.String(100))
    role = db.Column(db.Enum('super_admin', 'admin_operateur', 'utilisateur_operateur'), 
                    default='utilisateur_operateur', nullable=False)
    operateur_id = db.Column(db.Integer, db.ForeignKey('operateurs.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    telephone = db.Column(db.String(20))
    derniere_connexion = db.Column(db.DateTime)
    
    # Relation avec l'opérateur
    operateur = db.relationship('Operateur', backref='users', lazy=True)
    
    def set_password(self, password):
        """Hasher et enregistrer le mot de passe"""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        """Vérifier le mot de passe"""
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def is_super_admin(self):
        """Vérifier si l'utilisateur est super admin"""
        return self.role == 'super_admin'
    
    def is_admin_operateur(self):
        """Vérifier si l'utilisateur est admin d'un opérateur"""
        return self.role == 'admin_operateur'
    
    def is_admin(self):
        """Vérifier si l'utilisateur est admin (super admin ou admin opérateur)"""
        return self.role in ['super_admin', 'admin_operateur']
    
    def is_utilisateur_operateur(self):
        """Vérifier si l'utilisateur est utilisateur d'un opérateur"""
        return self.role == 'utilisateur_operateur'
    
    @property
    def nom_complet(self):
        """Obtenir le nom complet de l'utilisateur"""
        if self.nom and self.prenom:
            return f"{self.prenom} {self.nom}"
        elif self.nom:
            return self.nom
        elif self.prenom:
            return self.prenom
        else:
            return self.username
    
    def has_permission(self, permission):
        """Vérifier les permissions selon le rôle"""
        permissions = {
            'super_admin': ['create_operateur', 'edit_operateur', 'delete_operateur', 
                           'create_user', 'edit_user', 'delete_user', 'view_all_reports'],
            'admin_operateur': ['edit_own_operateur', 'create_user_operateur', 
                               'edit_user_operateur', 'view_own_reports', 'create_reports'],
            'utilisateur_operateur': ['view_own_reports', 'create_reports', 'edit_own_reports']
        }
        return permission in permissions.get(self.role, [])
    
    def can_access_operateur(self, operateur_id):
        """Vérifier si l'utilisateur peut accéder aux données d'un opérateur"""
        if self.is_super_admin():
            return True
        return self.operateur_id == operateur_id
    
    def get_accessible_operateurs(self):
        """Obtenir la liste des opérateurs accessibles"""
        if self.is_super_admin():
            from app.models.operateurs import Operateur
            return Operateur.query.filter_by(actif=True).all()
        elif self.operateur_id:
            return [self.operateur] if self.operateur else []
        return []
    
    def update_last_login(self):
        """Mettre à jour la dernière connexion"""
        self.derniere_connexion = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """Convertir en dictionnaire"""
        data = super().to_dict()
        data.update({
            'username': self.username,
            'email': self.email,
            'nom': self.nom,
            'prenom': self.prenom,
            'role': self.role,
            'operateur_id': self.operateur_id,
            'is_active': self.is_active,
            'telephone': self.telephone,
            'derniere_connexion': self.derniere_connexion.isoformat() if self.derniere_connexion else None,
            'operateur_nom': self.operateur.nom if self.operateur else None
        })
        return data
    
    def __repr__(self):
        return f'<User {self.username} ({self.role})>'
