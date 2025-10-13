"""
Formulaires pour le module de notifications et messagerie
"""
from flask_wtf import FlaskForm
from wtforms import (StringField, TextAreaField, SelectField, BooleanField, 
                     HiddenField, IntegerField)
from wtforms.validators import DataRequired, Optional, Length, NumberRange
from wtforms.widgets import TextArea


class MessageInterneForm(FlaskForm):
    """Formulaire pour créer un message interne"""
    
    destinataire_id = SelectField('Destinataire', coerce=lambda x: int(x) if x else None, validators=[DataRequired()])
    sujet = StringField('Sujet', validators=[DataRequired(), Length(max=300)])
    contenu = TextAreaField('Message', validators=[DataRequired()], widget=TextArea())
    priorite = SelectField('Priorité', choices=[
        (1, 'Normale'),
        (2, 'Importante'),
        (3, 'Urgente')
    ], coerce=lambda x: int(x) if x else None, default=1)
    
    # Pour les réponses
    message_parent_id = HiddenField()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Les choix de destinataires seront remplis dynamiquement dans la vue


class ReponseMessageForm(FlaskForm):
    """Formulaire pour répondre à un message"""
    
    contenu = TextAreaField('Réponse', validators=[DataRequired()], widget=TextArea())
    message_parent_id = HiddenField(validators=[DataRequired()])


class FiltreNotificationsForm(FlaskForm):
    """Formulaire de filtrage des notifications"""
    
    type_notification = SelectField('Type', choices=[
        ('', 'Tous les types'),
        ('rappel_rapport', 'Rappels de rapport'),
        ('validation_rapport', 'Validations'),
        ('rejet_rapport', 'Rejets'),
        ('alerte_donnees', 'Alertes données'),
        ('message_systeme', 'Messages système'),
        ('maintenance_planifiee', 'Maintenance'),
        ('incident_technique', 'Incidents'),
        ('nouvelle_reglementation', 'Réglementations')
    ], validators=[Optional()])
    
    priorite = SelectField('Priorité', choices=[
        ('', 'Toutes priorités'),
        ('1', 'Normale'),
        ('2', 'Importante'),
        ('3', 'Urgente')
    ], validators=[Optional()])
    
    statut = SelectField('Statut', choices=[
        ('', 'Toutes'),
        ('non_lue', 'Non lues'),
        ('lue', 'Lues'),
        ('archivee', 'Archivées')
    ], validators=[Optional()])


class FiltreMessagesForm(FlaskForm):
    """Formulaire de filtrage des messages"""
    
    type_message = SelectField('Type', choices=[
        ('', 'Tous'),
        ('recus', 'Messages reçus'),
        ('envoyes', 'Messages envoyés'),
        ('archives', 'Messages archivés')
    ], validators=[Optional()])
    
    priorite = SelectField('Priorité', choices=[
        ('', 'Toutes priorités'),
        ('1', 'Normale'),
        ('2', 'Importante'),
        ('3', 'Urgente')
    ], validators=[Optional()])
    
    statut = SelectField('Statut', choices=[
        ('', 'Tous'),
        ('non_lu', 'Non lus'),
        ('lu', 'Lus')
    ], validators=[Optional()])
    
    recherche = StringField('Recherche', validators=[Optional(), Length(max=200)], 
                           render_kw={'placeholder': 'Sujet ou contenu...'})


class PreferencesNotificationForm(FlaskForm):
    """Formulaire pour les préférences de notifications"""
    
    # Préférences par type
    rappel_rapport = BooleanField('Rappels de soumission de rapports')
    validation_rapport = BooleanField('Notifications de validation')
    rejet_rapport = BooleanField('Notifications de rejet')
    alerte_donnees = BooleanField('Alertes sur données anormales')
    message_systeme = BooleanField('Messages système')
    maintenance_planifiee = BooleanField('Maintenance programmée')
    incident_technique = BooleanField('Incidents techniques')
    nouvelle_reglementation = BooleanField('Nouvelles réglementations')
    
    # Préférences globales
    notifications_email = BooleanField('Recevoir par email')
    notifications_browser = BooleanField('Notifications navigateur')
    digest_quotidien = BooleanField('Résumé quotidien')
    digest_hebdomadaire = BooleanField('Résumé hebdomadaire')


class CreerNotificationForm(FlaskForm):
    """Formulaire pour créer une notification (admin)"""
    
    user_id = SelectField('Utilisateur', coerce=lambda x: int(x) if x else None, validators=[DataRequired()])
    type_notification = SelectField('Type', choices=[
        ('rappel_rapport', 'Rappel de rapport'),
        ('validation_rapport', 'Validation'),
        ('rejet_rapport', 'Rejet'),
        ('alerte_donnees', 'Alerte données'),
        ('message_systeme', 'Message système'),
        ('maintenance_planifiee', 'Maintenance'),
        ('incident_technique', 'Incident'),
        ('nouvelle_reglementation', 'Réglementation')
    ], validators=[DataRequired()])
    
    titre = StringField('Titre', validators=[DataRequired(), Length(max=200)])
    message = TextAreaField('Message', validators=[DataRequired()], widget=TextArea())
    
    priorite = SelectField('Priorité', choices=[
        (1, 'Normale'),
        (2, 'Importante'),
        (3, 'Urgente')
    ], coerce=lambda x: int(x) if x else None, default=1)
    
    url_action = StringField('URL d\'action', validators=[Optional(), Length(max=500)],
                            render_kw={'placeholder': 'URL optionnelle vers une action'})
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Les choix d'utilisateurs seront remplis dynamiquement dans la vue


class CreerTemplateForm(FlaskForm):
    """Formulaire pour créer un template de notification"""
    
    code = StringField('Code unique', validators=[DataRequired(), Length(max=100)])
    nom = StringField('Nom du template', validators=[DataRequired(), Length(max=200)])
    
    type_notification = SelectField('Type', choices=[
        ('rappel_rapport', 'Rappel de rapport'),
        ('validation_rapport', 'Validation'),
        ('rejet_rapport', 'Rejet'),
        ('alerte_donnees', 'Alerte données'),
        ('message_systeme', 'Message système'),
        ('maintenance_planifiee', 'Maintenance'),
        ('incident_technique', 'Incident'),
        ('nouvelle_reglementation', 'Réglementation')
    ], validators=[DataRequired()])
    
    titre_template = StringField('Template du titre', validators=[DataRequired(), Length(max=300)],
                                render_kw={'placeholder': 'Ex: Rappel: {rapport_type} pour {operateur}'})
    
    message_template = TextAreaField('Template du message', validators=[DataRequired()], 
                                    widget=TextArea(),
                                    render_kw={'placeholder': 'Ex: Votre rapport {rapport_type} pour la période {periode} est en retard.'})
    
    priorite_defaut = SelectField('Priorité par défaut', choices=[
        (1, 'Normale'),
        (2, 'Importante'),
        (3, 'Urgente')
    ], coerce=lambda x: int(x) if x else None, default=1)
    
    url_template = StringField('Template d\'URL', validators=[Optional(), Length(max=500)],
                              render_kw={'placeholder': 'Ex: /rapports/{rapport_id}'})
    
    actif = BooleanField('Template actif', default=True)