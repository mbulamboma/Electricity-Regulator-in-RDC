"""
Fonctions utilitaires pour le module production thermique
"""
from flask_login import current_user
from app.models.production_thermique import CentraleThermique


def get_accessible_centrales_thermique():
    """Obtenir les centrales thermiques accessibles selon les permissions"""
    if current_user.is_admin():
        return CentraleThermique.query.filter_by(actif=True).all()
    elif current_user.operateur:
        return CentraleThermique.query.filter_by(
            operateur_id=current_user.operateur.id,
            actif=True
        ).all()
    return []