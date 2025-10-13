"""
Module de reporting pour la production hydroélectrique
"""
from flask import Blueprint

production_hydro = Blueprint('production_hydro', __name__, url_prefix='/production-hydro')

from app.production_hydro import routes