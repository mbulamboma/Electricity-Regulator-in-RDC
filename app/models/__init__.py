"""
Package des modèles
"""
from app.models.base import BaseModel
from app.models.utilisateurs import User
from app.models.operateurs import Operateur, Contact

# Import des modèles de production
from app.models.production_hydro import CentraleHydro, RapportHydro, GroupeProduction, TransformateurRapport, DonneesMensuelles
from app.models.production_thermique import CentraleThermique, RapportThermique, GroupeProductionThermique
from app.models.production_solaire import CentraleSolaire, RapportSolaire, DonneesSolaireQuotidiennes

# Import des modèles de transport
from app.models.transport import LigneTransport, PosteTransport, TransformateurTransport, RapportTransport

# Import des modèles de distribution
from app.models.distribution import (
    ReseauDistribution, PosteDistribution, TransformateurDistribution, 
    FeederDistribution, RapportDistribution
)

# Import des modèles ARE (Dashboard stratégique)
from app.models.dashboard_are import (
    KPIStrategic, IndicateurSectoriel, AlerteRegulateur, 
    DonneesProvince, RapportAnnuel
)

# Import des modèles de notifications
from app.models.notifications import (
    Notification, MessageInterne, TemplateNotification, PreferenceNotification,
    TypeNotification
)

# Import des modèles de workflow
from app.models.workflow import (
    Workflow, ValidationRapport, HistoriqueValidation, ValidateurDesigne,
    TypeRapport, StatutWorkflow, TypeAction
)

__all__ = [
    'BaseModel', 'User', 'Operateur', 'Contact',
    'CentraleHydro', 'RapportHydro', 'GroupeProduction', 'TransformateurRapport', 'DonneesMensuelles',
    'CentraleThermique', 'RapportThermique', 'GroupeProductionThermique',
    'CentraleSolaire', 'RapportSolaire', 'DonneesSolaireQuotidiennes',
    'LigneTransport', 'PosteTransport', 'TransformateurTransport', 'RapportTransport',
    'ReseauDistribution', 'PosteDistribution', 'TransformateurDistribution', 
    'FeederDistribution', 'RapportDistribution',
    'Notification', 'MessageInterne', 'TemplateNotification', 'PreferenceNotification',
    'TypeNotification',
    'Workflow', 'ValidationRapport', 'HistoriqueValidation', 'ValidateurDesigne',
    'TypeRapport', 'StatutWorkflow', 'TypeAction'
]
