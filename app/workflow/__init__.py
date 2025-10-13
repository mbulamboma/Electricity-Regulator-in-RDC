"""
Module de workflow pour la validation des rapports
"""
from flask import Blueprint

bp = Blueprint('workflow', __name__, url_prefix='/workflow')

from app.workflow import routes