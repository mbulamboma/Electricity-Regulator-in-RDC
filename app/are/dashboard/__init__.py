"""
Initialisation du sous-module dashboard ARE
"""

from flask import Blueprint

dashboard_bp = Blueprint('are_dashboard', __name__, url_prefix='/are/dashboard')

from app.are.dashboard import routes