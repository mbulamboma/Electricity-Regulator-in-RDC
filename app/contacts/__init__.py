"""
Module d'authentification des contacts
"""
from flask import Blueprint

bp = Blueprint('contacts', __name__, url_prefix='/contacts')

from app.contacts import routes