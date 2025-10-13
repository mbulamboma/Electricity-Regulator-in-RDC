"""
Formulaires pour la production solaire
"""
from flask_wtf import FlaskForm
from wtforms import (
    StringField, FloatField, IntegerField, TextAreaField, 
    SelectField, DateField, FieldList, FormField, SubmitField, BooleanField
)
from wtforms.validators import DataRequired, Optional, NumberRange, Length, Email
from wtforms.widgets import TextArea
from datetime import datetime, date
from app.utils.permissions import get_operateur_choices, get_default_operateur_id
from app.utils.helpers import safe_int_coerce


class CentraleSolaireForm(FlaskForm):
    """Formulaire pour créer/modifier une centrale solaire"""
    
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
    puissance_installee = FloatField('Puissance installée (MWc)', validators=[Optional(), NumberRange(min=0)])
    puissance_disponible = FloatField('Puissance disponible (MW)', validators=[Optional(), NumberRange(min=0)])
    type_centrale = SelectField('Type de centrale',
                               choices=[
                                   ('', 'Sélectionner...'),
                                   ('fixe', 'Installation fixe'),
                                   ('tracker', 'Avec système de suivi'),
                                   ('flottante', 'Flottante'),
                                   ('agrovoltaique', 'Agrovoltaïque'),
                                   ('toiture', 'Sur toiture'),
                                   ('sol', 'Au sol')
                               ],
                               validators=[Optional()])
    
    technologie_modules = SelectField('Technologie des modules',
                                     choices=[
                                         ('', 'Sélectionner...'),
                                         ('silicium_monocristallin', 'Silicium monocristallin'),
                                         ('silicium_polycristallin', 'Silicium polycristallin'),
                                         ('couches_minces', 'Couches minces'),
                                         ('cigs', 'CIGS'),
                                         ('cdte', 'CdTe'),
                                         ('organiques', 'Cellules organiques'),
                                         ('perovskite', 'Pérovskite')
                                     ],
                                     validators=[Optional()])
    
    # Coordonnées GPS et orientation
    latitude = FloatField('Latitude', validators=[Optional(), NumberRange(min=-90, max=90)])
    longitude = FloatField('Longitude', validators=[Optional(), NumberRange(min=-180, max=180)])
    altitude = FloatField('Altitude (m)', validators=[Optional(), NumberRange(min=0)])
    orientation_azimut = FloatField('Orientation azimut (°)', validators=[Optional(), NumberRange(min=0, max=360)])
    inclinaison_modules = FloatField('Inclinaison modules (°)', validators=[Optional(), NumberRange(min=0, max=90)])
    
    # Modules photovoltaïques
    nombre_modules = IntegerField('Nombre de modules', validators=[Optional(), NumberRange(min=0)])
    puissance_unitaire_module = FloatField('Puissance unitaire module (Wc)', validators=[Optional(), NumberRange(min=0)])
    marque_modules = StringField('Marque des modules', validators=[Optional(), Length(max=100)])
    modele_modules = StringField('Modèle des modules', validators=[Optional(), Length(max=100)])
    technologie_cellules = SelectField('Technologie des cellules',
                                      choices=[
                                          ('', 'Sélectionner...'),
                                          ('monocristallin', 'Monocristallin'),
                                          ('polycristallin', 'Polycristallin'),
                                          ('amorphe', 'Silicium amorphe'),
                                          ('heterojunction', 'Hétérojonction'),
                                          ('perc', 'PERC'),
                                          ('topcon', 'TOPCon'),
                                          ('bifacial', 'Bifacial')
                                      ],
                                      validators=[Optional()])
    
    # Systèmes de conversion
    nombre_onduleurs = IntegerField('Nombre d\'onduleurs', validators=[Optional(), NumberRange(min=0)])
    puissance_unitaire_onduleur = FloatField('Puissance unitaire onduleur (kW)', validators=[Optional(), NumberRange(min=0)])
    marque_onduleurs = StringField('Marque des onduleurs', validators=[Optional(), Length(max=100)])
    type_onduleur = SelectField('Type d\'onduleur',
                               choices=[
                                   ('', 'Sélectionner...'),
                                   ('string', 'String'),
                                   ('central', 'Central'),
                                   ('micro', 'Micro-onduleur'),
                                   ('optimiseur', 'Optimiseur de puissance')
                               ],
                               validators=[Optional()])
    
    rendement_onduleur = FloatField('Rendement onduleur (%)', validators=[Optional(), NumberRange(min=0, max=100)])
    
    # Systèmes de stockage (si applicable)
    stockage_batterie = BooleanField('Système de stockage par batterie')
    capacite_stockage = FloatField('Capacité de stockage (kWh)', validators=[Optional(), NumberRange(min=0)])
    type_batterie = SelectField('Type de batterie',
                               choices=[
                                   ('', 'Sélectionner...'),
                                   ('lithium_ion', 'Lithium-ion'),
                                   ('plomb_acide', 'Plomb-acide'),
                                   ('nickel_cadmium', 'Nickel-cadmium'),
                                   ('sodium_soufre', 'Sodium-soufre'),
                                   ('vanadium', 'Redox vanadium'),
                                   ('air_comprime', 'Air comprimé')
                               ],
                               validators=[Optional()])
    
    nombre_batteries = IntegerField('Nombre de batteries', validators=[Optional(), NumberRange(min=0)])
    marque_batteries = StringField('Marque des batteries', validators=[Optional(), Length(max=100)])
    
    # Système de suivi (tracking)
    systeme_suivi = BooleanField('Système de suivi solaire')
    type_suivi = SelectField('Type de suivi',
                            choices=[
                                ('', 'Sélectionner...'),
                                ('monoaxial', 'Monoaxial'),
                                ('biaxial', 'Biaxial'),
                                ('horizontal', 'Horizontal'),
                                ('vertical', 'Vertical')
                            ],
                            validators=[Optional()])
    
    precision_suivi = FloatField('Précision du suivi (°)', validators=[Optional(), NumberRange(min=0)])
    
    # Infrastructure électrique
    niveau_tension = FloatField('Niveau de tension (kV)', validators=[Optional(), NumberRange(min=0)])
    tension_evacuation = StringField('Tension d\'évacuation', validators=[Optional(), Length(max=50)])
    nombre_transformateurs = IntegerField('Nombre de transformateurs', validators=[Optional(), NumberRange(min=0)])
    puissance_transformateurs = FloatField('Puissance transformateurs (MVA)', validators=[Optional(), NumberRange(min=0)])
    
    # Données météorologiques et performance
    irradiation_annuelle_estimee = FloatField('Irradiation annuelle estimée (kWh/m²/an)', validators=[Optional(), NumberRange(min=0)])
    temperature_fonctionnement_nominale = FloatField('Température fonctionnement nominale (°C)', validators=[Optional()])
    coefficient_temperature = FloatField('Coefficient de température (%/°C)', validators=[Optional()])
    facteur_degradation_annuelle = FloatField('Facteur de dégradation annuelle (%/an)', validators=[Optional(), NumberRange(min=0)])
    
    # Système de monitoring
    systeme_monitoring = BooleanField('Système de monitoring')
    fournisseur_monitoring = StringField('Fournisseur du monitoring', validators=[Optional(), Length(max=100)])
    precision_mesure = FloatField('Précision des mesures (%)', validators=[Optional(), NumberRange(min=0, max=100)])
    
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
                                         ('grid_tied', 'Connecté au réseau'),
                                         ('off_grid', 'Autonome'),
                                         ('hybride', 'Hybride'),
                                         ('stockage', 'Avec stockage')
                                     ],
                                     validators=[Optional()])
    
    superficie_totale = FloatField('Superficie totale (hectares)', validators=[Optional(), NumberRange(min=0)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=1000)])
    
    # Dates importantes
    date_mise_service = DateField('Date de mise en service', validators=[Optional()])
    date_derniere_revision = DateField('Date dernière révision', validators=[Optional()])
    prochaine_maintenance = DateField('Prochaine maintenance', validators=[Optional()])
    
    # Informations complémentaires
    constructeur = StringField('Constructeur', validators=[Optional(), Length(max=100)])
    installateur = StringField('Installateur', validators=[Optional(), Length(max=100)])
    annee_construction = IntegerField('Année de construction', validators=[Optional(), NumberRange(min=2000, max=2030)])
    duree_vie_estimee = IntegerField('Durée de vie estimée (années)', validators=[Optional(), NumberRange(min=1)])
    garantie_modules = IntegerField('Garantie modules (années)', validators=[Optional(), NumberRange(min=0)])
    garantie_onduleurs = IntegerField('Garantie onduleurs (années)', validators=[Optional(), NumberRange(min=0)])
    observations = TextAreaField('Observations', validators=[Optional()])
    
    submit = SubmitField('Enregistrer')
    
    def __init__(self, *args, **kwargs):
        super(CentraleSolaireForm, self).__init__(*args, **kwargs)
        # Configurer les choix d'opérateurs selon les permissions
        self.operateur_id.choices = get_operateur_choices()
        # Définir la valeur par défaut si non admin
        if not kwargs.get('obj') and get_default_operateur_id():
            self.operateur_id.data = get_default_operateur_id()


class RapportSolaireForm(FlaskForm):
    """Formulaire pour créer/modifier un rapport de production solaire"""
    
    # Centrale concernée
    centrale_id = SelectField('Centrale', coerce=safe_int_coerce, validators=[DataRequired()])
    
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
    productible_theorique = FloatField('Productible théorique (MWh)', validators=[Optional(), NumberRange(min=0)])
    performance_ratio = FloatField('Performance Ratio (%)', validators=[Optional(), NumberRange(min=0, max=100)])
    
    # Données météorologiques
    irradiation_totale = FloatField('Irradiation totale (kWh/m²)', validators=[Optional(), NumberRange(min=0)])
    irradiation_moyenne_quotidienne = FloatField('Irradiation moyenne quotidienne (kWh/m²/jour)', validators=[Optional(), NumberRange(min=0)])
    temperature_ambiante_moyenne = FloatField('Température ambiante moyenne (°C)', validators=[Optional()])
    temperature_modules_moyenne = FloatField('Température modules moyenne (°C)', validators=[Optional()])
    humidite_relative_moyenne = FloatField('Humidité relative moyenne (%)', validators=[Optional(), NumberRange(min=0, max=100)])
    vitesse_vent_moyenne = FloatField('Vitesse vent moyenne (m/s)', validators=[Optional(), NumberRange(min=0)])
    heures_ensoleillement = FloatField('Heures d\'ensoleillement', validators=[Optional(), NumberRange(min=0, max=744)])
    
    # Performance du système
    rendement_global = FloatField('Rendement global (%)', validators=[Optional(), NumberRange(min=0, max=100)])
    rendement_modules = FloatField('Rendement modules (%)', validators=[Optional(), NumberRange(min=0, max=100)])
    rendement_onduleurs = FloatField('Rendement onduleurs (%)', validators=[Optional(), NumberRange(min=0, max=100)])
    pertes_ombrages = FloatField('Pertes par ombrages (%)', validators=[Optional(), NumberRange(min=0, max=100)])
    pertes_cables = FloatField('Pertes câbles (%)', validators=[Optional(), NumberRange(min=0, max=100)])
    pertes_poussiere = FloatField('Pertes poussière (%)', validators=[Optional(), NumberRange(min=0, max=100)])
    pertes_thermiques = FloatField('Pertes thermiques (%)', validators=[Optional(), NumberRange(min=0, max=100)])
    
    # Fonctionnement onduleurs
    temps_fonctionnement_onduleurs = FloatField('Temps fonctionnement onduleurs (h)', validators=[Optional(), NumberRange(min=0)])
    nombre_demarrages_onduleurs = IntegerField('Nombre démarrages onduleurs', validators=[Optional(), NumberRange(min=0)])
    nombre_arrets_onduleurs = IntegerField('Nombre arrêts onduleurs', validators=[Optional(), NumberRange(min=0)])
    alarmes_onduleurs = IntegerField('Alarmes onduleurs', validators=[Optional(), NumberRange(min=0)])
    
    # Système de stockage (si applicable)
    energie_stockee = FloatField('Énergie stockée (MWh)', validators=[Optional(), NumberRange(min=0)])
    energie_destockee = FloatField('Énergie déstockée (MWh)', validators=[Optional(), NumberRange(min=0)])
    rendement_stockage = FloatField('Rendement stockage (%)', validators=[Optional(), NumberRange(min=0, max=100)])
    cycles_charge_decharge = IntegerField('Cycles charge/décharge', validators=[Optional(), NumberRange(min=0)])
    etat_sante_batteries = FloatField('État santé batteries (%)', validators=[Optional(), NumberRange(min=0, max=100)])
    
    # Système de suivi (tracking)
    precision_suivi_moyenne = FloatField('Précision suivi moyenne (°)', validators=[Optional(), NumberRange(min=0)])
    defauts_suivi = IntegerField('Défauts de suivi', validators=[Optional(), NumberRange(min=0)])
    maintenance_systeme_suivi = IntegerField('Maintenances système suivi', validators=[Optional(), NumberRange(min=0)])
    
    # Maintenance et incidents
    maintenances_preventives = IntegerField('Maintenances préventives', validators=[Optional(), NumberRange(min=0)])
    maintenances_correctives = IntegerField('Maintenances correctives', validators=[Optional(), NumberRange(min=0)])
    nettoyage_modules = IntegerField('Nettoyages modules', validators=[Optional(), NumberRange(min=0)])
    incidents_majeurs = IntegerField('Incidents majeurs', validators=[Optional(), NumberRange(min=0)])
    description_incidents = TextAreaField('Description des incidents', validators=[Optional()])
    modules_defectueux = IntegerField('Modules défectueux', validators=[Optional(), NumberRange(min=0)])
    onduleurs_defectueux = IntegerField('Onduleurs défectueux', validators=[Optional(), NumberRange(min=0)])
    
    # Données de surveillance
    defauts_systeme_monitoring = IntegerField('Défauts système monitoring', validators=[Optional(), NumberRange(min=0)])
    disponibilite_donnees = FloatField('Disponibilité données (%)', validators=[Optional(), NumberRange(min=0, max=100)])
    precision_mesures = FloatField('Précision mesures (%)', validators=[Optional(), NumberRange(min=0, max=100)])
    
    # Données environnementales
    reduction_emissions_co2 = FloatField('Réduction émissions CO2 (tonnes)', validators=[Optional(), NumberRange(min=0)])
    impact_environnemental = TextAreaField('Impact environnemental', validators=[Optional()])
    gestion_fin_vie_composants = TextAreaField('Gestion fin de vie composants', validators=[Optional()])
    
    # Données économiques
    cout_maintenance = FloatField('Coût maintenance (USD)', validators=[Optional(), NumberRange(min=0)])
    cout_nettoyage = FloatField('Coût nettoyage (USD)', validators=[Optional(), NumberRange(min=0)])
    recettes_vente = FloatField('Recettes vente (USD)', validators=[Optional(), NumberRange(min=0)])
    economie_carburant = FloatField('Économie carburant (USD)', validators=[Optional(), NumberRange(min=0)])
    rentabilite = FloatField('Rentabilité (%)', validators=[Optional()])
    
    # Indicateurs de performance
    degradation_observee = FloatField('Dégradation observée (%)', validators=[Optional(), NumberRange(min=0)])
    disponibilite_systeme = FloatField('Disponibilité système (%)', validators=[Optional(), NumberRange(min=0, max=100)])
    taux_defaillance = FloatField('Taux de défaillance (%)', validators=[Optional(), NumberRange(min=0, max=100)])
    
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
        super(RapportSolaireForm, self).__init__(*args, **kwargs)
        # Import here to avoid circular imports
        from app.models.production_solaire import CentraleSolaire
        # Charger les centrales actives pour la liste déroulante
        centrales = CentraleSolaire.query.filter_by(actif=True).all()
        self.centrale_id.choices = [(None, 'Sélectionner une centrale')] + [
            (c.id, f"{c.nom} ({c.code})") for c in centrales
        ]


class DonneesSolaireQuotidiennesForm(FlaskForm):
    """Formulaire pour les données quotidiennes solaires"""
    
    date_production = DateField('Date de production', validators=[DataRequired()])
    
    # Production
    energie_produite = FloatField('Énergie produite (kWh)', validators=[Optional(), NumberRange(min=0)])
    puissance_max = FloatField('Puissance maximale (kW)', validators=[Optional(), NumberRange(min=0)])
    heure_puissance_max = StringField('Heure puissance max (HH:MM)', validators=[Optional(), Length(max=10)])
    
    # Météorologie
    irradiation = FloatField('Irradiation (kWh/m²)', validators=[Optional(), NumberRange(min=0)])
    temperature_ambiante_max = FloatField('Température ambiante max (°C)', validators=[Optional()])
    temperature_ambiante_min = FloatField('Température ambiante min (°C)', validators=[Optional()])
    temperature_modules_max = FloatField('Température modules max (°C)', validators=[Optional()])
    humidite_relative = FloatField('Humidité relative (%)', validators=[Optional(), NumberRange(min=0, max=100)])
    vitesse_vent_max = FloatField('Vitesse vent max (m/s)', validators=[Optional(), NumberRange(min=0)])
    
    # Performance
    performance_ratio = FloatField('Performance Ratio (%)', validators=[Optional(), NumberRange(min=0, max=100)])
    rendement_quotidien = FloatField('Rendement quotidien (%)', validators=[Optional(), NumberRange(min=0, max=100)])
    
    # Incidents
    duree_arrets = FloatField('Durée arrêts (heures)', validators=[Optional(), NumberRange(min=0, max=24)])
    cause_arrets = StringField('Cause des arrêts', validators=[Optional(), Length(max=200)])


class FiltreRapportSolaireForm(FlaskForm):
    """Formulaire pour filtrer les rapports solaires"""
    
    centrale_id = SelectField('Centrale', coerce=safe_int_coerce, validators=[Optional()])
    annee = SelectField('Année', coerce=safe_int_coerce, validators=[Optional()])
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