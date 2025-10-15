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


def can_access_dashboard_are():
    """Vérifier si l'utilisateur peut accéder au dashboard ARE"""
    # Contact d'opérateur peut accéder au dashboard
    if hasattr(current_user, 'operateur_id') and current_user.operateur_id:
        return True
    # User avec rôle admin peut accéder
    if hasattr(current_user, 'is_admin') and current_user.is_admin():
        return True
    return False


def get_dashboard_are_operateur_filter():
    """Obtenir le filtre opérateur pour le dashboard ARE selon les permissions"""
    # Super admin peut voir tous les opérateurs (pas de filtre)
    if hasattr(current_user, 'is_super_admin') and current_user.is_super_admin():
        return None
    
    # Contact ou utilisateur d'opérateur ne peut voir que son opérateur
    if hasattr(current_user, 'operateur_id') and current_user.operateur_id:
        return current_user.operateur_id
    
    # Par défaut, aucun accès
    return -1  # Filtre qui ne retournera aucun résultat


def get_dashboard_are_operateurs_choices():
    """Obtenir les choix d'opérateurs pour les filtres du dashboard ARE"""
    from app.models.operateurs import Operateur
    
    # Super admin peut choisir parmi tous les opérateurs
    if hasattr(current_user, 'is_super_admin') and current_user.is_super_admin():
        operateurs = Operateur.query.filter_by(actif=True).all()
        choices = [('', 'Tous les opérateurs')] + [(op.id, op.nom) for op in operateurs]
        return choices
    
    # Contact ou utilisateur d'opérateur ne voit que son opérateur
    if hasattr(current_user, 'operateur_id') and current_user.operateur_id and current_user.operateur:
        return [(current_user.operateur_id, current_user.operateur.nom)]
    
    return []


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