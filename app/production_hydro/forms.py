"""
Formulaires pour la production hydroélectrique
"""
from flask_wtf import FlaskForm
from wtforms import (
    StringField, FloatField, IntegerField, TextAreaField, 
    SelectField, DateField, DateTimeField, HiddenField,
    FieldList, FormField, SubmitField
)
from wtforms.validators import DataRequired, Optional, NumberRange, Length, Email
from app.utils.helpers import safe_int_coerce
from wtforms.widgets import TextArea
from datetime import datetime, date
from app.utils.permissions import get_operateur_choices, get_default_operateur_id


class CentraleHydroForm(FlaskForm):
    """Formulaire pour créer/modifier une centrale hydroélectrique"""
    
    # Opérateur (requis)
    operateur_id = SelectField('Opérateur', coerce=safe_int_coerce, validators=[DataRequired()])
    
    # Informations de base
    nom = StringField('Nom de la centrale', validators=[DataRequired(), Length(min=2, max=200)])
    code = StringField('Code centrale', validators=[DataRequired(), Length(min=2, max=50)])
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
    cours_eau = StringField('Cours d\'eau', validators=[Optional(), Length(max=100)])
    
    # Caractéristiques techniques
    puissance_installee = FloatField('Puissance installée (MW)', validators=[Optional(), NumberRange(min=0)])
    puissance_disponible = FloatField('Puissance disponible (MW)', validators=[Optional(), NumberRange(min=0)])
    hauteur_chute = FloatField('Hauteur de chute (m)', validators=[Optional(), NumberRange(min=0)])
    debit_equipement = FloatField('Débit d\'équipement (m³/s)', validators=[Optional(), NumberRange(min=0)])
    type_centrale = SelectField('Type de centrale',
                               choices=[
                                   ('', 'Sélectionner...'),
                                   ('au_fil_eau', 'Au fil de l\'eau'),
                                   ('reservoir', 'À réservoir'),
                                   ('eclusee', 'À éclusée'),
                                   ('pompage', 'Station de pompage')
                               ],
                               validators=[Optional()])
    
    # Équipements
    nombre_groupes = IntegerField('Nombre de groupes', validators=[Optional(), NumberRange(min=0)], default=0)
    nombre_transformateurs = IntegerField('Nombre de transformateurs', validators=[Optional(), NumberRange(min=0)], default=0)
    tension_evacuation = StringField('Tension d\'évacuation (kV)', validators=[Optional(), Length(max=50)])
    
    # Dates
    date_mise_service = DateField('Date de mise en service', validators=[Optional()])
    date_derniere_revision = DateField('Date dernière révision', validators=[Optional()])
    
    # Autres informations
    constructeur = StringField('Constructeur', validators=[Optional(), Length(max=100)])
    annee_construction = IntegerField('Année de construction', validators=[Optional(), NumberRange(min=1900, max=2030)])
    observations = TextAreaField('Observations', validators=[Optional()], widget=TextArea())
    
    def __init__(self, *args, **kwargs):
        super(CentraleHydroForm, self).__init__(*args, **kwargs)
        # Configurer les choix d'opérateurs selon les permissions
        self.operateur_id.choices = get_operateur_choices()
        # Définir la valeur par défaut si non admin
        if not kwargs.get('obj') and get_default_operateur_id():
            self.operateur_id.data = get_default_operateur_id()
    
    submit = SubmitField('Enregistrer')


class GroupeProductionForm(FlaskForm):
    """Formulaire pour un groupe de production (sous-formulaire)"""
    
    # Champs cachés pour la gestion dynamique
    id = HiddenField()
    delete = HiddenField()
    
    # Identification
    numero_groupe = StringField('N° Groupe', validators=[DataRequired(), Length(max=10)])
    nom_groupe = StringField('Nom du groupe', validators=[Optional(), Length(max=100)])
    
    # Caractéristiques techniques
    puissance_nominale = FloatField('Puissance nominale (MW)', validators=[Optional(), NumberRange(min=0)])
    tension_nominale = FloatField('Tension nominale (kV)', validators=[Optional(), NumberRange(min=0)])
    vitesse_rotation = FloatField('Vitesse rotation (tr/min)', validators=[Optional(), NumberRange(min=0)])
    type_turbine = SelectField('Type de turbine',
                              choices=[
                                  ('', 'Sélectionner...'),
                                  ('Pelton', 'Pelton'),
                                  ('Francis', 'Francis'),
                                  ('Kaplan', 'Kaplan'),
                                  ('Turgo', 'Turgo'),
                                  ('Banki', 'Banki'),
                                  ('Autre', 'Autre')
                              ],
                              validators=[Optional()])
    
    # Données de fonctionnement
    heures_fonctionnement = FloatField('Heures fonctionnement', validators=[Optional(), NumberRange(min=0)])
    energie_produite = FloatField('Énergie produite (MWh)', validators=[Optional(), NumberRange(min=0)])
    puissance_moyenne = FloatField('Puissance moyenne (MW)', validators=[Optional(), NumberRange(min=0)])
    puissance_max = FloatField('Puissance max (MW)', validators=[Optional(), NumberRange(min=0)])
    
    # Arrêts
    nombre_arrets_programme = IntegerField('Arrêts programmés', validators=[Optional(), NumberRange(min=0)], default=0)
    nombre_arrets_force = IntegerField('Arrêts forcés', validators=[Optional(), NumberRange(min=0)], default=0)
    duree_arrets_programme = FloatField('Durée arrêts prog. (h)', validators=[Optional(), NumberRange(min=0)], default=0.0)
    duree_arrets_force = FloatField('Durée arrêts forcés (h)', validators=[Optional(), NumberRange(min=0)], default=0.0)
    
    # Performance
    rendement_moyen = FloatField('Rendement moyen (%)', validators=[Optional(), NumberRange(min=0, max=100)])
    
    # Maintenance
    date_derniere_revision = DateField('Dernière révision', validators=[Optional()])
    type_derniere_revision = StringField('Type révision', validators=[Optional(), Length(max=100)])
    prochaine_revision = DateField('Prochaine révision', validators=[Optional()])
    
    # Observations
    incidents = TextAreaField('Incidents', validators=[Optional()], widget=TextArea())
    travaux_realises = TextAreaField('Travaux réalisés', validators=[Optional()], widget=TextArea())
    observations = TextAreaField('Observations', validators=[Optional()], widget=TextArea())


class TransformateurRapportForm(FlaskForm):
    """Formulaire pour un transformateur (sous-formulaire)"""
    
    # Champs cachés
    id = HiddenField()
    delete = HiddenField()
    
    # Identification
    numero_transformateur = StringField('N° Transformateur', validators=[DataRequired(), Length(max=10)])
    nom_transformateur = StringField('Nom', validators=[Optional(), Length(max=100)])
    
    # Caractéristiques
    puissance_nominale = FloatField('Puissance (MVA)', validators=[Optional(), NumberRange(min=0)])
    tension_primaire = FloatField('Tension primaire (kV)', validators=[Optional(), NumberRange(min=0)])
    tension_secondaire = FloatField('Tension secondaire (kV)', validators=[Optional(), NumberRange(min=0)])
    type_refroidissement = SelectField('Refroidissement',
                                      choices=[
                                          ('', 'Sélectionner...'),
                                          ('ONAN', 'ONAN - Huile naturelle'),
                                          ('ONAF', 'ONAF - Huile forcée'),
                                          ('OFAF', 'OFAF - Huile/Air forcé'),
                                          ('ODAF', 'ODAF - Huile dirigée'),
                                          ('Sec', 'Transformateur sec')
                                      ],
                                      validators=[Optional()])
    
    # Fonctionnement
    energie_transferee = FloatField('Énergie transférée (MWh)', validators=[Optional(), NumberRange(min=0)], default=0.0)
    heures_service = FloatField('Heures service', validators=[Optional(), NumberRange(min=0)], default=0.0)
    charge_moyenne = FloatField('Charge moyenne (%)', validators=[Optional(), NumberRange(min=0, max=150)], default=0.0)
    charge_max = FloatField('Charge max (%)', validators=[Optional(), NumberRange(min=0, max=150)], default=0.0)
    
    # Températures
    temperature_huile_moyenne = FloatField('Temp. huile moy. (°C)', validators=[Optional()])
    temperature_huile_max = FloatField('Temp. huile max (°C)', validators=[Optional()])
    temperature_enroulements_max = FloatField('Temp. enroulements max (°C)', validators=[Optional()])
    
    # État et maintenance
    etat_general = SelectField('État général',
                              choices=[
                                  ('bon', 'Bon'),
                                  ('moyen', 'Moyen'),
                                  ('mauvais', 'Mauvais'),
                                  ('critique', 'Critique')
                              ],
                              validators=[Optional()],
                              default='bon')
    date_derniere_maintenance = DateField('Dernière maintenance', validators=[Optional()])
    type_maintenance = StringField('Type maintenance', validators=[Optional(), Length(max=100)])
    prochaine_maintenance = DateField('Prochaine maintenance', validators=[Optional()])
    
    # Observations
    incidents = TextAreaField('Incidents', validators=[Optional()], widget=TextArea())
    travaux_realises = TextAreaField('Travaux réalisés', validators=[Optional()], widget=TextArea())
    observations = TextAreaField('Observations', validators=[Optional()], widget=TextArea())


class RapportHydroForm(FlaskForm):
    """Formulaire principal pour un rapport hydroélectrique"""
    
    # Sélection centrale
    centrale_id = SelectField('Centrale hydroélectrique', 
                             choices=[], 
                             validators=[DataRequired()],
                             coerce=lambda x: int(x) if x else None)
    
    # Période
    annee = IntegerField('Année', validators=[DataRequired(), NumberRange(min=2000, max=2030)])
    mois = SelectField('Mois',
                      choices=[
                          (1, 'Janvier'), (2, 'Février'), (3, 'Mars'),
                          (4, 'Avril'), (5, 'Mai'), (6, 'Juin'),
                          (7, 'Juillet'), (8, 'Août'), (9, 'Septembre'),
                          (10, 'Octobre'), (11, 'Novembre'), (12, 'Décembre')
                      ],
                      validators=[DataRequired()],
                      coerce=safe_int_coerce)
    periode_debut = DateField('Début période', validators=[DataRequired()])
    periode_fin = DateField('Fin période', validators=[DataRequired()])
    
    # Données hydrologiques
    niveau_retenue_moyen = FloatField('Niveau retenue moyen (m)', validators=[Optional(), NumberRange(min=0)])
    niveau_retenue_min = FloatField('Niveau retenue min (m)', validators=[Optional(), NumberRange(min=0)])
    niveau_retenue_max = FloatField('Niveau retenue max (m)', validators=[Optional(), NumberRange(min=0)])
    debit_moyen = FloatField('Débit moyen (m³/s)', validators=[Optional(), NumberRange(min=0)])
    debit_min = FloatField('Débit min (m³/s)', validators=[Optional(), NumberRange(min=0)])
    debit_max = FloatField('Débit max (m³/s)', validators=[Optional(), NumberRange(min=0)])
    volume_turbiné = FloatField('Volume turbiné (millions m³)', validators=[Optional(), NumberRange(min=0)])
    
    # Production
    energie_produite = FloatField('Énergie produite (MWh)', validators=[Optional(), NumberRange(min=0)])
    energie_disponible = FloatField('Énergie disponible (MWh)', validators=[Optional(), NumberRange(min=0)])
    facteur_charge = FloatField('Facteur de charge (%)', validators=[Optional(), NumberRange(min=0, max=100)])
    temps_fonctionnement = FloatField('Temps fonctionnement (h)', validators=[Optional(), NumberRange(min=0)])
    nombre_arrets = IntegerField('Nombre d\'arrêts', validators=[Optional(), NumberRange(min=0)], default=0)
    duree_arrets = FloatField('Durée arrêts (h)', validators=[Optional(), NumberRange(min=0)], default=0.0)
    
    # Rendements
    rendement_global = FloatField('Rendement global (%)', validators=[Optional(), NumberRange(min=0, max=100)])
    rendement_turbine = FloatField('Rendement turbine (%)', validators=[Optional(), NumberRange(min=0, max=100)])
    rendement_alternateur = FloatField('Rendement alternateur (%)', validators=[Optional(), NumberRange(min=0, max=100)])
    
    # Maintenance
    maintenances_preventives = IntegerField('Maintenances préventives', validators=[Optional(), NumberRange(min=0)], default=0)
    maintenances_correctives = IntegerField('Maintenances correctives', validators=[Optional(), NumberRange(min=0)], default=0)
    incidents_majeurs = IntegerField('Incidents majeurs', validators=[Optional(), NumberRange(min=0)], default=0)
    description_incidents = TextAreaField('Description incidents', validators=[Optional()], widget=TextArea())
    
    # Environnement
    debit_reserve = FloatField('Débit réservé (m³/s)', validators=[Optional(), NumberRange(min=0)])
    impact_environnemental = TextAreaField('Impact environnemental', validators=[Optional()], widget=TextArea())
    
    # Statut
    statut = SelectField('Statut',
                        choices=[
                            ('brouillon', 'Brouillon'),
                            ('valide', 'Validé'),
                            ('transmis', 'Transmis')
                        ],
                        validators=[DataRequired()],
                        default='brouillon')
    
    # Observations générales
    observations = TextAreaField('Observations générales', validators=[Optional()], widget=TextArea())
    
    # Listes dynamiques de sous-formulaires
    groupes_production = FieldList(FormField(GroupeProductionForm), min_entries=0)
    transformateurs = FieldList(FormField(TransformateurRapportForm), min_entries=0)
    
    # Boutons
    submit = SubmitField('Enregistrer le rapport')
    submit_validate = SubmitField('Enregistrer et valider')
    
    def __init__(self, *args, **kwargs):
        super(RapportHydroForm, self).__init__(*args, **kwargs)
        
        # Définir l'année et le mois par défaut
        if not self.annee.data:
            self.annee.data = datetime.now().year
        if not self.mois.data:
            self.mois.data = datetime.now().month
    
    def populate_centrales(self, centrales):
        """Peupler la liste des centrales"""
        choices = [('', 'Sélectionner une centrale...')]
        for centrale in centrales:
            choices.append((centrale.id, f"{centrale.nom} ({centrale.code})"))
        self.centrale_id.choices = choices
    
    def validate(self, extra_validators=None):
        """Validation personnalisée"""
        rv = FlaskForm.validate(self, extra_validators)
        if not rv:
            return False
        
        # Vérifier que la période de fin est après le début
        if self.periode_debut.data and self.periode_fin.data:
            if self.periode_fin.data < self.periode_debut.data:
                self.periode_fin.errors.append('La date de fin doit être postérieure à la date de début.')
                return False
        
        return True


class FiltreRapportForm(FlaskForm):
    """Formulaire pour filtrer les rapports"""
    
    centrale_id = SelectField('Centrale', choices=[('', 'Toutes les centrales')], coerce=lambda x: int(x) if x else None)
    annee = SelectField('Année', choices=[('', 'Toutes les années')])
    mois = SelectField('Mois', choices=[('', 'Tous les mois')])
    statut = SelectField('Statut',
                        choices=[
                            ('', 'Tous les statuts'),
                            ('brouillon', 'Brouillon'),
                            ('valide', 'Validé'),
                            ('transmis', 'Transmis')
                        ])
    
    submit = SubmitField('Filtrer')
    
    def populate_centrales(self, centrales):
        """Peupler la liste des centrales"""
        choices = [('', 'Toutes les centrales')]
        for centrale in centrales:
            choices.append((centrale.id, f"{centrale.nom} ({centrale.code})"))
        self.centrale_id.choices = choices
    
    def populate_annees(self, annees):
        """Peupler la liste des années"""
        choices = [('', 'Toutes les années')]
        for annee in sorted(annees, reverse=True):
            choices.append((str(annee), str(annee)))
        self.annee.choices = choices