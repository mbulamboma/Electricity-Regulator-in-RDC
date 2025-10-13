"""
Formulaires pour l'administration
"""
from flask_wtf import FlaskForm
from wtforms import (
    StringField, BooleanField, IntegerField, SelectField, 
    TextAreaField, SubmitField, DecimalField
)
from wtforms.validators import DataRequired, Email, NumberRange, Length, Optional


class ConfigurationForm(FlaskForm):
    """Formulaire de configuration système"""
    
    # Mode maintenance
    maintenance_mode = BooleanField('Mode maintenance', default=False)
    
    # Configuration des sauvegardes
    backup_retention_days = IntegerField(
        'Rétention des sauvegardes (jours)',
        validators=[DataRequired(), NumberRange(min=1, max=365)],
        default=30
    )
    
    auto_backup_enabled = BooleanField('Sauvegarde automatique', default=False)
    auto_backup_frequency = SelectField(
        'Fréquence sauvegarde auto',
        choices=[
            ('daily', 'Quotidienne'),
            ('weekly', 'Hebdomadaire'),
            ('monthly', 'Mensuelle')
        ],
        default='weekly'
    )
    
    # Alertes
    alert_email = StringField(
        'Email d\'alerte',
        validators=[Optional(), Email()],
        description='Email pour recevoir les alertes système'
    )
    
    # Limites système
    max_file_size = IntegerField(
        'Taille max fichier (MB)',
        validators=[DataRequired(), NumberRange(min=1, max=100)],
        default=16
    )
    
    report_deadline_days = IntegerField(
        'Délai rapport (jours)',
        validators=[DataRequired(), NumberRange(min=1, max=30)],
        default=5,
        description='Nombre de jours après fin de mois pour soumettre rapport'
    )
    
    # Paramètres de performance
    session_timeout_minutes = IntegerField(
        'Timeout session (minutes)',
        validators=[Optional(), NumberRange(min=30, max=480)],
        default=120
    )
    
    pagination_per_page = IntegerField(
        'Éléments par page',
        validators=[DataRequired(), NumberRange(min=10, max=100)],
        default=20
    )
    
    submit = SubmitField('Sauvegarder Configuration')


class BackupForm(FlaskForm):
    """Formulaire de sauvegarde"""
    
    backup_type = SelectField(
        'Type de sauvegarde',
        choices=[
            ('database', 'Base de données uniquement'),
            ('files', 'Fichiers uniquement'),
            ('complete', 'Complète (BDD + Fichiers)')
        ],
        validators=[DataRequired()],
        default='complete'
    )
    
    include_files = BooleanField(
        'Inclure les fichiers uploadés',
        default=True,
        description='Inclure les documents et images dans la sauvegarde'
    )
    
    compress = BooleanField(
        'Compresser la sauvegarde',
        default=True,
        description='Créer un fichier ZIP compressé'
    )
    
    description = TextAreaField(
        'Description',
        validators=[Optional(), Length(max=500)],
        description='Description optionnelle de cette sauvegarde'
    )
    
    submit = SubmitField('Créer Sauvegarde')


class AlertConfigForm(FlaskForm):
    """Configuration des alertes"""
    
    # Alertes de rapport
    missing_report_alert = BooleanField(
        'Alerte rapports manquants',
        default=True
    )
    
    missing_report_days = IntegerField(
        'Délai alerte rapport (jours)',
        validators=[NumberRange(min=1, max=90)],
        default=7
    )
    
    # Alertes de production
    low_production_alert = BooleanField(
        'Alerte production faible',
        default=True
    )
    
    low_production_threshold = DecimalField(
        'Seuil production faible (%)',
        validators=[NumberRange(min=0, max=100)],
        default=70.0,
        description='% du facteur de charge en dessous duquel alerter'
    )
    
    # Alertes système
    disk_space_alert = BooleanField(
        'Alerte espace disque',
        default=True
    )
    
    disk_space_threshold = IntegerField(
        'Seuil espace disque (%)',
        validators=[NumberRange(min=50, max=95)],
        default=85,
        description='% d\'utilisation disque au-dessus duquel alerter'
    )
    
    # Notifications
    email_notifications = BooleanField(
        'Notifications email',
        default=True
    )
    
    dashboard_notifications = BooleanField(
        'Notifications dashboard',
        default=True
    )
    
    submit = SubmitField('Sauvegarder Alertes')


class MaintenanceForm(FlaskForm):
    """Formulaire de maintenance système"""
    
    action = SelectField(
        'Action de maintenance',
        choices=[
            ('cleanup_logs', 'Nettoyer les logs'),
            ('optimize_db', 'Optimiser la base de données'),
            ('clear_cache', 'Vider le cache'),
            ('check_integrity', 'Vérifier l\'intégrité des données'),
            ('update_stats', 'Mettre à jour les statistiques')
        ],
        validators=[DataRequired()]
    )
    
    confirm = BooleanField(
        'Confirmer l\'action',
        validators=[DataRequired()],
        description='Je confirme vouloir exécuter cette action de maintenance'
    )
    
    submit = SubmitField('Exécuter Maintenance')


class UserManagementForm(FlaskForm):
    """Formulaire de gestion des utilisateurs"""
    
    action = SelectField(
        'Action',
        choices=[
            ('activate', 'Activer'),
            ('deactivate', 'Désactiver'),
            ('reset_password', 'Réinitialiser mot de passe'),
            ('change_role', 'Changer le rôle')
        ],
        validators=[DataRequired()]
    )
    
    new_role = SelectField(
        'Nouveau rôle',
        choices=[
            ('utilisateur_operateur', 'Utilisateur Opérateur'),
            ('admin_operateur', 'Admin Opérateur'),
            ('super_admin', 'Super Administrateur')
        ],
        validators=[Optional()]
    )
    
    reason = TextAreaField(
        'Raison',
        validators=[Optional(), Length(max=500)],
        description='Raison de cette action (optionnel)'
    )
    
    submit = SubmitField('Appliquer Action')