"""
Utilitaires pour la gestion des permissions des rapports
"""
from flask_login import current_user
from app.models.operateurs import Operateur


def get_accessible_operateurs():
    """Obtenir la liste des opérateurs accessibles selon les permissions de l'utilisateur"""
    if current_user.is_admin():
        # Super admin peut voir tous les opérateurs
        return Operateur.query.filter_by(actif=True).all()
    elif current_user.operateur_id:
        # Utilisateur d'opérateur ne peut voir que son opérateur
        return [current_user.operateur] if current_user.operateur else []
    else:
        return []


def can_access_operateur(operateur_id):
    """Vérifier si l'utilisateur peut accéder aux données d'un opérateur spécifique"""
    if current_user.is_admin():
        return True
    return current_user.operateur_id == operateur_id


def filter_query_by_operateur(query, operateur_field='operateur_id'):
    """Filtrer une requête selon les permissions de l'utilisateur"""
    if current_user.is_admin():
        return query
    elif current_user.operateur_id:
        return query.filter(getattr(query.column_descriptions[0]['type'], operateur_field) == current_user.operateur_id)
    else:
        # Si pas d'opérateur associé, ne retourner aucun résultat
        return query.filter(False)


def can_access_reseau(reseau):
    """Vérifier si l'utilisateur peut accéder à un réseau de distribution"""
    if current_user.is_admin():
        return True
    return current_user.operateur_id == reseau.operateur_id


def can_access_poste(poste):
    """Vérifier si l'utilisateur peut accéder à un poste de distribution"""
    if current_user.is_admin():
        return True
    return current_user.operateur_id == poste.reseau.operateur_id


def can_access_feeder(feeder):
    """Vérifier si l'utilisateur peut accéder à un feeder de distribution"""
    if current_user.is_admin():
        return True
    return current_user.operateur_id == feeder.reseau.operateur_id


def get_operateur_choices():
    """Obtenir les choix d'opérateurs pour les formulaires SelectField"""
    operateurs = get_accessible_operateurs()
    if current_user.is_admin():
        return [('', 'Sélectionner un opérateur')] + [(op.id, op.nom) for op in operateurs]
    else:
        return [(op.id, op.nom) for op in operateurs]


def get_default_operateur_id():
    """Obtenir l'ID d'opérateur par défaut pour les nouveaux enregistrements"""
    if not current_user.is_admin() and current_user.operateur_id:
        return current_user.operateur_id
    return None