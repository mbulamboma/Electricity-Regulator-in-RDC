"""
Module de production solaire
"""
from flask import Blueprint

# Créer le blueprint
production_solaire = Blueprint('production_solaire', __name__, url_prefix='/production-solaire')

# Importer les routes après la création du blueprint pour éviter les imports circulaires
from app.production_solaire import routes