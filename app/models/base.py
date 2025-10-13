"""
Modèle de base avec méthodes communes
"""
from datetime import datetime
from app.extensions import db


class BaseModel(db.Model):
    """Classe de base pour tous les modèles"""
    __abstract__ = True
    
    id = db.Column(db.Integer, primary_key=True)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    date_modification = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    actif = db.Column(db.Boolean, default=True, nullable=False)
    
    def save(self):
        """Enregistrer l'objet dans la base de données"""
        db.session.add(self)
        db.session.commit()
        return self
    
    def delete(self):
        """Supprimer l'objet de la base de données"""
        db.session.delete(self)
        db.session.commit()
    
    def update(self, **kwargs):
        """Mettre à jour les attributs de l'objet"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.date_modification = datetime.utcnow()
        db.session.commit()
        return self
    
    def soft_delete(self):
        """Désactiver l'objet sans le supprimer"""
        self.actif = False
        db.session.commit()
    
    def to_dict(self):
        """Convertir l'objet en dictionnaire"""
        return {
            'id': self.id,
            'date_creation': self.date_creation.isoformat() if self.date_creation else None,
            'date_modification': self.date_modification.isoformat() if self.date_modification else None,
            'actif': self.actif
        }
    
    def __repr__(self):
        return f'<{self.__class__.__name__} {self.id}>'
