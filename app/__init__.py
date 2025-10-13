"""
Factory de l'application Flask
"""
import os
from flask import Flask, Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app.config import config
from app.extensions import db, migrate, bcrypt, login_manager, csrf
from app.models import User


def create_app(config_name=None):
    """Créer et configurer l'application Flask"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialiser les extensions
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    
    # Processeur de contexte pour CSRF token
    @app.context_processor
    def inject_csrf_token():
        from flask_wtf.csrf import generate_csrf
        return dict(csrf_token=generate_csrf)
    
    # User loader pour Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import Contact
        # Vérifier si c'est un Contact (préfixé avec "contact_")
        if user_id.startswith('contact_'):
            contact_id = int(user_id.replace('contact_', ''))
            return Contact.query.get(contact_id)
        # Sinon, c'est un User standard
        return User.query.get(int(user_id))
    
    # Enregistrer les blueprints
    from app.auth import auth
    app.register_blueprint(auth)
    
    # Blueprint contacts (représentants d'entreprise)
    from app.contacts import bp as contacts_bp
    app.register_blueprint(contacts_bp)
    
    from app.operateurs import operateurs
    app.register_blueprint(operateurs)
    
    # Blueprint production hydroélectrique
    from app.production_hydro import production_hydro
    app.register_blueprint(production_hydro, url_prefix='/production-hydro')
    
    # Blueprint production thermique
    from app.production_thermique import production_thermique
    app.register_blueprint(production_thermique)
    
    # Blueprint production solaire
    from app.production_solaire import production_solaire
    app.register_blueprint(production_solaire)
    
    # Blueprint transport
    from app.transport.routes import bp as transport_bp
    app.register_blueprint(transport_bp)
    
    # Blueprint distribution
    from app.distribution.routes import bp as distribution_bp
    app.register_blueprint(distribution_bp)
    
    # Blueprint notifications
    from app.notifications.routes import bp as notifications_bp
    app.register_blueprint(notifications_bp)
    
    # Blueprint administration
    from app.admin import admin
    app.register_blueprint(admin, url_prefix='/admin')
    
    # Blueprint ARE (Dashboard stratégique)
    from app.are import bp as are_bp
    app.register_blueprint(are_bp)
    
    from app.are.dashboard import dashboard_bp
    app.register_blueprint(dashboard_bp)
    
    # Blueprint principal (à créer)
    from flask import Blueprint, render_template
    from flask_login import login_required
    
    main = Blueprint('main', __name__)
    
    @main.route('/')
    def index():
        return render_template('base.html', title='Accueil')
    
    @main.route('/dashboard')
    @login_required
    def dashboard():
        from datetime import datetime
        if current_user.role == 'super_admin':
            # Rediriger vers le dashboard admin complet
            return redirect(url_for('admin.dashboard'))
        else:
            # Dashboard simple pour les autres utilisateurs
            current_time = datetime.now()
            return render_template('admin/dashboard.html', 
                                 title='Tableau de bord',
                                 current_time=current_time,
                                 stats={'operateurs_count': 0, 'centrales_count': 0, 'total_production': 0},
                                 production_data={'labels': [], 'data': []},
                                 recent_reports=[],
                                 recent_users=[],
                                 alerts=[])
    
    app.register_blueprint(main)
    
    # Filtres Jinja2 personnalisés
    @app.template_filter('month_name')
    def month_name_filter(month_num):
        """Convertir le numéro de mois en nom français"""
        months = {
            1: 'Janvier', 2: 'Février', 3: 'Mars', 4: 'Avril',
            5: 'Mai', 6: 'Juin', 7: 'Juillet', 8: 'Août',
            9: 'Septembre', 10: 'Octobre', 11: 'Novembre', 12: 'Décembre'
        }
        return months.get(month_num, str(month_num))
    
    @app.template_filter('time_ago')
    def time_ago_filter(date_obj):
        """Convertir une date en temps relatif (il y a X temps)"""
        from datetime import datetime, timedelta
        
        if not date_obj:
            return "Jamais"
        
        # Assurer que c'est un objet datetime
        if isinstance(date_obj, str):
            try:
                date_obj = datetime.fromisoformat(date_obj.replace('Z', '+00:00'))
            except:
                return "Date invalide"
        
        now = datetime.now()
        
        # Si la date est dans le futur, la traiter comme maintenant
        if date_obj > now:
            return "Maintenant"
        
        diff = now - date_obj
        
        # Moins d'une minute
        if diff.total_seconds() < 60:
            return "Il y a quelques secondes"
        
        # Moins d'une heure
        elif diff.total_seconds() < 3600:
            minutes = int(diff.total_seconds() / 60)
            return f"Il y a {minutes} minute{'s' if minutes > 1 else ''}"
        
        # Moins d'un jour
        elif diff.total_seconds() < 86400:
            hours = int(diff.total_seconds() / 3600)
            return f"Il y a {hours} heure{'s' if hours > 1 else ''}"
        
        # Moins d'une semaine
        elif diff.days < 7:
            return f"Il y a {diff.days} jour{'s' if diff.days > 1 else ''}"
        
        # Moins d'un mois
        elif diff.days < 30:
            weeks = int(diff.days / 7)
            return f"Il y a {weeks} semaine{'s' if weeks > 1 else ''}"
        
        # Moins d'une année
        elif diff.days < 365:
            months = int(diff.days / 30)
            return f"Il y a {months} mois"
        
        # Plus d'une année
        else:
            years = int(diff.days / 365)
            return f"Il y a {years} an{'s' if years > 1 else ''}"
    
    @app.template_filter('nl2br')
    def nl2br_filter(text):
        """Convertir les sauts de ligne en balises <br> HTML"""
        if not text:
            return ""
        from markupsafe import Markup
        return Markup(text.replace('\n', '<br>\n'))
    
    # Créer les dossiers nécessaires
    with app.app_context():
        os.makedirs(app.config.get('UPLOAD_FOLDER', 'uploads'), exist_ok=True)
        os.makedirs(os.path.join(app.instance_path), exist_ok=True)
    
    return app
