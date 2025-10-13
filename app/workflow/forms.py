"""
Formulaires pour le système de workflow de validation
"""
from flask_wtf import FlaskForm
from wtforms import (
    SelectField, TextAreaField, StringField, IntegerField, 
    BooleanField, SubmitField, HiddenField
)
from wtforms.validators import DataRequired, Length, Optional, NumberRange
from app.models.workflow import TypeRapport, StatutWorkflow
from app.utils.helpers import safe_int_coerce


class SoumissionRapportForm(FlaskForm):
    """Formulaire pour soumettre un rapport à la validation"""
    rapport_id = HiddenField('ID Rapport', validators=[DataRequired()])
    type_rapport = SelectField(
        'Type de Rapport',
        choices=[(t.value, t.value.replace('_', ' ').title()) for t in TypeRapport],
        validators=[DataRequired(message="Veuillez sélectionner un type de rapport")]
    )
    commentaires = TextAreaField(
        'Commentaires de soumission',
        validators=[Length(max=1000)],
        render_kw={"placeholder": "Commentaires optionnels pour les validateurs..."}
    )
    priorite = SelectField(
        'Priorité',
        choices=[
            (1, 'Normale'),
            (2, 'Urgente'), 
            (3, 'Critique')
        ],
        coerce=safe_int_coerce,
        default=1
    )
    submit = SubmitField('Soumettre pour validation')


class ValidationRapportForm(FlaskForm):
    """Formulaire pour valider un rapport"""
    validation_id = HiddenField('ID Validation', validators=[DataRequired()])
    action = SelectField(
        'Action',
        choices=[
            ('valider', 'Valider le rapport'),
            ('rejeter', 'Rejeter le rapport'),
            ('demander_modification', 'Demander des modifications')
        ],
        validators=[DataRequired(message="Veuillez sélectionner une action")]
    )
    commentaires = TextAreaField(
        'Commentaires',
        validators=[DataRequired(message="Les commentaires sont obligatoires")],
        render_kw={"placeholder": "Détaillez votre décision..."}
    )
    signature_electronique = StringField(
        'Signature électronique',
        validators=[Length(max=255)],
        render_kw={"placeholder": "Votre signature (optionnel)"}
    )
    submit = SubmitField('Confirmer la décision')


class RechercheValidationsForm(FlaskForm):
    """Formulaire de recherche et filtrage des validations"""
    type_rapport = SelectField(
        'Type de Rapport',
        choices=[('', 'Tous les types')] + [(t.value, t.value.replace('_', ' ').title()) for t in TypeRapport],
        default=''
    )
    statut = SelectField(
        'Statut',
        choices=[('', 'Tous les statuts')] + [(s.value, s.value.replace('_', ' ').title()) for s in StatutWorkflow],
        default=''
    )
    validateur = SelectField(
        'Validateur',
        choices=[('', 'Tous les validateurs')],  # Sera rempli dynamiquement
        default=''
    )
    priorite = SelectField(
        'Priorité',
        choices=[
            ('', 'Toutes les priorités'),
            (1, 'Normale'),
            (2, 'Urgente'),
            (3, 'Critique')
        ],
        coerce=str,
        default=''
    )
    expiration = SelectField(
        'Expiration',
        choices=[
            ('', 'Toutes'),
            ('expire', 'Expirées'),
            ('bientot_expire', 'Bientôt expirées (< 24h)'),
            ('en_cours', 'En cours')
        ],
        default=''
    )
    submit = SubmitField('Filtrer')


class ConfigurationWorkflowForm(FlaskForm):
    """Formulaire pour configurer un workflow"""
    type_rapport = SelectField(
        'Type de Rapport',
        choices=[(t.value, t.value.replace('_', ' ').title()) for t in TypeRapport],
        validators=[DataRequired()]
    )
    nom = StringField(
        'Nom du Workflow',
        validators=[DataRequired(), Length(min=3, max=100)]
    )
    description = TextAreaField(
        'Description',
        validators=[Length(max=500)]
    )
    delai_validation = IntegerField(
        'Délai de validation (heures)',
        validators=[DataRequired(), NumberRange(min=1, max=720)],
        default=72
    )
    validateurs_requis = IntegerField(
        'Nombre de validateurs requis',
        validators=[DataRequired(), NumberRange(min=1, max=10)],
        default=1
    )
    rappel_automatique = BooleanField(
        'Rappels automatiques',
        default=True
    )
    submit = SubmitField('Enregistrer la configuration')


class ValidateurDesigneForm(FlaskForm):
    """Formulaire pour désigner un validateur"""
    operateur_id = SelectField(
        'Opérateur',
        choices=[],  # Sera rempli dynamiquement
        validators=[DataRequired()],
        coerce=safe_int_coerce
    )
    validateur_id = SelectField(
        'Validateur',
        choices=[],  # Sera rempli dynamiquement
        validators=[DataRequired()],
        coerce=safe_int_coerce
    )
    type_rapport = SelectField(
        'Type de Rapport',
        choices=[(t.value, t.value.replace('_', ' ').title()) for t in TypeRapport],
        validators=[DataRequired()]
    )
    niveau_validation = IntegerField(
        'Niveau de validation',
        validators=[DataRequired(), NumberRange(min=1, max=10)],
        default=1
    )
    peut_valider_urgent = BooleanField(
        'Peut valider les rapports urgents',
        default=False
    )
    delai_max_validation = IntegerField(
        'Délai maximum de validation (heures)',
        validators=[Optional(), NumberRange(min=1, max=720)]
    )
    submit = SubmitField('Désigner le validateur')


class CommentaireValidationForm(FlaskForm):
    """Formulaire pour ajouter un commentaire à une validation"""
    validation_id = HiddenField('ID Validation', validators=[DataRequired()])
    commentaire = TextAreaField(
        'Commentaire',
        validators=[DataRequired(), Length(min=10, max=1000)],
        render_kw={"placeholder": "Ajoutez votre commentaire..."}
    )
    submit = SubmitField('Ajouter le commentaire')


class RelanceValidationForm(FlaskForm):
    """Formulaire pour relancer une validation"""
    validation_id = HiddenField('ID Validation', validators=[DataRequired()])
    message_relance = TextAreaField(
        'Message de relance',
        validators=[Length(max=500)],
        render_kw={"placeholder": "Message personnalisé pour la relance (optionnel)..."}
    )
    submit = SubmitField('Envoyer la relance')