"""
Formulaires pour le dashboard ARE
"""
from flask_wtf import FlaskForm
from wtforms import (
    SelectField, IntegerField, FloatField, StringField, 
    TextAreaField, DateField, HiddenField, SubmitField
)
from wtforms.validators import DataRequired, Optional, NumberRange, Length
from datetime import datetime, date
from app.models.dashboard_are import TypeAlerte, SeveriteAlerte, CategorieIndicateur
from app.utils.permissions import get_operateur_choices
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
        self.operateur_id.choices.extend(get_operateur_choices())


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