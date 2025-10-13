"""
Module ARE - Autorité de Régulation de l'Électricité
Dashboard stratégique et indicateurs
"""

from flask import Blueprint

bp = Blueprint('are', __name__, url_prefix='/are')

from app.are import routes