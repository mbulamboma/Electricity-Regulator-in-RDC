"""
Formulaires pour l'authentification des contacts
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length
from app.models import Contact


class ContactLoginForm(FlaskForm):
    """Formulaire de connexion pour les contacts"""
    username = StringField('Nom d\'utilisateur', validators=[
        DataRequired(message='Le nom d\'utilisateur est requis')
    ])
    password = PasswordField('Mot de passe', validators=[
        DataRequired(message='Le mot de passe est requis')
    ])
    remember_me = BooleanField('Se souvenir de moi')
    submit = SubmitField('Se connecter')


class ContactRegistrationForm(FlaskForm):
    """Formulaire d'enregistrement pour les contacts"""
    username = StringField('Nom d\'utilisateur', validators=[
        DataRequired(message='Le nom d\'utilisateur est requis'),
        Length(min=3, max=80, message='Le nom d\'utilisateur doit contenir entre 3 et 80 caractères')
    ])
    email = StringField('Email', validators=[
        DataRequired(message='L\'email est requis'),
        Email(message='Adresse email invalide')
    ])
    password = PasswordField('Mot de passe', validators=[
        DataRequired(message='Le mot de passe est requis'),
        Length(min=6, message='Le mot de passe doit contenir au moins 6 caractères')
    ])
    submit = SubmitField('S\'enregistrer')

    def validate_username(self, username):
        """Valider l'unicité du nom d'utilisateur"""
        from wtforms.validators import ValidationError
        contact = Contact.query.filter_by(username=username.data).first()
        if contact:
            raise ValidationError('Ce nom d\'utilisateur est déjà utilisé')

    def validate_email(self, email):
        """Valider l'unicité de l'email"""
        from wtforms.validators import ValidationError
        contact = Contact.query.filter_by(email=email.data).first()
        if contact:
            raise ValidationError('Cette adresse email est déjà utilisée')