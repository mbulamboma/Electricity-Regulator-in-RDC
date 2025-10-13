"""
Formulaires pour la gestion des opérateurs
"""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, FloatField, IntegerField, DateField, FieldList, FormField
from wtforms.validators import DataRequired, Email, Optional, Length, NumberRange
from wtforms.widgets import TextArea


class ContactForm(FlaskForm):
    """Formulaire pour un contact"""
    nom = StringField('Nom', validators=[DataRequired(), Length(min=2, max=100)])
    prenom = StringField('Prénom', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    telephone = StringField('Téléphone', validators=[Optional(), Length(max=20)])
    fonction = StringField('Fonction', validators=[Optional(), Length(max=100)])


class OperateurForm(FlaskForm):
    """Formulaire pour créer/modifier un opérateur"""
    
    # Informations de base
    nom = StringField('Nom de l\'opérateur', validators=[DataRequired(), Length(min=2, max=200)])
    sigle = StringField('Sigle', validators=[Optional(), Length(max=50)])
    type_operateur = SelectField('Type d\'opérateur', 
                                choices=[
                                    ('', 'Sélectionner...'),
                                    ('Production', 'Production'),
                                    ('Transport', 'Transport'),
                                    ('Distribution', 'Distribution'),
                                    ('Mixte', 'Mixte')
                                ],
                                validators=[DataRequired()])
    
    # Adresse et contact
    adresse = TextAreaField('Adresse', validators=[Optional()], widget=TextArea())
    ville = StringField('Ville', validators=[Optional(), Length(max=100)])
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
                              ('Mai-Ndombe', 'Mai-Ndombe'),
                              ('Mongala', 'Mongala'),
                              ('Nord-Ubangi', 'Nord-Ubangi'),
                              ('Sud-Ubangi', 'Sud-Ubangi'),
                              ('Tshuapa', 'Tshuapa'),
                              ('Sankuru', 'Sankuru'),
                              ('Lomami', 'Lomami'),
                              ('Kasai', 'Kasaï'),
                              ('Kasai-Central', 'Kasaï-Central'),
                              ('Tanganyika', 'Tanganyika'),
                              ('Haut-Lomami', 'Haut-Lomami'),
                              ('Ituri', 'Ituri'),
                              ('Haut-Uele', 'Haut-Uélé'),
                              ('Bas-Uele', 'Bas-Uélé'),
                              ('Tshopo', 'Tshopo')
                          ],
                          validators=[Optional()])
    telephone = StringField('Téléphone', validators=[Optional(), Length(max=20)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=120)])
    site_web = StringField('Site web', validators=[Optional(), Length(max=200)])
    
    # Informations légales
    numero_licence = StringField('Numéro de licence', validators=[Optional(), Length(max=100)])
    date_licence = DateField('Date de licence', validators=[Optional()])
    statut_licence = SelectField('Statut de licence',
                                choices=[
                                    ('active', 'Active'),
                                    ('suspendue', 'Suspendue'),
                                    ('expiree', 'Expirée')
                                ],
                                default='active',
                                validators=[DataRequired()])
    
    # Informations techniques
    capacite_installee = FloatField('Capacité installée (MW)', 
                                   validators=[Optional(), NumberRange(min=0)])
    zone_couverture = TextAreaField('Zone de couverture', validators=[Optional()], widget=TextArea())
    nombre_clients = IntegerField('Nombre de clients', 
                                 validators=[Optional(), NumberRange(min=0)])
    
    # Notes
    observations = TextAreaField('Observations', validators=[Optional()], widget=TextArea())


class ContactOperateurForm(FlaskForm):
    """Formulaire pour ajouter un contact à un opérateur"""
    contact = FormField(ContactForm)