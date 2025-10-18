"""
Module de reporting pour la production hydroélectrique
"""
from flask import Blueprint

production_hydro = Blueprint('production_hydro', __name__, url_prefix='/production-hydro')

# Importer tous les modules de routes
from app.production_hydro import routes_rapports
from app.production_hydro import routes_centrales
from app.production_hydro import routes_equipements
from app.production_hydro import routes_api
from app.production_hydro import routes_export