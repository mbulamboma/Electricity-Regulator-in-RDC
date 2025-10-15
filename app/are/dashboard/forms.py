"""
Formulaires pour le dashboard ARE et la collecte de données
"""
from flask_wtf import FlaskForm
from wtforms import (
    SelectField, IntegerField, FloatField, StringField, 
    TextAreaField, DateField, HiddenField, SubmitField, BooleanField
)
from wtforms.validators import DataRequired, Optional, NumberRange, Length, Email
from datetime import datetime, date
from app.models.dashboard_are import TypeAlerte, SeveriteAlerte, CategorieIndicateur
from app.models.statistiques_are import TypeProjet
from app.utils.permissions import get_operateur_choices, get_dashboard_are_operateurs_choices
from app.utils.helpers import safe_int_coerce


class FiltreTableauBordForm(FlaskForm):
    """Formulaire pour filtrer le tableau de bord"""
    
    annee = SelectField('Année', 
                       choices=[(str(y), str(y)) for y in range(2020, datetime.now().year + 2)],
                       default=str(datetime.now().year),
                       coerce=lambda x: int(x) if x else None)
    
    operateur_id = SelectField('Opérateur', 
                              choices=[('', 'Tous les opérateurs')],
                              coerce=lambda x: int(x) if x else None,
                              validators=[Optional()])
    
    province = SelectField('Province',
                          choices=[
                              ('', 'Toutes les provinces'),
                              ('Kinshasa', 'Kinshasa'),
                              ('Bas-Congo', 'Bas-Congo'),
                              ('Bandundu', 'Bandundu'),
                              ('Équateur', 'Équateur'),
                              ('Orientale', 'Orientale'),
                              ('Nord-Kivu', 'Nord-Kivu'),
                              ('Sud-Kivu', 'Sud-Kivu'),
                              ('Maniema', 'Maniema'),
                              ('Katanga', 'Katanga'),
                              ('Kasaï-Oriental', 'Kasaï-Oriental'),
                              ('Kasaï-Occidental', 'Kasaï-Occidental')
                          ],
                          validators=[Optional()])
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Utiliser les choix d'opérateurs adaptés aux permissions du dashboard ARE
        self.operateur_id.choices = get_dashboard_are_operateurs_choices()


class AlerteForm(FlaskForm):
    """Formulaire pour créer/modifier une alerte"""
    
    type = SelectField('Type d\'alerte',
                      choices=[(t.value, t.value.replace('_', ' ').title()) for t in TypeAlerte],
                      validators=[DataRequired()])
    
    severite = SelectField('Sévérité',
                          choices=[(s.value, s.value.title()) for s in SeveriteAlerte],
                          validators=[DataRequired()])
    
    operateur_id = SelectField('Opérateur concerné',
                              choices=[('', 'Sélectionner un opérateur')],
                              coerce=lambda x: int(x) if x else None,
                              validators=[Optional()])
    
    entite_concernee = StringField('Entité concernée',
                                  validators=[DataRequired(), Length(max=200)])
    
    titre = StringField('Titre',
                       validators=[DataRequired(), Length(max=200)])
    
    description = TextAreaField('Description',
                               validators=[DataRequired()],
                               render_kw={'rows': 4})
    
    date_echeance = DateField('Date d\'échéance',
                             validators=[Optional()])
    
    actions_recommandees = TextAreaField('Actions recommandées',
                                       validators=[Optional()],
                                       render_kw={'rows': 3})
    
    priorite = SelectField('Priorité',
                          choices=[
                              (1, 'Haute'),
                              (2, 'Moyenne'),
                              (3, 'Basse')
                          ],
                          coerce=safe_int_coerce,
                          default=2)
    
    submit = SubmitField('Enregistrer')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.operateur_id.choices.extend(get_operateur_choices())


class KPIForm(FlaskForm):
    """Formulaire pour créer/modifier un KPI stratégique"""
    
    # Modèles prédéfinis pour faciliter la saisie
    modele_kpi = SelectField('Modèle KPI (optionnel)',
                            choices=[
                                ('', 'Créer un KPI personnalisé'),
                                ('taux_acces', 'Taux d\'accès à l\'électricité (%)'),
                                ('production_nationale', 'Production électrique nationale (GWh)'),
                                ('puissance_installee', 'Puissance installée totale (MW)'),
                                ('fiabilite_reseau', 'Fiabilité du réseau (SAIDI)'),
                                ('qualite_service', 'Qualité de service (SAIFI)'),
                                ('consommation_habitant', 'Consommation par habitant (kWh/hab)'),
                                ('pertes_techniques', 'Pertes techniques (%)'),
                                ('taux_collecte', 'Taux de collecte (%)')
                            ],
                            validators=[Optional()],
                            render_kw={'onchange': 'remplirModeleKPI(this.value)'})
    
    code = StringField('Code KPI',
                      validators=[DataRequired(), Length(max=50)],
                      render_kw={'placeholder': 'Ex: TAUX_ACCES_NATIONAL'})
    
    nom = StringField('Nom du KPI',
                     validators=[DataRequired(), Length(max=200)],
                     render_kw={'placeholder': 'Ex: Taux d\'accès à l\'électricité'})
    
    description = TextAreaField('Description',
                               validators=[Optional()],
                               render_kw={'rows': 3, 'placeholder': 'Décrivez ce que mesure ce KPI...'})
    
    valeur = FloatField('Valeur',
                       validators=[DataRequired()],
                       render_kw={'placeholder': 'Ex: 35.5'})
    
    unite = SelectField('Unité',
                       choices=[
                           ('', 'Sélectionner une unité'),
                           ('%', 'Pourcentage (%)'),
                           ('MW', 'Mégawatts (MW)'),
                           ('GWh', 'Gigawattheures (GWh)'),
                           ('MWh', 'Mégawattheures (MWh)'),
                           ('kWh/hab', 'kWh par habitant'),
                           ('minutes', 'Minutes'),
                           ('heures', 'Heures'),
                           ('nombre', 'Nombre'),
                           ('ratio', 'Ratio'),
                           ('USD', 'Dollars US'),
                           ('CDF', 'Francs congolais')
                       ],
                       validators=[DataRequired()])
    
    periode = SelectField('Type de période',
                         choices=[
                             ('annuelle', 'Annuelle'),
                             ('trimestrielle', 'Trimestrielle'),
                             ('mensuelle', 'Mensuelle')
                         ],
                         default='annuelle',
                         validators=[DataRequired()])
    
    annee = IntegerField('Année',
                        validators=[DataRequired(), NumberRange(min=2020, max=2030)],
                        default=datetime.now().year)
    
    mois = SelectField('Mois (si période mensuelle)',
                      choices=[
                          ('', 'Non applicable'),
                          ('01', 'Janvier'), ('02', 'Février'), ('03', 'Mars'),
                          ('04', 'Avril'), ('05', 'Mai'), ('06', 'Juin'),
                          ('07', 'Juillet'), ('08', 'Août'), ('09', 'Septembre'),
                          ('10', 'Octobre'), ('11', 'Novembre'), ('12', 'Décembre')
                      ],
                      validators=[Optional()])
    
    trimestre = SelectField('Trimestre (si période trimestrielle)',
                           choices=[
                               ('', 'Non applicable'),
                               ('Q1', 'Q1 (Jan-Mar)'),
                               ('Q2', 'Q2 (Avr-Juin)'),
                               ('Q3', 'Q3 (Juil-Sep)'),
                               ('Q4', 'Q4 (Oct-Déc)')
                           ],
                           validators=[Optional()])
    
    objectif = FloatField('Objectif (cible)',
                         validators=[Optional()],
                         render_kw={'placeholder': 'Ex: 50 (pour 50% d\'objectif)'})
    
    seuil_alerte = FloatField('Seuil d\'alerte',
                             validators=[Optional()],
                             render_kw={'placeholder': 'Valeur déclenchant une alerte'})
    
    operateur_id = SelectField('Opérateur',
                              choices=[('', 'National (tous opérateurs)')],
                              coerce=lambda x: int(x) if x else None,
                              validators=[Optional()])
    
    source_donnees = SelectField('Source des données',
                                choices=[
                                    ('', 'Sélectionner une source'),
                                    ('Rapports opérateurs', 'Rapports des opérateurs'),
                                    ('Rapports production', 'Rapports de production'),
                                    ('Rapports distribution', 'Rapports de distribution'),
                                    ('Rapports transport', 'Rapports de transport'),
                                    ('Base opérateurs', 'Base de données opérateurs'),
                                    ('Données terrain', 'Collecte terrain'),
                                    ('Statistiques nationales', 'Statistiques nationales'),
                                    ('Données financières', 'Rapports financiers'),
                                    ('Enquêtes satisfaction', 'Enquêtes de satisfaction'),
                                    ('Données techniques', 'Données techniques'),
                                    ('Autre', 'Autre source')
                                ],
                                validators=[DataRequired()],
                                render_kw={'class': 'form-select'})
    
    submit = SubmitField('Enregistrer le KPI')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.operateur_id.choices.extend(get_operateur_choices())


class IndicateurSectorielForm(FlaskForm):
    """Formulaire pour créer/modifier un indicateur sectoriel"""
    
    categorie = SelectField('Catégorie',
                           choices=[(c.value, c.value.title()) for c in CategorieIndicateur],
                           validators=[DataRequired()])
    
    sous_categorie = StringField('Sous-catégorie',
                                validators=[DataRequired(), Length(max=100)])
    
    nom = StringField('Nom de l\'indicateur',
                     validators=[DataRequired(), Length(max=200)])
    
    valeur = FloatField('Valeur',
                       validators=[DataRequired()])
    
    unite = StringField('Unité',
                       validators=[DataRequired(), Length(max=50)])
    
    periode = StringField('Période',
                         validators=[DataRequired(), Length(max=20)])
    
    annee = IntegerField('Année',
                        validators=[DataRequired(), NumberRange(min=2020, max=2030)],
                        default=datetime.now().year)
    
    evolution = FloatField('Évolution (%)',
                          validators=[Optional()],
                          render_kw={'placeholder': 'Ex: +5.2 pour +5.2%'})
    
    province = SelectField('Province',
                          choices=[
                              ('', 'National'),
                              ('Kinshasa', 'Kinshasa'),
                              ('Bas-Congo', 'Bas-Congo'),
                              ('Bandundu', 'Bandundu'),
                              ('Équateur', 'Équateur'),
                              ('Orientale', 'Orientale'),
                              ('Nord-Kivu', 'Nord-Kivu'),
                              ('Sud-Kivu', 'Sud-Kivu'),
                              ('Maniema', 'Maniema'),
                              ('Katanga', 'Katanga'),
                              ('Kasaï-Oriental', 'Kasaï-Oriental'),
                              ('Kasaï-Occidental', 'Kasaï-Occidental')
                          ],
                          validators=[Optional()])
    
    operateur_id = SelectField('Opérateur',
                              choices=[('', 'National (tous opérateurs)')],
                              coerce=lambda x: int(x) if x else None,
                              validators=[Optional()])
    
    submit = SubmitField('Enregistrer')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.operateur_id.choices.extend(get_operateur_choices())


class RapportAnnuelForm(FlaskForm):
    """Formulaire pour configurer un rapport annuel"""
    
    annee = IntegerField('Année',
                        validators=[DataRequired(), NumberRange(min=2020, max=2030)],
                        default=datetime.now().year - 1)
    
    titre = StringField('Titre du rapport',
                       validators=[DataRequired(), Length(max=200)],
                       default=lambda: f"Rapport annuel {datetime.now().year - 1}")
    
    periode_debut = DateField('Début de période',
                             validators=[DataRequired()],
                             default=lambda: date(datetime.now().year - 1, 1, 1))
    
    periode_fin = DateField('Fin de période',
                           validators=[DataRequired()],
                           default=lambda: date(datetime.now().year - 1, 12, 31))
    
    # Options de contenu
    inclure_mix_energetique = SelectField('Mix énergétique',
                                         choices=[('oui', 'Inclure'), ('non', 'Exclure')],
                                         default='oui')
    
    inclure_performance_operateurs = SelectField('Performance opérateurs',
                                                choices=[('oui', 'Inclure'), ('non', 'Exclure')],
                                                default='oui')
    
    inclure_indicateurs_financiers = SelectField('Indicateurs financiers',
                                                choices=[('oui', 'Inclure'), ('non', 'Exclure')],
                                                default='oui')
    
    inclure_activites_regulation = SelectField('Activités de régulation',
                                              choices=[('oui', 'Inclure'), ('non', 'Exclure')],
                                              default='oui')
    
    inclure_perspectives = SelectField('Perspectives et projets',
                                      choices=[('oui', 'Inclure'), ('non', 'Exclure')],
                                      default='oui')
    
    submit = SubmitField('Générer le rapport')


class ExportForm(FlaskForm):
    """Formulaire pour exporter des données"""
    
    format_export = SelectField('Format d\'export',
                               choices=[
                                   ('excel', 'Excel (.xlsx)'),
                                   ('csv', 'CSV'),
                                   ('pdf', 'PDF'),
                                   ('powerpoint', 'PowerPoint (.pptx)')
                               ],
                               validators=[DataRequired()],
                               default='excel')
    
    donnees_export = SelectField('Données à exporter',
                                choices=[
                                    ('kpis', 'KPIs stratégiques'),
                                    ('indicateurs', 'Indicateurs sectoriels'),
                                    ('alertes', 'Alertes'),
                                    ('performance', 'Performance opérateurs'),
                                    ('tout', 'Toutes les données')
                                ],
                                validators=[DataRequired()],
                                default='tout')
    
    annee_export = SelectField('Année',
                              choices=[(str(y), str(y)) for y in range(2020, datetime.now().year + 1)],
                              default=str(datetime.now().year),
                              coerce=lambda x: int(x) if x else None)
    
    operateur_id = SelectField('Opérateur',
                              choices=[('', 'Tous les opérateurs')],
                              coerce=lambda x: int(x) if x else None,
                              validators=[Optional()])
    
    submit = SubmitField('Exporter')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.operateur_id.choices.extend(get_operateur_choices())


# ===== FORMULAIRES DE COLLECTE DE DONNÉES MENSUELLES =====

class CollecteCapaciteForm(FlaskForm):
    """Formulaire de collecte des données de capacité installée mensuelle"""
    
    # Période de rapport
    annee = SelectField('Année', 
                       choices=[(str(y), str(y)) for y in range(2020, datetime.now().year + 2)],
                       default=str(datetime.now().year),
                       coerce=int,
                       validators=[DataRequired()])
    
    mois = SelectField('Mois',
                      choices=[
                          ('1', 'Janvier'), ('2', 'Février'), ('3', 'Mars'),
                          ('4', 'Avril'), ('5', 'Mai'), ('6', 'Juin'),
                          ('7', 'Juillet'), ('8', 'Août'), ('9', 'Septembre'),
                          ('10', 'Octobre'), ('11', 'Novembre'), ('12', 'Décembre')
                      ],
                      coerce=int,
                      validators=[DataRequired()])
    
    # Capacités par source d'énergie
    capacite_hydro_mw = FloatField('Capacité Hydroélectrique Installée (MW)',
                                  validators=[DataRequired(), NumberRange(min=0)],
                                  render_kw={'step': '0.01', 'placeholder': '0.00'})
    
    capacite_hydro_disponible_mw = FloatField('Capacité Hydroélectrique Disponible (MW)',
                                            validators=[Optional(), NumberRange(min=0)],
                                            render_kw={'step': '0.01', 'placeholder': '0.00'})
    
    production_hydro_gwh = FloatField('Production Hydroélectrique (GWh)',
                                     validators=[Optional(), NumberRange(min=0)],
                                     render_kw={'step': '0.01', 'placeholder': '0.00'})
    
    capacite_thermique_mw = FloatField('Capacité Thermique Installée (MW)',
                                      validators=[DataRequired(), NumberRange(min=0)],
                                      render_kw={'step': '0.01', 'placeholder': '0.00'})
    
    capacite_thermique_disponible_mw = FloatField('Capacité Thermique Disponible (MW)',
                                                 validators=[Optional(), NumberRange(min=0)],
                                                 render_kw={'step': '0.01', 'placeholder': '0.00'})
    
    production_thermique_gwh = FloatField('Production Thermique (GWh)',
                                         validators=[Optional(), NumberRange(min=0)],
                                         render_kw={'step': '0.01', 'placeholder': '0.00'})
    
    capacite_solaire_mw = FloatField('Capacité Solaire Installée (MW)',
                                    validators=[DataRequired(), NumberRange(min=0)],
                                    render_kw={'step': '0.01', 'placeholder': '0.00'})
    
    capacite_solaire_disponible_mw = FloatField('Capacité Solaire Disponible (MW)',
                                               validators=[Optional(), NumberRange(min=0)],
                                               render_kw={'step': '0.01', 'placeholder': '0.00'})
    
    production_solaire_gwh = FloatField('Production Solaire (GWh)',
                                       validators=[Optional(), NumberRange(min=0)],
                                       render_kw={'step': '0.01', 'placeholder': '0.00'})
    
    # Informations géographiques
    province = SelectField('Province',
                          choices=[
                              ('Kinshasa', 'Kinshasa'),
                              ('Kongo-Central', 'Kongo-Central'),
                              ('Kwango', 'Kwango'),
                              ('Kwilu', 'Kwilu'),
                              ('Mai-Ndombe', 'Mai-Ndombe'),
                              ('Équateur', 'Équateur'),
                              ('Mongala', 'Mongala'),
                              ('Nord-Ubangi', 'Nord-Ubangi'),
                              ('Sud-Ubangi', 'Sud-Ubangi'),
                              ('Tshuapa', 'Tshuapa'),
                              ('Bas-Uele', 'Bas-Uele'),
                              ('Haut-Uele', 'Haut-Uele'),
                              ('Ituri', 'Ituri'),
                              ('Tshopo', 'Tshopo'),
                              ('Nord-Kivu', 'Nord-Kivu'),
                              ('Sud-Kivu', 'Sud-Kivu'),
                              ('Maniema', 'Maniema'),
                              ('Haut-Katanga', 'Haut-Katanga'),
                              ('Lualaba', 'Lualaba'),
                              ('Haut-Lomami', 'Haut-Lomami'),
                              ('Tanganyika', 'Tanganyika'),
                              ('Lomami', 'Lomami'),
                              ('Kasaï', 'Kasaï'),
                              ('Kasaï-Central', 'Kasaï-Central'),
                              ('Kasaï-Oriental', 'Kasaï-Oriental'),
                              ('Sankuru', 'Sankuru')
                          ],
                          validators=[DataRequired()])
    
    # Notes et observations
    observations = TextAreaField('Observations et Notes',
                               validators=[Optional(), Length(max=500)],
                               render_kw={'rows': 3, 'placeholder': 'Notes sur les données saisies...'})
    
    submit = SubmitField('Enregistrer les Données de Capacité')


class CollecteClienteleForm(FlaskForm):
    """Formulaire de collecte des données de clientèle mensuelle"""
    
    # Période
    annee = SelectField('Année', 
                       choices=[(str(y), str(y)) for y in range(2020, datetime.now().year + 2)],
                       default=str(datetime.now().year),
                       coerce=int,
                       validators=[DataRequired()])
    
    mois = SelectField('Mois',
                      choices=[
                          ('1', 'Janvier'), ('2', 'Février'), ('3', 'Mars'),
                          ('4', 'Avril'), ('5', 'Mai'), ('6', 'Juin'),
                          ('7', 'Juillet'), ('8', 'Août'), ('9', 'Septembre'),
                          ('10', 'Octobre'), ('11', 'Novembre'), ('12', 'Décembre')
                      ],
                      coerce=int,
                      validators=[DataRequired()])
    
    # Clients par type de tension
    clients_haute_tension = IntegerField('Nombre de Clients Haute Tension (HT)',
                                       validators=[DataRequired(), NumberRange(min=0)],
                                       render_kw={'placeholder': '0'})
    
    clients_moyenne_tension = IntegerField('Nombre de Clients Moyenne Tension (MT)',
                                         validators=[DataRequired(), NumberRange(min=0)],
                                         render_kw={'placeholder': '0'})
    
    clients_basse_tension = IntegerField('Nombre de Clients Basse Tension (BT)',
                                       validators=[DataRequired(), NumberRange(min=0)],
                                       render_kw={'placeholder': '0'})
    
    # Clients facturés et desservis
    clients_factures = IntegerField('Nombre de Clients Facturés',
                                   validators=[Optional(), NumberRange(min=0)],
                                   render_kw={'placeholder': '0'})
    
    menages_factures = IntegerField('Nombre de Ménages Facturés',
                                   validators=[Optional(), NumberRange(min=0)],
                                   render_kw={'placeholder': '0'})
    
    menages_desservis = IntegerField('Nombre de Ménages Desservis',
                                    validators=[Optional(), NumberRange(min=0)],
                                    render_kw={'placeholder': '0'})
    
    # Données géographiques et de couverture
    population_zone = IntegerField('Population de la Zone de Desserte',
                                  validators=[Optional(), NumberRange(min=0)],
                                  render_kw={'placeholder': '0'})
    
    superficie_couverte_km2 = FloatField('Superficie Couverte (km²)',
                                        validators=[Optional(), NumberRange(min=0)],
                                        render_kw={'step': '0.01', 'placeholder': '0.00'})
    
    province = SelectField('Province',
                          choices=[
                              ('Kinshasa', 'Kinshasa'),
                              ('Kongo-Central', 'Kongo-Central'),
                              ('Kwango', 'Kwango'),
                              ('Kwilu', 'Kwilu'),
                              ('Mai-Ndombe', 'Mai-Ndombe'),
                              ('Équateur', 'Équateur'),
                              ('Mongala', 'Mongala'),
                              ('Nord-Ubangi', 'Nord-Ubangi'),
                              ('Sud-Ubangi', 'Sud-Ubangi'),
                              ('Tshuapa', 'Tshuapa'),
                              ('Bas-Uele', 'Bas-Uele'),
                              ('Haut-Uele', 'Haut-Uele'),
                              ('Ituri', 'Ituri'),
                              ('Tshopo', 'Tshopo'),
                              ('Nord-Kivu', 'Nord-Kivu'),
                              ('Sud-Kivu', 'Sud-Kivu'),
                              ('Maniema', 'Maniema'),
                              ('Haut-Katanga', 'Haut-Katanga'),
                              ('Lualaba', 'Lualaba'),
                              ('Haut-Lomami', 'Haut-Lomami'),
                              ('Tanganyika', 'Tanganyika'),
                              ('Lomami', 'Lomami'),
                              ('Kasaï', 'Kasaï'),
                              ('Kasaï-Central', 'Kasaï-Central'),
                              ('Kasaï-Oriental', 'Kasaï-Oriental'),
                              ('Sankuru', 'Sankuru')
                          ],
                          validators=[DataRequired()])
    
    # Observations
    observations = TextAreaField('Observations',
                               validators=[Optional(), Length(max=500)],
                               render_kw={'rows': 3, 'placeholder': 'Notes sur la clientèle...'})
    
    submit = SubmitField('Enregistrer les Données de Clientèle')


class CollecteProjetForm(FlaskForm):
    """Formulaire de collecte des données de nouveaux projets"""
    
    # Informations du projet
    nom_projet = StringField('Nom du Projet',
                           validators=[DataRequired(), Length(max=200)],
                           render_kw={'placeholder': 'Ex: Centrale Hydroélectrique de Katende'})
    
    type_projet = SelectField('Type de Projet',
                            choices=[
                                ('production_hydro', 'Production Hydroélectrique'),
                                ('production_thermique', 'Production Thermique'),
                                ('production_solaire', 'Production Solaire'),
                                ('transport', 'Transport/Transmission'),
                                ('distribution', 'Distribution'),
                                ('mini_grid', 'Mini-Grid')
                            ],
                            validators=[DataRequired()])
    
    capacite_prevue_mw = FloatField('Capacité Prévue (MW)',
                                   validators=[DataRequired(), NumberRange(min=0)],
                                   render_kw={'step': '0.01', 'placeholder': '0.00'})
    
    investissement_prevu_usd = FloatField('Investissement Prévu (Millions USD)',
                                         validators=[Optional(), NumberRange(min=0)],
                                         render_kw={'step': '0.01', 'placeholder': '0.00'})
    
    # Dates importantes
    date_depot_demande = DateField('Date de Dépôt de la Demande',
                                  validators=[DataRequired()],
                                  default=datetime.now().date)
    
    date_prevue_mise_service = DateField('Date Prévue de Mise en Service',
                                        validators=[Optional()])
    
    # Localisation
    province = SelectField('Province',
                          choices=[
                              ('Kinshasa', 'Kinshasa'),
                              ('Kongo-Central', 'Kongo-Central'),
                              ('Kwango', 'Kwango'),
                              ('Kwilu', 'Kwilu'),
                              ('Mai-Ndombe', 'Mai-Ndombe'),
                              ('Équateur', 'Équateur'),
                              ('Mongala', 'Mongala'),
                              ('Nord-Ubangi', 'Nord-Ubangi'),
                              ('Sud-Ubangi', 'Sud-Ubangi'),
                              ('Tshuapa', 'Tshuapa'),
                              ('Bas-Uele', 'Bas-Uele'),
                              ('Haut-Uele', 'Haut-Uele'),
                              ('Ituri', 'Ituri'),
                              ('Tshopo', 'Tshopo'),
                              ('Nord-Kivu', 'Nord-Kivu'),
                              ('Sud-Kivu', 'Sud-Kivu'),
                              ('Maniema', 'Maniema'),
                              ('Haut-Katanga', 'Haut-Katanga'),
                              ('Lualaba', 'Lualaba'),
                              ('Haut-Lomami', 'Haut-Lomami'),
                              ('Tanganyika', 'Tanganyika'),
                              ('Lomami', 'Lomami'),
                              ('Kasaï', 'Kasaï'),
                              ('Kasaï-Central', 'Kasaï-Central'),
                              ('Kasaï-Oriental', 'Kasaï-Oriental'),
                              ('Sankuru', 'Sankuru')
                          ],
                          validators=[DataRequired()])
    
    localisation_precise = StringField('Localisation Précise',
                                     validators=[Optional(), Length(max=200)],
                                     render_kw={'placeholder': 'Ville, commune, quartier...'})
    
    # Description du projet
    description_technique = TextAreaField('Description Technique',
                                        validators=[Optional(), Length(max=1000)],
                                        render_kw={'rows': 4, 'placeholder': 'Description technique du projet...'})
    
    population_beneficiaire = IntegerField('Population Bénéficiaire Estimée',
                                         validators=[Optional(), NumberRange(min=0)],
                                         render_kw={'placeholder': '0'})
    
    # Statut actuel
    statut_evaluation = SelectField('Statut d\'Évaluation ARE',
                                   choices=[
                                       ('en_etude', 'En Étude'),
                                       ('evaluation_technique', 'Évaluation Technique'),
                                       ('evaluation_environnementale', 'Évaluation Environnementale'),
                                       ('consultation_publique', 'Consultation Publique'),
                                       ('avis_favorable', 'Avis Favorable'),
                                       ('avis_conditionnel', 'Avis Favorable Conditionnel'),
                                       ('avis_defavorable', 'Avis Défavorable'),
                                       ('en_attente_complements', 'En Attente de Compléments')
                                   ],
                                   validators=[DataRequired()])
    
    # Informations complémentaires
    contact_projet = StringField('Responsable du Projet',
                               validators=[Optional(), Length(max=100)],
                               render_kw={'placeholder': 'Nom du responsable'})
    
    email_contact = StringField('Email de Contact',
                              validators=[Optional(), Email(), Length(max=100)],
                              render_kw={'placeholder': 'email@exemple.com'})
    
    telephone_contact = StringField('Téléphone de Contact',
                                  validators=[Optional(), Length(max=20)],
                                  render_kw={'placeholder': '+243...'})
    
    observations = TextAreaField('Observations',
                               validators=[Optional(), Length(max=500)],
                               render_kw={'rows': 3, 'placeholder': 'Notes additionnelles...'})
    
    submit = SubmitField('Enregistrer le Projet')


class CollecteSolaireForm(FlaskForm):
    """Formulaire spécialisé pour les données solaires détaillées"""
    
    # Période
    annee = SelectField('Année', 
                       choices=[(str(y), str(y)) for y in range(2020, datetime.now().year + 2)],
                       default=str(datetime.now().year),
                       coerce=int,
                       validators=[DataRequired()])
    
    mois = SelectField('Mois',
                      choices=[
                          ('1', 'Janvier'), ('2', 'Février'), ('3', 'Mars'),
                          ('4', 'Avril'), ('5', 'Mai'), ('6', 'Juin'),
                          ('7', 'Juillet'), ('8', 'Août'), ('9', 'Septembre'),
                          ('10', 'Octobre'), ('11', 'Novembre'), ('12', 'Décembre')
                      ],
                      coerce=int,
                      validators=[DataRequired()])
    
    # Type d'installation
    type_installation = SelectField('Type d\'Installation Solaire',
                                   choices=[
                                       ('champs_solaires', 'Champs Solaires (Centralisée)'),
                                       ('toitures_commerciales', 'Toitures Commerciales'),
                                       ('toitures_residentielles', 'Toitures Résidentielles'),
                                       ('kits_solaires', 'Kits Solaires Domestiques'),
                                       ('mini_grids', 'Mini-Grids Solaires'),
                                       ('pompage_solaire', 'Systèmes de Pompage Solaire'),
                                       ('eclairage_public', 'Éclairage Public Solaire')
                                   ],
                                   validators=[DataRequired()])
    
    # Données techniques
    puissance_installee_kw = FloatField('Puissance Installée (kW)',
                                       validators=[DataRequired(), NumberRange(min=0)],
                                       render_kw={'step': '0.01', 'placeholder': '0.00'})
    
    nombre_installations = IntegerField('Nombre d\'Installations',
                                      validators=[DataRequired(), NumberRange(min=1)],
                                      render_kw={'placeholder': '1'})
    
    production_mensuelle_kwh = FloatField('Production Mensuelle (kWh)',
                                         validators=[Optional(), NumberRange(min=0)],
                                         render_kw={'step': '0.01', 'placeholder': '0.00'})
    
    # Données de performance
    irradiance_moyenne = FloatField('Irradiance Moyenne Mensuelle (kWh/m²)',
                                   validators=[Optional(), NumberRange(min=0)],
                                   render_kw={'step': '0.01', 'placeholder': '0.00'})
    
    facteur_charge = FloatField('Facteur de Charge Moyen (%)',
                               validators=[Optional(), NumberRange(min=0, max=100)],
                               render_kw={'step': '0.01', 'placeholder': '0.00'})
    
    # Données de clientèle
    nombre_clients_desservis = IntegerField('Nombre de Clients Desservis',
                                          validators=[Optional(), NumberRange(min=0)],
                                          render_kw={'placeholder': '0'})
    
    population_beneficiaire = IntegerField('Population Bénéficiaire',
                                         validators=[Optional(), NumberRange(min=0)],
                                         render_kw={'placeholder': '0'})
    
    # Localisation
    province = SelectField('Province',
                          choices=[
                              ('Kinshasa', 'Kinshasa'),
                              ('Kongo-Central', 'Kongo-Central'),
                              ('Nord-Kivu', 'Nord-Kivu'),
                              ('Sud-Kivu', 'Sud-Kivu'),
                              ('Haut-Katanga', 'Haut-Katanga'),
                              ('Lualaba', 'Lualaba'),
                              ('Équateur', 'Équateur'),
                              ('Kasaï', 'Kasaï'),
                              ('Kasaï-Central', 'Kasaï-Central'),
                              ('Maniema', 'Maniema'),
                              ('Tshopo', 'Tshopo'),
                              ('Ituri', 'Ituri')
                          ],
                          validators=[DataRequired()])
    
    zone_climatique = SelectField('Zone Climatique',
                                 choices=[
                                     ('equatoriale', 'Équatoriale'),
                                     ('tropicale_humide', 'Tropicale Humide'),
                                     ('tropicale_seche', 'Tropicale Sèche'),
                                     ('subtropicale', 'Subtropicale')
                                 ],
                                 validators=[Optional()])
    
    # Informations techniques complémentaires
    technologie_panneaux = SelectField('Technologie des Panneaux',
                                      choices=[
                                          ('monocristallin', 'Silicium Monocristallin'),
                                          ('polycristallin', 'Silicium Polycristallin'),
                                          ('couche_mince', 'Couche Mince'),
                                          ('bifacial', 'Panneaux Bifaciaux'),
                                          ('autre', 'Autre Technologie')
                                      ],
                                      validators=[Optional()])
    
    systeme_stockage = BooleanField('Système de Stockage (Batteries)')
    
    capacite_stockage_kwh = FloatField('Capacité de Stockage (kWh)',
                                      validators=[Optional(), NumberRange(min=0)],
                                      render_kw={'step': '0.01', 'placeholder': '0.00'})
    
    # Coûts et financement
    cout_installation_usd = FloatField('Coût d\'Installation (USD)',
                                      validators=[Optional(), NumberRange(min=0)],
                                      render_kw={'step': '0.01', 'placeholder': '0.00'})
    
    tarif_kwh_usd = FloatField('Tarif de Vente (USD/kWh)',
                              validators=[Optional(), NumberRange(min=0)],
                              render_kw={'step': '0.001', 'placeholder': '0.000'})
    
    # Maintenance et performance
    pannes_mensuelles = IntegerField('Nombre de Pannes ce Mois',
                                   validators=[Optional(), NumberRange(min=0)],
                                   render_kw={'placeholder': '0'})
    
    taux_disponibilite = FloatField('Taux de Disponibilité (%)',
                                   validators=[Optional(), NumberRange(min=0, max=100)],
                                   render_kw={'step': '0.01', 'placeholder': '0.00'})
    
    observations = TextAreaField('Observations Techniques',
                               validators=[Optional(), Length(max=500)],
                               render_kw={'rows': 3, 'placeholder': 'Notes techniques, problèmes rencontrés...'})
    
    submit = SubmitField('Enregistrer les Données Solaires')
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.operateur_id.choices.extend(get_operateur_choices())
