"""
Module de gestion des opérateurs
"""
from flask import Blueprint

operateurs = Blueprint('operateurs', __name__, url_prefix='/operateurs')

from app.operateurs import routes