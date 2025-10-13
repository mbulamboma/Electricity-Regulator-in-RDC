"""
Formulaires pour la production thermique
"""
from flask_wtf import FlaskForm
from wtforms import (
    StringField, FloatField, IntegerField, TextAreaField, 
    SelectField, DateField, FieldList, FormField, SubmitField, BooleanField
)
from wtforms.validators import DataRequired, Optional, NumberRange, Length, Email
from wtforms.widgets import TextArea
from app.utils.helpers import safe_int_coerce
from datetime import datetime, date
from app.utils.permissions import get_operateur_choices, get_default_operateur_id


def coerce_int_or_none(value):
    """Convertit en int ou None si vide"""
    if value == '' or value is None:
        return None
    return int(value)


class CentraleThermiqueForm(FlaskForm):
    """Formulaire pour créer/modifier une centrale thermique"""
    
    # Informations de base
    nom = StringField('Nom de la centrale', validators=[DataRequired(), Length(min=2, max=200)])
    code = StringField('Code centrale', validators=[DataRequired(), Length(min=2, max=50)])
    operateur_id = SelectField('Opérateur', coerce=safe_int_coerce, validators=[DataRequired()])
    localisation = StringField('Localisation', validators=[Optional(), Length(max=200)])
    province = SelectField('Province',
                          choices=[
                              ('', 'Sélectionner...'),
                              ('Kinshasa', 'Kinshasa'),
                              ('Bas-Congo', 'Bas-Congo'),
                              ('Bandundu', 'Bandundu'),
                              ('Equateur', 'Équateur'),
                              ('Province Orientale', 'Province Orientale'),
                              ('Nord-Kivu', 'Nord-Kivu'),
                              ('Sud-Kivu', 'Sud-Kivu'),
                              ('Maniema', 'Maniema'),
                              ('Katanga', 'Katanga'),
                              ('Kasai-Oriental', 'Kasaï-Oriental'),
                              ('Kasai-Occidental', 'Kasaï-Occidental'),
                              ('Haut-Katanga', 'Haut-Katanga'),
                              ('Lualaba', 'Lualaba'),
                              ('Kwango', 'Kwango'),
                              ('Kwilu', 'Kwilu'),
                              ('Mai-Ndombe', 'Mai-Ndombe')
                          ],
                          validators=[Optional()])
    
    # Caractéristiques techniques
    puissance_installee = FloatField('Puissance installée (MW)', validators=[Optional(), NumberRange(min=0)])
    puissance_disponible = FloatField('Puissance disponible (MW)', validators=[Optional(), NumberRange(min=0)])
    type_centrale = SelectField('Type de centrale',
                               choices=[
                                   ('', 'Sélectionner...'),
                                   ('diesel', 'Diesel'),
                                   ('gaz', 'Gaz naturel'),
                                   ('charbon', 'Charbon'),
                                   ('fuel_lourd', 'Fuel lourd'),
                                   ('biomasse', 'Biomasse'),
                                   ('turbine_gaz', 'Turbine à gaz'),
                                   ('cycle_combine', 'Cycle combiné')
                               ],
                               validators=[Optional()])
    
    type_combustible = SelectField('Type de combustible principal',
                                  choices=[
                                      ('', 'Sélectionner...'),
                                      ('diesel', 'Diesel/Gasoil'),
                                      ('fuel_lourd', 'Fuel lourd'),
                                      ('gaz_naturel', 'Gaz naturel'),
                                      ('charbon', 'Charbon'),
                                      ('biomasse', 'Biomasse'),
                                      ('dual_fuel', 'Dual fuel'),
                                      ('autre', 'Autre')
                                  ],
                                  validators=[Optional()])
    
    consommation_specifique = FloatField('Consommation spécifique (g/kWh)', validators=[Optional(), NumberRange(min=0)])
    
    # Coordonnées GPS
    latitude = FloatField('Latitude', validators=[Optional(), NumberRange(min=-90, max=90)])
    longitude = FloatField('Longitude', validators=[Optional(), NumberRange(min=-180, max=180)])
    
    # Équipements spécifiques thermique
    nombre_groupes = IntegerField('Nombre de groupes', validators=[Optional(), NumberRange(min=0)])
    type_moteur = SelectField('Type de moteur',
                             choices=[
                                 ('', 'Sélectionner...'),
                                 ('diesel', 'Moteur diesel'),
                                 ('turbine_gaz', 'Turbine à gaz'),
                                 ('turbine_vapeur', 'Turbine à vapeur'),
                                 ('moteur_gaz', 'Moteur à gaz'),
                                 ('cycle_combine', 'Cycle combiné')
                             ],
                             validators=[Optional()])
    
    refroidissement = SelectField('Système de refroidissement',
                                 choices=[
                                     ('', 'Sélectionner...'),
                                     ('air', 'Refroidissement par air'),
                                     ('eau', 'Refroidissement par eau'),
                                     ('mixte', 'Système mixte')
                                 ],
                                 validators=[Optional()])
    
    niveau_tension = FloatField('Niveau de tension (kV)', validators=[Optional(), NumberRange(min=0)])
    tension_evacuation = StringField('Tension d\'évacuation', validators=[Optional(), Length(max=50)])
    
    # Systèmes auxiliaires
    systeme_demarrage = SelectField('Système de démarrage',
                                   choices=[
                                       ('', 'Sélectionner...'),
                                       ('manuel', 'Manuel'),
                                       ('automatique', 'Automatique'),
                                       ('semi_automatique', 'Semi-automatique')
                                   ],
                                   validators=[Optional()])
    
    systeme_refroidissement = StringField('Système de refroidissement', validators=[Optional(), Length(max=100)])
    capacite_stockage_combustible = FloatField('Capacité stockage combustible (L/T)', validators=[Optional(), NumberRange(min=0)])
    autonomie_combustible = FloatField('Autonomie combustible (heures)', validators=[Optional(), NumberRange(min=0)])
    
    # Caractéristiques environnementales
    systeme_traitement_fumees = BooleanField('Système de traitement des fumées')
    niveau_emission_nox = FloatField('Niveau émission NOx (mg/Nm³)', validators=[Optional(), NumberRange(min=0)])
    niveau_emission_co = FloatField('Niveau émission CO (mg/Nm³)', validators=[Optional(), NumberRange(min=0)])
    certification_environnementale = StringField('Certification environnementale', validators=[Optional(), Length(max=100)])
    
    # Statut et état
    statut = SelectField('Statut',
                        choices=[
                            ('operationnelle', 'Opérationnelle'),
                            ('maintenance', 'En maintenance'),
                            ('arret', 'Arrêtée'),
                            ('construction', 'En construction')
                        ],
                        default='operationnelle',
                        validators=[DataRequired()])
    
    mode_fonctionnement = SelectField('Mode de fonctionnement',
                                     choices=[
                                         ('', 'Sélectionner...'),
                                         ('base', 'Base'),
                                         ('pointe', 'Pointe'),
                                         ('secours', 'Secours'),
                                         ('hybride', 'Hybride')
                                     ],
                                     validators=[Optional()])
    
    description = TextAreaField('Description', validators=[Optional(), Length(max=1000)])
    
    # Dates importantes
    date_mise_service = DateField('Date de mise en service', validators=[Optional()])
    date_derniere_revision = DateField('Date dernière révision', validators=[Optional()])
    prochaine_maintenance = DateField('Prochaine maintenance', validators=[Optional()])
    
    # Informations complémentaires
    constructeur = StringField('Constructeur', validators=[Optional(), Length(max=100)])
    fournisseur_combustible = StringField('Fournisseur de combustible', validators=[Optional(), Length(max=100)])
    annee_construction = IntegerField('Année de construction', validators=[Optional(), NumberRange(min=1950, max=2030)])
    duree_vie_estimee = IntegerField('Durée de vie estimée (années)', validators=[Optional(), NumberRange(min=1)])
    observations = TextAreaField('Observations', validators=[Optional()])
    
    submit = SubmitField('Enregistrer')
    
    def __init__(self, *args, **kwargs):
        super(CentraleThermiqueForm, self).__init__(*args, **kwargs)
        # Configurer les choix d'opérateurs selon les permissions
        self.operateur_id.choices = get_operateur_choices()
        # Définir la valeur par défaut si non admin
        if not kwargs.get('obj') and get_default_operateur_id():
            self.operateur_id.data = get_default_operateur_id()


class RapportThermiqueForm(FlaskForm):
    """Formulaire pour créer/modifier un rapport de production thermique"""
    
    # Centrale concernée
    centrale_id = SelectField('Centrale', coerce=coerce_int_or_none, validators=[DataRequired()])
    
    # Période de rapport
    annee = IntegerField('Année', validators=[DataRequired(), NumberRange(min=2020, max=2030)])
    mois = SelectField('Mois',
                      choices=[
                          (1, 'Janvier'), (2, 'Février'), (3, 'Mars'),
                          (4, 'Avril'), (5, 'Mai'), (6, 'Juin'),
                          (7, 'Juillet'), (8, 'Août'), (9, 'Septembre'),
                          (10, 'Octobre'), (11, 'Novembre'), (12, 'Décembre')
                      ],
                      coerce=safe_int_coerce,
                      validators=[DataRequired()])
    
    periode_debut = DateField('Début de période', validators=[DataRequired()])
    periode_fin = DateField('Fin de période', validators=[DataRequired()])
    
    # Production
    energie_produite = FloatField('Énergie produite (MWh)', validators=[Optional(), NumberRange(min=0)])
    energie_disponible = FloatField('Énergie disponible (MWh)', validators=[Optional(), NumberRange(min=0)])
    facteur_charge = FloatField('Facteur de charge (%)', validators=[Optional(), NumberRange(min=0, max=100)])
    temps_fonctionnement = FloatField('Temps de fonctionnement (heures)', validators=[Optional(), NumberRange(min=0)])
    nombre_demarrages = IntegerField('Nombre de démarrages', validators=[Optional(), NumberRange(min=0)])
    nombre_arrets = IntegerField('Nombre d\'arrêts', validators=[Optional(), NumberRange(min=0)])
    duree_arrets = FloatField('Durée des arrêts (heures)', validators=[Optional(), NumberRange(min=0)])
    
    # Consommation combustible
    consommation_combustible = FloatField('Consommation combustible (L/T)', validators=[Optional(), NumberRange(min=0)])
    type_combustible_utilise = SelectField('Type de combustible utilisé',
                                          choices=[
                                              ('', 'Sélectionner...'),
                                              ('diesel', 'Diesel/Gasoil'),
                                              ('fuel_lourd', 'Fuel lourd'),
                                              ('gaz_naturel', 'Gaz naturel'),
                                              ('charbon', 'Charbon'),
                                              ('biomasse', 'Biomasse')
                                          ],
                                          validators=[Optional()])
    
    cout_combustible = FloatField('Coût combustible (USD)', validators=[Optional(), NumberRange(min=0)])
    prix_unitaire_combustible = FloatField('Prix unitaire (USD/L ou USD/T)', validators=[Optional(), NumberRange(min=0)])
    consommation_specifique_reelle = FloatField('Consommation spécifique réelle (g/kWh)', validators=[Optional(), NumberRange(min=0)])
    
    # Performance thermique
    rendement_global = FloatField('Rendement global (%)', validators=[Optional(), NumberRange(min=0, max=100)])
    rendement_thermique = FloatField('Rendement thermique (%)', validators=[Optional(), NumberRange(min=0, max=100)])
    rendement_electrique = FloatField('Rendement électrique (%)', validators=[Optional(), NumberRange(min=0, max=100)])
    temperature_fumees = FloatField('Température des fumées (°C)', validators=[Optional(), NumberRange(min=0)])
    pression_admission = FloatField('Pression d\'admission (bar)', validators=[Optional(), NumberRange(min=0)])
    
    # Données d'exploitation
    charge_moyenne = FloatField('Charge moyenne (%)', validators=[Optional(), NumberRange(min=0, max=100)])
    charge_maximale = FloatField('Charge maximale (%)', validators=[Optional(), NumberRange(min=0, max=100)])
    charge_minimale = FloatField('Charge minimale (%)', validators=[Optional(), NumberRange(min=0, max=100)])
    temperature_ambiante_moyenne = FloatField('Température ambiante moyenne (°C)', validators=[Optional()])
    humidite_relative_moyenne = FloatField('Humidité relative moyenne (%)', validators=[Optional(), NumberRange(min=0, max=100)])
    
    # Maintenance et incidents
    maintenances_preventives = IntegerField('Maintenances préventives', validators=[Optional(), NumberRange(min=0)])
    maintenances_correctives = IntegerField('Maintenances correctives', validators=[Optional(), NumberRange(min=0)])
    incidents_majeurs = IntegerField('Incidents majeurs', validators=[Optional(), NumberRange(min=0)])
    description_incidents = TextAreaField('Description des incidents', validators=[Optional()])
    duree_maintenance = FloatField('Durée de maintenance (heures)', validators=[Optional(), NumberRange(min=0)])
    
    # Consommables et lubrifiants
    consommation_huile_moteur = FloatField('Consommation huile moteur (L)', validators=[Optional(), NumberRange(min=0)])
    consommation_liquide_refroidissement = FloatField('Consommation liquide refroidissement (L)', validators=[Optional(), NumberRange(min=0)])
    remplacement_filtres = IntegerField('Remplacement de filtres', validators=[Optional(), NumberRange(min=0)])
    autres_consommables = TextAreaField('Autres consommables', validators=[Optional()])
    
    # Données environnementales
    emissions_co2 = FloatField('Émissions CO2 (tonnes)', validators=[Optional(), NumberRange(min=0)])
    emissions_nox = FloatField('Émissions NOx (kg)', validators=[Optional(), NumberRange(min=0)])
    emissions_co = FloatField('Émissions CO (kg)', validators=[Optional(), NumberRange(min=0)])
    gestion_dechets = TextAreaField('Gestion des déchets', validators=[Optional()])
    impact_environnemental = TextAreaField('Impact environnemental', validators=[Optional()])
    
    # Données économiques
    cout_exploitation = FloatField('Coût d\'exploitation (USD)', validators=[Optional(), NumberRange(min=0)])
    cout_maintenance = FloatField('Coût de maintenance (USD)', validators=[Optional(), NumberRange(min=0)])
    recettes_vente = FloatField('Recettes de vente (USD)', validators=[Optional(), NumberRange(min=0)])
    rentabilite = FloatField('Rentabilité (%)', validators=[Optional()])
    
    # Statut du rapport
    statut = SelectField('Statut du rapport',
                        choices=[
                            ('brouillon', 'Brouillon'),
                            ('valide', 'Validé'),
                            ('transmis', 'Transmis')
                        ],
                        default='brouillon',
                        validators=[DataRequired()])
    
    # Observations
    observations = TextAreaField('Observations', validators=[Optional()])
    
    submit = SubmitField('Enregistrer le rapport')
    
    def __init__(self, *args, **kwargs):
        super(RapportThermiqueForm, self).__init__(*args, **kwargs)
        # Import here to avoid circular imports
        from app.models.production_thermique import CentraleThermique
        # Charger les centrales actives pour la liste déroulante
        centrales = CentraleThermique.query.filter_by(actif=True).all()
        self.centrale_id.choices = [(None, 'Sélectionner une centrale')] + [
            (c.id, f"{c.nom} ({c.code})") for c in centrales
        ]


class GroupeProductionThermiqueForm(FlaskForm):
    """Formulaire pour les données de groupe de production thermique"""
    
    numero_groupe = IntegerField('Numéro du groupe', validators=[DataRequired(), NumberRange(min=1)])
    nom_groupe = StringField('Nom du groupe', validators=[Optional(), Length(max=100)])
    type_groupe = SelectField('Type de groupe',
                             choices=[
                                 ('', 'Sélectionner...'),
                                 ('diesel', 'Diesel'),
                                 ('gaz', 'Gaz'),
                                 ('turbine', 'Turbine'),
                                 ('vapeur', 'Vapeur')
                             ],
                             validators=[Optional()])
    
    # Production
    energie_produite = FloatField('Énergie produite (MWh)', validators=[Optional(), NumberRange(min=0)])
    temps_fonctionnement = FloatField('Temps de fonctionnement (h)', validators=[Optional(), NumberRange(min=0)])
    nombre_demarrages = IntegerField('Nombre de démarrages', validators=[Optional(), NumberRange(min=0)])
    facteur_charge = FloatField('Facteur de charge (%)', validators=[Optional(), NumberRange(min=0, max=100)])
    
    # Consommation
    consommation_combustible = FloatField('Consommation combustible', validators=[Optional(), NumberRange(min=0)])
    consommation_specifique = FloatField('Consommation spécifique (g/kWh)', validators=[Optional(), NumberRange(min=0)])
    
    # Performance
    rendement = FloatField('Rendement (%)', validators=[Optional(), NumberRange(min=0, max=100)])
    puissance_moyenne = FloatField('Puissance moyenne (MW)', validators=[Optional(), NumberRange(min=0)])
    temperature_echappement = FloatField('Température échappement (°C)', validators=[Optional(), NumberRange(min=0)])
    
    # État et maintenance
    etat_general = SelectField('État général',
                              choices=[
                                  ('', 'Sélectionner...'),
                                  ('bon', 'Bon'),
                                  ('moyen', 'Moyen'),
                                  ('defaillant', 'Défaillant')
                              ],
                              validators=[Optional()])
    
    heures_fonctionnement_totales = FloatField('Heures fonctionnement totales', validators=[Optional(), NumberRange(min=0)])
    prochaine_maintenance = DateField('Prochaine maintenance', validators=[Optional()])
    observations = TextAreaField('Observations', validators=[Optional()])


class FiltreRapportThermiqueForm(FlaskForm):
    """Formulaire pour filtrer les rapports thermiques"""
    
    centrale_id = SelectField('Centrale', coerce=coerce_int_or_none, validators=[Optional()])
    annee = SelectField('Année', coerce=coerce_int_or_none, validators=[Optional()])
    mois = SelectField('Mois',
                      choices=[('', 'Tous les mois')] + [
                          (i, f'{i:02d}') for i in range(1, 13)
                      ],
                      coerce=str,
                      validators=[Optional()])
    
    statut = SelectField('Statut',
                        choices=[
                            ('', 'Tous les statuts'),
                            ('brouillon', 'Brouillon'),
                            ('valide', 'Validé'),
                            ('transmis', 'Transmis')
                        ],
                        validators=[Optional()])
    
    submit = SubmitField('Filtrer')