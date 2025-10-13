"""
Routes d'authentification avec système de permissions
"""
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from app.extensions import db
from app.models import User, Operateur
from app.auth.forms import (LoginForm, RegistrationForm, UserEditForm, 
                           ChangePasswordForm, ProfileForm)
from app.utils.decorators import super_admin_required, active_user_required

auth = Blueprint('auth', __name__, url_prefix='/auth')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    """Page de connexion"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash('Votre compte a été désactivé. Contactez l\'administrateur.', 'danger')
                return render_template('auth/login.html', form=form)
            
            if not user.actif:
                flash('Votre compte a été supprimé. Contactez l\'administrateur.', 'danger')
                return render_template('auth/login.html', form=form)
            
            login_user(user, remember=form.remember_me.data)
            user.update_last_login()
            
            # Message de bienvenue personnalisé selon le rôle
            if user.is_super_admin():
                flash(f'Bienvenue Super Administrateur {user.prenom or user.username}!', 'success')
            elif user.is_admin_operateur():
                operateur_nom = user.operateur.nom if user.operateur else "N/A"
                flash(f'Bienvenue Administrateur de {operateur_nom}, {user.prenom or user.username}!', 'success')
            else:
                operateur_nom = user.operateur.nom if user.operateur else "N/A"
                flash(f'Bienvenue {user.prenom or user.username} ({operateur_nom})!', 'success')
            
            # Redirection vers la page demandée ou le tableau de bord
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('main.dashboard'))
        else:
            flash('Nom d\'utilisateur ou mot de passe invalide.', 'danger')
    
    return render_template('auth/login.html', form=form)


@auth.route('/register', methods=['GET', 'POST'])
@super_admin_required
def register():
    """Page d'inscription (super admin seulement)"""
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            # Gérer l'opérateur
            operateur_id = form.operateur_id.data if form.operateur_id.data != 0 else None
            
            # Créer le nouvel utilisateur
            user = User(
                username=form.username.data,
                email=form.email.data,
                nom=form.nom.data,
                prenom=form.prenom.data,
                telephone=form.telephone.data,
                role=form.role.data,
                operateur_id=operateur_id,
                is_active=True
            )
            user.set_password(form.password.data)
            user.save()
            
            operateur_info = f" ({user.operateur.nom})" if user.operateur else ""
            flash(f'Utilisateur {user.username} créé avec succès{operateur_info}!', 'success')
            return redirect(url_for('auth.users'))
        except Exception as e:
            flash(f'Erreur lors de la création de l\'utilisateur: {str(e)}', 'danger')
    elif request.method == 'POST':
        # Le formulaire a été soumis mais n'est pas valide
        flash('Le formulaire contient des erreurs. Veuillez corriger et réessayer.', 'warning')
    
    return render_template('auth/register.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    """Déconnexion"""
    logout_user()
    flash('Vous avez été déconnecté avec succès.', 'info')
    return redirect(url_for('main.index'))


@auth.route('/profile', methods=['GET', 'POST'])
@active_user_required
def profile():
    """Page de profil utilisateur"""
    form = ProfileForm(current_user)
    change_password_form = ChangePasswordForm()
    
    if form.validate_on_submit() and form.submit.data:
        current_user.nom = form.nom.data
        current_user.prenom = form.prenom.data
        current_user.email = form.email.data
        current_user.telephone = form.telephone.data
        db.session.commit()
        flash('Votre profil a été mis à jour avec succès.', 'success')
        return redirect(url_for('auth.profile'))
    
    if change_password_form.validate_on_submit() and change_password_form.submit.data:
        if current_user.check_password(change_password_form.current_password.data):
            current_user.set_password(change_password_form.new_password.data)
            db.session.commit()
            flash('Votre mot de passe a été changé avec succès.', 'success')
            return redirect(url_for('auth.profile'))
        else:
            flash('Mot de passe actuel incorrect.', 'danger')
    
    # Pré-remplir le formulaire avec les données actuelles
    if request.method == 'GET':
        form.nom.data = current_user.nom
        form.prenom.data = current_user.prenom
        form.email.data = current_user.email
        form.telephone.data = current_user.telephone
    
    return render_template('auth/profile.html', form=form, 
                         change_password_form=change_password_form, user=current_user)


@auth.route('/users')
@super_admin_required
def users():
    """Liste des utilisateurs (super admin seulement)"""
    page = request.args.get('page', 1, type=int)
    users_query = User.query.join(Operateur, User.operateur_id == Operateur.id, isouter=True)\
                            .add_columns(Operateur.nom.label('operateur_nom'))\
                            .filter(User.actif == True)
    
    users = users_query.paginate(page=page, per_page=20, error_out=False)
    
    return render_template('auth/users.html', users=users)


@auth.route('/user/<int:user_id>/edit', methods=['GET', 'POST'])
@super_admin_required
def edit_user(user_id):
    """Éditer un utilisateur (super admin seulement)"""
    user = User.query.get_or_404(user_id)
    form = UserEditForm(user)
    
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.nom = form.nom.data
        user.prenom = form.prenom.data
        user.telephone = form.telephone.data
        user.role = form.role.data
        user.operateur_id = form.operateur_id.data if form.operateur_id.data != 0 else None
        user.is_active = form.is_active.data
        db.session.commit()
        
        flash(f'Utilisateur {user.username} mis à jour avec succès.', 'success')
        return redirect(url_for('auth.users'))
    
    # Pré-remplir le formulaire
    if request.method == 'GET':
        form.username.data = user.username
        form.email.data = user.email
        form.nom.data = user.nom
        form.prenom.data = user.prenom
        form.telephone.data = user.telephone
        form.role.data = user.role
        form.operateur_id.data = user.operateur_id or 0
        form.is_active.data = user.is_active
    
    return render_template('auth/edit_user.html', form=form, user=user)


@auth.route('/user/<int:user_id>/toggle_active')
@super_admin_required
def toggle_user_active(user_id):
    """Activer/désactiver un utilisateur"""
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('Vous ne pouvez pas désactiver votre propre compte.', 'warning')
        return redirect(url_for('auth.users'))
    
    user.is_active = not user.is_active
    db.session.commit()
    
    status = "activé" if user.is_active else "désactivé"
    flash(f'Utilisateur {user.username} {status} avec succès.', 'success')
    
    return redirect(url_for('auth.users'))


@auth.route('/user/<int:user_id>/delete')
@super_admin_required
def delete_user(user_id):
    """Supprimer un utilisateur (soft delete)"""
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('Vous ne pouvez pas supprimer votre propre compte.', 'warning')
        return redirect(url_for('auth.users'))
    
    user.soft_delete()
    flash(f'Utilisateur {user.username} supprimé avec succès.', 'success')
    
    return redirect(url_for('auth.users'))


@auth.route('/forbidden')
def forbidden():
    """Page d'erreur 403 - Accès interdit"""
    return render_template('auth/forbidden.html'), 403