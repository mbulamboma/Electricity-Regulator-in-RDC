"""
Fonctions utilitaires générales
"""
from datetime import datetime
from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user


def format_date(date, format='%d/%m/%Y'):
    """Formater une date"""
    if isinstance(date, datetime):
        return date.strftime(format)
    return date


def format_datetime(dt, format='%d/%m/%Y %H:%M'):
    """Formater une date et heure"""
    if isinstance(dt, datetime):
        return dt.strftime(format)
    return dt


def admin_required(f):
    """Décorateur pour restreindre l'accès aux administrateurs"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
            return redirect(url_for('auth.login'))
        
        if not current_user.is_admin():
            flash('Accès refusé. Droits administrateur requis.', 'danger')
            return redirect(url_for('main.index'))
        
        return f(*args, **kwargs)
    return decorated_function


def format_number(number, decimals=2):
    """Formater un nombre avec séparateurs de milliers"""
    if number is None:
        return '0'
    return '{:,.{prec}f}'.format(number, prec=decimals).replace(',', ' ')


def get_current_year():
    """Obtenir l'année actuelle"""
    return datetime.now().year


def safe_int_coerce(value):
    """
    Coercition sécurisée pour les SelectField
    Gère les chaînes vides et les valeurs None
    """
    if value is None or value == '' or value == 'None':
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def flash_errors(form):
    """Afficher les erreurs de formulaire"""
    for field, errors in form.errors.items():
        for error in errors:
            flash(f"Erreur dans {getattr(form, field).label.text}: {error}", 'danger')
