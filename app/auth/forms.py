"""
Formulaires d'authentification
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Optional
from app.models import User, Operateur


class LoginForm(FlaskForm):
    """Formulaire de connexion"""
    username = StringField('Nom d\'utilisateur', validators=[DataRequired()])
    password = PasswordField('Mot de passe', validators=[DataRequired()])
    remember_me = BooleanField('Se souvenir de moi')
    submit = SubmitField('Se connecter')


class RegistrationForm(FlaskForm):
    """Formulaire d'inscription (super admin seulement)"""
    username = StringField('Nom d\'utilisateur', validators=[
        DataRequired(),
        Length(min=3, max=80, message='Le nom d\'utilisateur doit contenir entre 3 et 80 caractères')
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message='Adresse email invalide')
    ])
    nom = StringField('Nom', validators=[DataRequired()])
    prenom = StringField('Prénom', validators=[DataRequired()])
    telephone = StringField('Téléphone', validators=[Optional()])
    role = SelectField('Rôle', choices=[
        ('super_admin', 'Super Administrateur'),
        ('admin_operateur', 'Administrateur d\'Opérateur'),
        ('utilisateur_operateur', 'Utilisateur d\'Opérateur')
    ], validators=[DataRequired()])
    operateur_id = SelectField('Opérateur', coerce=lambda x: int(x) if x else None, validators=[Optional()])
    password = PasswordField('Mot de passe', validators=[
        DataRequired(),
        Length(min=6, message='Le mot de passe doit contenir au moins 6 caractères')
    ])
    password2 = PasswordField('Confirmer le mot de passe', validators=[
        DataRequired(),
        EqualTo('password', message='Les mots de passe doivent correspondre')
    ])
    submit = SubmitField('Créer le compte')
    
    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        # Charger les opérateurs actifs pour la liste déroulante
        self.operateur_id.choices = [(0, 'Aucun opérateur')] + [
            (o.id, o.nom) for o in Operateur.query.filter_by(actif=True).all()
        ]
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Ce nom d\'utilisateur est déjà utilisé.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Cette adresse email est déjà utilisée.')
    
    def validate_operateur_id(self, operateur_id):
        if self.role.data in ['admin_operateur', 'utilisateur_operateur']:
            if not operateur_id.data or operateur_id.data == 0:
                raise ValidationError('Un opérateur doit être sélectionné pour ce rôle.')


class UserEditForm(FlaskForm):
    """Formulaire d'édition d'utilisateur"""
    username = StringField('Nom d\'utilisateur', validators=[
        DataRequired(),
        Length(min=3, max=80, message='Le nom d\'utilisateur doit contenir entre 3 et 80 caractères')
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message='Adresse email invalide')
    ])
    nom = StringField('Nom', validators=[DataRequired()])
    prenom = StringField('Prénom', validators=[DataRequired()])
    telephone = StringField('Téléphone', validators=[Optional()])
    role = SelectField('Rôle', choices=[
        ('super_admin', 'Super Administrateur'),
        ('admin_operateur', 'Administrateur d\'Opérateur'),
        ('utilisateur_operateur', 'Utilisateur d\'Opérateur')
    ], validators=[DataRequired()])
    operateur_id = SelectField('Opérateur', coerce=lambda x: int(x) if x else None, validators=[Optional()])
    is_active = BooleanField('Compte actif')
    submit = SubmitField('Mettre à jour')
    
    def __init__(self, user, *args, **kwargs):
        super(UserEditForm, self).__init__(*args, **kwargs)
        self.user = user
        # Charger les opérateurs actifs pour la liste déroulante
        self.operateur_id.choices = [(0, 'Aucun opérateur')] + [
            (o.id, o.nom) for o in Operateur.query.filter_by(actif=True).all()
        ]
    
    def validate_username(self, username):
        if username.data != self.user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Ce nom d\'utilisateur est déjà utilisé.')
    
    def validate_email(self, email):
        if email.data != self.user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Cette adresse email est déjà utilisée.')


class ChangePasswordForm(FlaskForm):
    """Formulaire de changement de mot de passe"""
    current_password = PasswordField('Mot de passe actuel', validators=[DataRequired()])
    new_password = PasswordField('Nouveau mot de passe', validators=[
        DataRequired(),
        Length(min=6, message='Le mot de passe doit contenir au moins 6 caractères')
    ])
    new_password2 = PasswordField('Confirmer le nouveau mot de passe', validators=[
        DataRequired(),
        EqualTo('new_password', message='Les mots de passe doivent correspondre')
    ])
    submit = SubmitField('Changer le mot de passe')


class ProfileForm(FlaskForm):
    """Formulaire de profil utilisateur"""
    nom = StringField('Nom', validators=[DataRequired()])
    prenom = StringField('Prénom', validators=[DataRequired()])
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message='Adresse email invalide')
    ])
    telephone = StringField('Téléphone', validators=[Optional()])
    submit = SubmitField('Mettre à jour le profil')
    
    def __init__(self, user, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.user = user
    
    def validate_email(self, email):
        if email.data != self.user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Cette adresse email est déjà utilisée.')


class ResetPasswordRequestForm(FlaskForm):
    """Formulaire de demande de réinitialisation de mot de passe"""
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Demander la réinitialisation')


class ResetPasswordForm(FlaskForm):
    """Formulaire de réinitialisation de mot de passe"""
    password = PasswordField('Nouveau mot de passe', validators=[
        DataRequired(),
        Length(min=6, message='Le mot de passe doit contenir au moins 6 caractères')
    ])
    password2 = PasswordField('Confirmer le mot de passe', validators=[
        DataRequired(),
        EqualTo('password', message='Les mots de passe doivent correspondre')
    ])
    submit = SubmitField('Réinitialiser le mot de passe')
    password = PasswordField('Mot de passe', validators=[
        DataRequired(),
        Length(min=6, message='Le mot de passe doit contenir au moins 6 caractères')
    ])
    password2 = PasswordField('Confirmer le mot de passe', validators=[
        DataRequired(),
        EqualTo('password', message='Les mots de passe doivent correspondre')
    ])
    submit = SubmitField('S\'inscrire')
    
    def validate_username(self, username):
        """Vérifier que le nom d'utilisateur n'existe pas déjà"""
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Ce nom d\'utilisateur est déjà utilisé. Veuillez en choisir un autre.')
    
    def validate_email(self, email):
        """Vérifier que l'email n'existe pas déjà"""
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Cette adresse email est déjà utilisée.')
