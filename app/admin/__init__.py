"""
Module d'administration pour super administrateur
"""
from flask import Blueprint

admin = Blueprint('admin', __name__, url_prefix='/admin')

from . import routes