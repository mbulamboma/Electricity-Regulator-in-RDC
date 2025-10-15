"""
Routes pour le module de notifications et messagerie
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user
from sqlalchemy import func, and_, or_, desc
from datetime import datetime, timedelta
import json

from app.extensions import db
from app.models.notifications import (
    Notification, MessageInterne, TemplateNotification, PreferenceNotification, 
    TypeNotification
)
from app.models.utilisateurs import User
from app.notifications.forms import (
    MessageInterneForm, ReponseMessageForm, FiltreNotificationsForm, 
    FiltreMessagesForm, PreferencesNotificationForm, CreerNotificationForm,
    CreerTemplateForm
)

bp = Blueprint('notifications', __name__, url_prefix='/notifications')


@bp.route('/')
@login_required
def index():
    """Liste des notifications de l'utilisateur"""
    
    # Filtres
    filtre_form = FiltreNotificationsForm(request.args)
    
    # Requête de base
    query = Notification.query.filter_by(user_id=current_user.id, actif=True)
    
    # Application des filtres
    if filtre_form.type_notification.data:
        query = query.filter(Notification.type == TypeNotification(filtre_form.type_notification.data))
    
    if filtre_form.priorite.data:
        query = query.filter(Notification.priorite == int(filtre_form.priorite.data))
    
    if filtre_form.statut.data:
        if filtre_form.statut.data == 'non_lue':
            query = query.filter(Notification.lue == False)
        elif filtre_form.statut.data == 'lue':
            query = query.filter(Notification.lue == True)
        elif filtre_form.statut.data == 'archivee':
            query = query.filter(Notification.archivee == True)
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    notifications = query.order_by(desc(Notification.date_creation)).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Statistiques
    stats = {
        'total': Notification.query.filter_by(user_id=current_user.id, actif=True).count(),
        'non_lues': Notification.query.filter_by(user_id=current_user.id, lue=False, actif=True).count(),
        'importantes': Notification.query.filter_by(user_id=current_user.id, priorite=2, actif=True).count(),
        'urgentes': Notification.query.filter_by(user_id=current_user.id, priorite=3, actif=True).count()
    }
    
    return render_template('notifications/index.html',
                         title="Mes Notifications",
                         notifications=notifications,
                         filtre_form=filtre_form,
                         stats=stats)


@bp.route('/<int:id>/marquer-lu', methods=['POST'])
@login_required
def marquer_lu(id):
    """Marquer une notification comme lue"""
    
    notification = Notification.query.filter_by(
        id=id, user_id=current_user.id
    ).first_or_404()
    
    notification.marquer_comme_lue()
    
    if request.is_json:
        return jsonify({'success': True, 'message': 'Notification marquée comme lue'})
    
    flash('Notification marquée comme lue.', 'success')
    return redirect(request.referrer or url_for('notifications.index'))


@bp.route('/<int:id>/archiver', methods=['POST'])
@login_required
def archiver(id):
    """Archiver une notification"""
    
    notification = Notification.query.filter_by(
        id=id, user_id=current_user.id
    ).first_or_404()
    
    notification.archiver()
    
    if request.is_json:
        return jsonify({'success': True, 'message': 'Notification archivée'})
    
    flash('Notification archivée.', 'success')
    return redirect(request.referrer or url_for('notifications.index'))


@bp.route('/marquer-toutes-lues', methods=['POST'])
@login_required
def marquer_toutes_lues():
    """Marquer toutes les notifications comme lues"""
    
    notifications_non_lues = Notification.query.filter_by(
        user_id=current_user.id, lue=False, actif=True
    ).all()
    
    for notification in notifications_non_lues:
        notification.marquer_comme_lue()
    
    count = len(notifications_non_lues)
    
    if request.is_json:
        return jsonify({
            'success': True, 
            'message': f'{count} notifications marquées comme lues',
            'count': count
        })
    
    flash(f'{count} notifications marquées comme lues.', 'success')
    return redirect(url_for('notifications.index'))


@bp.route('/api/non-lues')
@login_required
def api_non_lues():
    """API pour récupérer le nombre de notifications non lues"""
    
    count = Notification.query.filter_by(
        user_id=current_user.id, lue=False, actif=True
    ).count()
    
    return jsonify({'count': count})


@bp.route('/api/recentes')
@login_required
def api_recentes():
    """API pour récupérer les notifications récentes"""
    
    limit = request.args.get('limit', 5, type=int)
    
    notifications = Notification.query.filter_by(
        user_id=current_user.id, actif=True
    ).order_by(desc(Notification.date_creation)).limit(limit).all()
    
    return jsonify({
        'notifications': [notif.to_dict() for notif in notifications]
    })


# Routes pour la messagerie
@bp.route('/messages/')
@login_required
def messages():
    """Interface de messagerie interne"""
    
    # Filtres
    filtre_form = FiltreMessagesForm(request.args)
    
    # Type de vue (reçus, envoyés, archivés)
    vue = request.args.get('vue', 'recus')
    
    # Filtres additionnels
    priorite_filter = request.args.get('priorite')
    statut_filter = request.args.get('statut')
    categorie_filter = request.args.get('categorie')
    etiquette_filter = request.args.get('etiquette')
    
    # Requête selon le type de vue
    if vue == 'envoyes':
        query = MessageInterne.query.filter_by(
            expediteur_id=current_user.id, 
            archive_expediteur=False
        )
    elif vue == 'archives':
        query = MessageInterne.query.filter(
            or_(
                and_(MessageInterne.destinataire_id == current_user.id, 
                     MessageInterne.archive_destinataire == True),
                and_(MessageInterne.expediteur_id == current_user.id, 
                     MessageInterne.archive_expediteur == True)
            )
        )
    else:  # vue == 'recus'
        query = MessageInterne.query.filter_by(
            destinataire_id=current_user.id, 
            archive_destinataire=False
        )
    
    # Application des filtres
    if priorite_filter:
        query = query.filter(MessageInterne.priorite == int(priorite_filter))
        
    if filtre_form.priorite.data:
        query = query.filter(MessageInterne.priorite == int(filtre_form.priorite.data))
    
    if filtre_form.statut.data:
        if filtre_form.statut.data == 'non_lu':
            query = query.filter(MessageInterne.lu == False)
        elif filtre_form.statut.data == 'lu':
            query = query.filter(MessageInterne.lu == True)
    
    if filtre_form.recherche.data:
        terme = f"%{filtre_form.recherche.data}%"
        query = query.filter(or_(
            MessageInterne.sujet.ilike(terme),
            MessageInterne.contenu.ilike(terme)
        ))
    
    # Filtres par catégorie et étiquette (simulation)
    if categorie_filter:
        # Pour l'instant, filtrer par mots-clés dans le sujet ou contenu
        if categorie_filter == 'work':
            terme = "%travail%"
            query = query.filter(or_(
                MessageInterne.sujet.ilike(terme),
                MessageInterne.contenu.ilike(terme)
            ))
        elif categorie_filter == 'documents':
            terme = "%document%"
            query = query.filter(or_(
                MessageInterne.sujet.ilike(terme),
                MessageInterne.contenu.ilike(terme)
            ))
        elif categorie_filter == 'reports':
            terme = "%rapport%"
            query = query.filter(or_(
                MessageInterne.sujet.ilike(terme),
                MessageInterne.contenu.ilike(terme)
            ))
        elif categorie_filter == 'notifications':
            terme = "%notification%"
            query = query.filter(or_(
                MessageInterne.sujet.ilike(terme),
                MessageInterne.contenu.ilike(terme)
            ))
    
    if etiquette_filter:
        if etiquette_filter == 'urgent':
            query = query.filter(MessageInterne.priorite == 3)
        elif etiquette_filter == 'maintenance':
            terme = "%maintenance%"
            query = query.filter(or_(
                MessageInterne.sujet.ilike(terme),
                MessageInterne.contenu.ilike(terme)
            ))
        elif etiquette_filter == 'production':
            terme = "%production%"
            query = query.filter(or_(
                MessageInterne.sujet.ilike(terme),
                MessageInterne.contenu.ilike(terme)
            ))
        elif etiquette_filter == 'distribution':
            terme = "%distribution%"
            query = query.filter(or_(
                MessageInterne.sujet.ilike(terme),
                MessageInterne.contenu.ilike(terme)
            ))
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = 15
    
    messages = query.order_by(desc(MessageInterne.date_creation)).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Statistiques
    stats = {
        'recus': MessageInterne.query.filter_by(
            destinataire_id=current_user.id, archive_destinataire=False
        ).count(),
        'non_lus': MessageInterne.query.filter_by(
            destinataire_id=current_user.id, lu=False, archive_destinataire=False
        ).count(),
        'envoyes': MessageInterne.query.filter_by(
            expediteur_id=current_user.id, archive_expediteur=False
        ).count(),
        'archives': MessageInterne.query.filter(
            or_(
                and_(MessageInterne.destinataire_id == current_user.id, 
                     MessageInterne.archive_destinataire == True),
                and_(MessageInterne.expediteur_id == current_user.id, 
                     MessageInterne.archive_expediteur == True)
            )
        ).count()
    }
    
    from datetime import datetime
    
    return render_template('notifications/messages.html',
                         title="Messagerie Interne",
                         messages=messages,
                         filtre_form=filtre_form,
                         vue=vue,
                         stats=stats,
                         now=datetime.now(),
                         current_filters={
                             'priorite': priorite_filter,
                             'statut': statut_filter,
                             'categorie': categorie_filter,
                             'etiquette': etiquette_filter
                         })


@bp.route('/messages/nouveau', methods=['GET', 'POST'])
@login_required
def nouveau_message():
    """Créer un nouveau message"""
    
    form = MessageInterneForm()
    
    # Remplir les choix de destinataires
    utilisateurs = User.query.filter(User.id != current_user.id, User.actif == True).all()
    form.destinataire_id.choices = [
        (user.id, f"{user.prenom} {user.nom}" if user.prenom else user.username)
        for user in utilisateurs
    ]
    
    # Pré-remplir le destinataire si spécifié
    destinataire_id = request.args.get('destinataire_id', type=int)
    if destinataire_id:
        form.destinataire_id.data = destinataire_id
    
    # Pré-remplir pour une réponse
    reponse_a = request.args.get('reponse_a', type=int)
    if reponse_a:
        message_parent = MessageInterne.query.get_or_404(reponse_a)
        if (message_parent.destinataire_id != current_user.id and 
            message_parent.expediteur_id != current_user.id):
            abort(403)
        
        # Déterminer le destinataire de la réponse
        if message_parent.expediteur_id == current_user.id:
            form.destinataire_id.data = message_parent.destinataire_id
        else:
            form.destinataire_id.data = message_parent.expediteur_id
        
        # Préfixer le sujet
        if not message_parent.sujet.startswith('Re: '):
            form.sujet.data = f"Re: {message_parent.sujet}"
        else:
            form.sujet.data = message_parent.sujet
        
        form.message_parent_id.data = reponse_a
    
    if form.validate_on_submit():
        message = MessageInterne(
            expediteur_id=current_user.id,
            destinataire_id=form.destinataire_id.data,
            sujet=form.sujet.data,
            contenu=form.contenu.data,
            priorite=form.priorite.data,
            message_parent_id=form.message_parent_id.data if form.message_parent_id.data else None
        )
        
        message.save()
        
        flash('Message envoyé avec succès.', 'success')
        return redirect(url_for('notifications.messages', vue='envoyes'))
    
    return render_template('notifications/nouveau_message.html',
                         title="Nouveau Message",
                         form=form)


@bp.route('/messages/<int:id>')
@login_required
def voir_message(id):
    """Voir un message en détail"""
    
    message = MessageInterne.query.get_or_404(id)
    
    # Vérifier les permissions
    if (message.destinataire_id != current_user.id and 
        message.expediteur_id != current_user.id):
        abort(403)
    
    # Marquer comme lu si l'utilisateur est le destinataire
    if message.destinataire_id == current_user.id and not message.lu:
        message.marquer_comme_lu()
    
    # Récupérer la conversation (message parent et réponses)
    if message.message_parent_id:
        message_principal = MessageInterne.query.get(message.message_parent_id)
        conversation = [message_principal] + list(message_principal.reponses)
    else:
        conversation = [message] + list(message.reponses)
    
    # Formulaire de réponse
    form_reponse = ReponseMessageForm()
    form_reponse.message_parent_id.data = message.id if not message.message_parent_id else message.message_parent_id
    
    return render_template('notifications/voir_message.html',
                         title=f"Message: {message.sujet}",
                         message=message,
                         conversation=conversation,
                         form_reponse=form_reponse)


@bp.route('/messages/<int:id>/repondre', methods=['POST'])
@login_required
def repondre_message(id):
    """Répondre à un message"""
    
    message_parent = MessageInterne.query.get_or_404(id)
    
    # Vérifier les permissions
    if (message_parent.destinataire_id != current_user.id and 
        message_parent.expediteur_id != current_user.id):
        abort(403)
    
    form = ReponseMessageForm()
    
    if form.validate_on_submit():
        # Déterminer le destinataire
        if message_parent.expediteur_id == current_user.id:
            destinataire_id = message_parent.destinataire_id
        else:
            destinataire_id = message_parent.expediteur_id
        
        # Créer la réponse
        reponse = MessageInterne(
            expediteur_id=current_user.id,
            destinataire_id=destinataire_id,
            sujet=f"Re: {message_parent.sujet}" if not message_parent.sujet.startswith('Re: ') else message_parent.sujet,
            contenu=form.contenu.data,
            priorite=message_parent.priorite,
            message_parent_id=message_parent.message_parent_id or message_parent.id
        )
        
        reponse.save()
        
        flash('Réponse envoyée avec succès.', 'success')
    else:
        flash('Erreur lors de l\'envoi de la réponse.', 'error')
    
    return redirect(url_for('notifications.voir_message', id=id))


@bp.route('/messages/<int:id>/archiver', methods=['POST'])
@login_required
def archiver_message(id):
    """Archiver un message"""
    
    message = MessageInterne.query.get_or_404(id)
    
    # Vérifier les permissions et archiver selon le rôle
    if message.destinataire_id == current_user.id:
        message.archiver_pour_destinataire()
    elif message.expediteur_id == current_user.id:
        message.archiver_pour_expediteur()
    else:
        abort(403)
    
    if request.is_json:
        return jsonify({'success': True, 'message': 'Message archivé'})
    
    flash('Message archivé.', 'success')
    return redirect(request.referrer or url_for('notifications.messages'))


@bp.route('/preferences', methods=['GET', 'POST'])
@login_required
def preferences():
    """Gérer les préférences de notifications"""
    
    # Récupérer ou créer les préférences
    prefs = PreferenceNotification.query.filter_by(user_id=current_user.id).first()
    if not prefs:
        prefs = PreferenceNotification(user_id=current_user.id)
        prefs.save()
    
    form = PreferencesNotificationForm(obj=prefs)
    
    if form.validate_on_submit():
        form.populate_obj(prefs)
        prefs.save()
        
        flash('Préférences mises à jour avec succès.', 'success')
        return redirect(url_for('notifications.preferences'))
    
    return render_template('notifications/preferences.html',
                         title="Préférences de Notifications",
                         form=form,
                         prefs=prefs)


# Routes d'administration (pour les admins)
@bp.route('/admin/')
@login_required
def admin_index():
    """Panel d'administration des notifications"""
    
    if not current_user.is_admin():
        abort(403)
    
    # Statistiques générales
    stats = {
        'total_notifications': Notification.query.filter_by(actif=True).count(),
        'notifications_non_lues': Notification.query.filter_by(lue=False, actif=True).count(),
        'total_messages': MessageInterne.query.count(),
        'messages_non_lus': MessageInterne.query.filter_by(lu=False).count(),
        'templates_actifs': TemplateNotification.query.filter_by(actif=True).count(),
        'utilisateurs_actifs': User.query.filter_by(actif=True).count()
    }
    
    # Notifications récentes
    notifications_recentes = Notification.query.filter_by(actif=True).order_by(
        desc(Notification.date_creation)
    ).limit(10).all()
    
    # Messages récents
    messages_recents = MessageInterne.query.order_by(
        desc(MessageInterne.date_creation)
    ).limit(10).all()
    
    return render_template('notifications/admin/index.html',
                         title="Administration des Notifications",
                         stats=stats,
                         notifications_recentes=notifications_recentes,
                         messages_recents=messages_recents)


@bp.route('/admin/creer-notification', methods=['GET', 'POST'])
@login_required
def admin_creer_notification():
    """Créer une notification pour un utilisateur"""
    
    if not current_user.is_admin():
        abort(403)
    
    form = CreerNotificationForm()
    
    # Remplir les choix d'utilisateurs
    utilisateurs = User.query.filter_by(actif=True).all()
    form.user_id.choices = [
        (user.id, f"{user.prenom} {user.nom}" if user.prenom else user.username)
        for user in utilisateurs
    ]
    
    if form.validate_on_submit():
        notification = Notification(
            user_id=form.user_id.data,
            type=TypeNotification(form.type_notification.data),
            titre=form.titre.data,
            message=form.message.data,
            priorite=form.priorite.data,
            url_action=form.url_action.data
        )
        
        notification.save()
        
        flash('Notification créée avec succès.', 'success')
        return redirect(url_for('notifications.admin_index'))
    
    return render_template('notifications/admin/creer_notification.html',
                         title="Créer une Notification",
                         form=form)


@bp.route('/admin/templates')
@login_required
def admin_templates():
    """Gestion des templates de notifications"""
    
    if not current_user.is_admin():
        abort(403)
    
    templates = TemplateNotification.query.filter_by(actif=True).order_by(
        TemplateNotification.nom
    ).all()
    
    return render_template('notifications/admin/templates.html',
                         title="Templates de Notifications",
                         templates=templates)


@bp.route('/admin/templates/nouveau', methods=['GET', 'POST'])
@login_required
def admin_nouveau_template():
    """Créer un nouveau template"""
    
    if not current_user.is_admin():
        abort(403)
    
    form = CreerTemplateForm()
    
    if form.validate_on_submit():
        template = TemplateNotification(
            code=form.code.data,
            nom=form.nom.data,
            type_notification=TypeNotification(form.type_notification.data),
            titre_template=form.titre_template.data,
            message_template=form.message_template.data,
            priorite_defaut=form.priorite_defaut.data,
            url_template=form.url_template.data,
            actif=form.actif.data
        )
        
        template.save()
        
        flash('Template créé avec succès.', 'success')
        return redirect(url_for('notifications.admin_templates'))
    
    return render_template('notifications/admin/nouveau_template.html',
                         title="Nouveau Template",
                         form=form)