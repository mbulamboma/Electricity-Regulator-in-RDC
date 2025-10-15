"""
Blueprint pour la collecte de données mensuelles des opérateurs
Remplace les fake data par des vraies soumissions
"""
from flask import Blueprint

collecte_bp = Blueprint('collecte', __name__, url_prefix='/collecte')