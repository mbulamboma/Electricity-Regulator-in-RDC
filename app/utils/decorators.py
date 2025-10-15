"""
Décorateurs pour la gestion des permissions et des rôles
"""
from functools import wraps
from flask import abort, flash, redirect, url_for, request
from flask_login import current_user


def login_required_with_message(f):
    """Décorateur personnalisé pour exiger la connexion avec message français"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def role_required(*roles):
    """Décorateur pour exiger un ou plusieurs rôles spécifiques"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
                return redirect(url_for('auth.login', next=request.url))
            
            if not current_user.is_active:
                flash('Votre compte a été désactivé. Contactez l\'administrateur.', 'danger')
                return redirect(url_for('auth.login'))
            
            if current_user.role not in roles:
                flash('Vous n\'avez pas les permissions nécessaires pour accéder à cette page.', 'danger')
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def super_admin_required(f):
    """Décorateur pour exiger le rôle super_admin"""
    return role_required('super_admin')(f)


def admin_required(f):
    """Décorateur pour exiger les rôles admin (super_admin ou admin_operateur)"""
    return role_required('super_admin', 'admin_operateur')(f)


def dashboard_are_required(f):
    """Décorateur pour l'accès au dashboard ARE (admins et contacts d'opérateurs)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
        # Vérifier si l'utilisateur peut accéder au dashboard ARE
        from app.utils.permissions import can_access_dashboard_are
        if not can_access_dashboard_are():
            flash('Vous n\'avez pas les permissions nécessaires pour accéder au dashboard ARE.', 'danger')
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function


def permission_required(permission):
    """Décorateur pour exiger une permission spécifique"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
                return redirect(url_for('auth.login', next=request.url))
            
            if not current_user.is_active:
                flash('Votre compte a été désactivé. Contactez l\'administrateur.', 'danger')
                return redirect(url_for('auth.login'))
            
            if not current_user.has_permission(permission):
                flash('Vous n\'avez pas les permissions nécessaires pour cette action.', 'danger')
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def operateur_access_required(f):
    """Décorateur pour vérifier l'accès aux données d'un opérateur"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
        if not current_user.is_active:
            flash('Votre compte a été désactivé. Contactez l\'administrateur.', 'danger')
            return redirect(url_for('auth.login'))
        
        # Récupérer l'ID de l'opérateur depuis les arguments de la route
        operateur_id = kwargs.get('operateur_id') or request.args.get('operateur_id')
        
        if operateur_id and not current_user.can_access_operateur(int(operateur_id)):
            flash('Vous n\'avez pas accès aux données de cet opérateur.', 'danger')
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function


def same_operateur_required(f):
    """Décorateur pour s'assurer que l'utilisateur appartient au même opérateur"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
        if current_user.is_super_admin():
            return f(*args, **kwargs)
        
        if not current_user.operateur_id:
            flash('Vous n\'êtes associé à aucun opérateur.', 'danger')
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function


def active_user_required(f):
    """Décorateur pour s'assurer que l'utilisateur est actif"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
        if not current_user.is_active:
            flash('Votre compte a été désactivé. Contactez l\'administrateur.', 'danger')
            return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    return decorated_function