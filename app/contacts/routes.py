"""
Routes pour l'authentification des contacts
"""
from flask import render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, current_user, login_required
from urllib.parse import urlparse
from app.contacts import bp
from app.contacts.forms import ContactLoginForm, ContactRegistrationForm
from app.models import Contact
from app.extensions import db
from datetime import datetime


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Page de connexion pour les contacts"""
    if current_user.is_authenticated and hasattr(current_user, 'username'):
        return redirect(url_for('contacts.dashboard'))
    
    form = ContactLoginForm()
    if form.validate_on_submit():
        contact = Contact.query.filter_by(username=form.username.data).first()
        
        if contact and contact.check_password(form.password.data) and contact.is_active:
            # Mise à jour de la dernière connexion
            contact.last_login = datetime.utcnow()
            db.session.commit()
            
            # Connexion du contact
            login_user(contact, remember=form.remember_me.data)
            flash('Connexion réussie !', 'success')
            
            next_page = request.args.get('next')
            if not next_page or urlparse(next_page).netloc != '':
                next_page = url_for('contacts.dashboard')
            return redirect(next_page)
        else:
            flash('Nom d\'utilisateur ou mot de passe incorrect, ou compte inactif', 'error')
    
    return render_template('contacts/login.html', form=form)


@bp.route('/register', methods=['GET', 'POST'])
def register():
    """Page d'enregistrement pour les contacts"""
    if current_user.is_authenticated and hasattr(current_user, 'username'):
        return redirect(url_for('contacts.dashboard'))
    
    form = ContactRegistrationForm()
    if form.validate_on_submit():
        contact = Contact(
            username=form.username.data,
            email=form.email.data,
            is_active=True
        )
        contact.set_password(form.password.data)
        
        try:
            db.session.add(contact)
            db.session.commit()
            flash('Enregistrement réussi ! Vous pouvez maintenant vous connecter.', 'success')
            return redirect(url_for('contacts.login'))
        except Exception as e:
            db.session.rollback()
            flash('Erreur lors de l\'enregistrement. Veuillez réessayer.', 'error')
    
    return render_template('contacts/register.html', form=form)


@bp.route('/logout')
@login_required
def logout():
    """Déconnexion des contacts"""
    logout_user()
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('contacts.login'))


@bp.route('/dashboard')
@login_required
def dashboard():
    """Tableau de bord pour les contacts connectés"""
    # Vérifier que l'utilisateur connecté est bien un contact
    if not hasattr(current_user, 'username'):
        flash('Accès non autorisé', 'error')
        return redirect(url_for('auth.login'))
    
    return render_template('contacts/dashboard.html', contact=current_user)


@bp.route('/profile')
@login_required
def profile():
    """Profil du contact"""
    if not hasattr(current_user, 'username'):
        flash('Accès non autorisé', 'error')
        return redirect(url_for('auth.login'))
    
    return render_template('contacts/profile.html', contact=current_user)