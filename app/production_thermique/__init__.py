"""
Module de production thermique
"""
from flask import Blueprint

# Créer le blueprint
production_thermique = Blueprint('production_thermique', __name__, url_prefix='/production-thermique')

# Importer les routes après la création du blueprint pour éviter les imports circulaires
from app.production_thermique import routes_main, routes_centrales, routes_api