"""
Routes pour la gestion des opérateurs
"""
from flask import render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from app.operateurs import operateurs
from app.operateurs.forms import OperateurForm, ContactForm, ContactOperateurForm
from app.models.operateurs import Operateur, Contact
from app.extensions import db
from app.utils.decorators import role_required, super_admin_required, operateur_access_required


@operateurs.route('/')
@login_required
@super_admin_required
def index():
    """Liste de tous les opérateurs (super admin seulement)"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Filtres
    search = request.args.get('search', '', type=str)
    type_filter = request.args.get('type', '', type=str)
    province_filter = request.args.get('province', '', type=str)
    statut_filter = request.args.get('statut', '', type=str)
    
    # Construction de la requête
    query = Operateur.query.filter(Operateur.actif == True)
    
    if search:
        query = query.filter(
            db.or_(
                Operateur.nom.contains(search),
                Operateur.sigle.contains(search),
                Operateur.ville.contains(search)
            )
        )
    
    if type_filter:
        query = query.filter(Operateur.type_operateur == type_filter)
    
    if province_filter:
        query = query.filter(Operateur.province == province_filter)
    
    if statut_filter:
        query = query.filter(Operateur.statut_licence == statut_filter)
    
    # Pagination
    operateurs = query.order_by(Operateur.nom).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Données pour les filtres
    types = db.session.query(Operateur.type_operateur).filter(
        Operateur.type_operateur.isnot(None),
        Operateur.actif == True
    ).distinct().all()
    types = [t[0] for t in types]
    
    provinces = db.session.query(Operateur.province).filter(
        Operateur.province.isnot(None),
        Operateur.actif == True
    ).distinct().all()
    provinces = [p[0] for p in provinces]
    
    return render_template('operateurs/liste.html',
                         operateurs=operateurs,
                         types=types,
                         provinces=provinces,
                         search=search,
                         type_filter=type_filter,
                         province_filter=province_filter,
                         statut_filter=statut_filter)


@operateurs.route('/mon-operateur')
@login_required
@role_required('admin_operateur')
def mon_operateur():
    """Voir/modifier son opérateur (admin opérateur seulement)"""
    if not current_user.operateur:
        flash('Vous n\'êtes associé à aucun opérateur.', 'warning')
        return redirect(url_for('main.dashboard'))
    
    return redirect(url_for('operateurs.details', id=current_user.operateur.id))


@operateurs.route('/nouveau', methods=['GET', 'POST'])
@login_required
@super_admin_required
def nouveau():
    """Créer un nouvel opérateur"""
    form = OperateurForm()
    
    if form.validate_on_submit():
        operateur = Operateur(
            nom=form.nom.data,
            sigle=form.sigle.data,
            type_operateur=form.type_operateur.data,
            adresse=form.adresse.data,
            ville=form.ville.data,
            province=form.province.data,
            telephone=form.telephone.data,
            email=form.email.data,
            site_web=form.site_web.data,
            numero_licence=form.numero_licence.data,
            date_licence=form.date_licence.data,
            statut_licence=form.statut_licence.data,
            capacite_installee=form.capacite_installee.data,
            zone_couverture=form.zone_couverture.data,
            nombre_clients=form.nombre_clients.data,
            observations=form.observations.data
        )
        
        try:
            operateur.save()
            flash(f'Opérateur "{operateur.nom}" créé avec succès.', 'success')
            return redirect(url_for('operateurs.details', id=operateur.id))
        except Exception as e:
            flash(f'Erreur lors de la création: {str(e)}', 'danger')
    
    return render_template('operateurs/form.html', form=form, title='Nouvel Opérateur')


@operateurs.route('/<int:id>')
@login_required
def details(id):
    """Afficher les détails d'un opérateur"""
    operateur = Operateur.query.get_or_404(id)
    
    # Vérifier les permissions
    if not current_user.is_super_admin():
        if not current_user.operateur or current_user.operateur.id != operateur.id:
            abort(403)
    
    return render_template('operateurs/details.html', 
                         operateur=operateur, 
                         now=datetime.utcnow())


@operateurs.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Modifier un opérateur"""
    operateur = Operateur.query.get_or_404(id)
    
    # Vérifier les permissions
    if not current_user.is_super_admin():
        if not current_user.operateur or current_user.operateur.id != operateur.id:
            abort(403)
    
    form = OperateurForm(obj=operateur)
    
    if form.validate_on_submit():
        try:
            form.populate_obj(operateur)
            operateur.save()
            flash(f'Opérateur "{operateur.nom}" modifié avec succès.', 'success')
            return redirect(url_for('operateurs.details', id=operateur.id))
        except Exception as e:
            flash(f'Erreur lors de la modification: {str(e)}', 'danger')
    
    return render_template('operateurs/form.html', 
                         form=form, 
                         operateur=operateur,
                         title=f'Modifier {operateur.nom}')


@operateurs.route('/<int:id>/delete', methods=['POST'])
@login_required
@super_admin_required
def delete(id):
    """Supprimer un opérateur (soft delete)"""
    operateur = Operateur.query.get_or_404(id)
    
    try:
        operateur.soft_delete()
        flash(f'Opérateur "{operateur.nom}" supprimé avec succès.', 'success')
    except Exception as e:
        flash(f'Erreur lors de la suppression: {str(e)}', 'danger')
    
    return redirect(url_for('operateurs.index'))


# Routes pour les contacts
@operateurs.route('/<int:id>/contacts/nouveau', methods=['GET', 'POST'])
@login_required
def nouveau_contact(id):
    """Ajouter un contact à un opérateur"""
    operateur = Operateur.query.get_or_404(id)
    
    # Vérifier les permissions
    if not current_user.is_super_admin():
        if not current_user.operateur or current_user.operateur.id != operateur.id:
            abort(403)
    
    form = ContactOperateurForm()
    
    if form.validate_on_submit():
        contact = Contact(
            operateur_id=operateur.id,
            nom=form.contact.nom.data,
            prenom=form.contact.prenom.data,
            email=form.contact.email.data,
            telephone=form.contact.telephone.data,
            fonction=form.contact.fonction.data
        )
        
        try:
            contact.save()
            flash(f'Contact "{contact.prenom} {contact.nom}" ajouté avec succès.', 'success')
            return redirect(url_for('operateurs.details', id=operateur.id))
        except Exception as e:
            flash(f'Erreur lors de l\'ajout du contact: {str(e)}', 'danger')
    
    return render_template('operateurs/contact_form.html', 
                         form=form, 
                         operateur=operateur,
                         title=f'Nouveau contact pour {operateur.nom}')


@operateurs.route('/contacts/<int:contact_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_contact(contact_id):
    """Modifier un contact"""
    contact = Contact.query.get_or_404(contact_id)
    operateur = contact.operateur
    
    # Vérifier les permissions
    if not current_user.is_super_admin():
        if not current_user.operateur or current_user.operateur.id != operateur.id:
            abort(403)
    
    form = ContactOperateurForm(obj={'contact': contact})
    
    if form.validate_on_submit():
        try:
            contact.nom = form.contact.nom.data
            contact.prenom = form.contact.prenom.data
            contact.email = form.contact.email.data
            contact.telephone = form.contact.telephone.data
            contact.fonction = form.contact.fonction.data
            contact.save()
            flash(f'Contact "{contact.prenom} {contact.nom}" modifié avec succès.', 'success')
            return redirect(url_for('operateurs.details', id=operateur.id))
        except Exception as e:
            flash(f'Erreur lors de la modification du contact: {str(e)}', 'danger')
    
    return render_template('operateurs/contact_form.html', 
                         form=form, 
                         contact=contact,
                         operateur=operateur,
                         title=f'Modifier {contact.prenom} {contact.nom}')


@operateurs.route('/contacts/<int:contact_id>/delete', methods=['POST'])
@login_required
def delete_contact(contact_id):
    """Supprimer un contact"""
    contact = Contact.query.get_or_404(contact_id)
    operateur = contact.operateur
    
    # Vérifier les permissions
    if not current_user.is_super_admin():
        if not current_user.operateur or current_user.operateur.id != operateur.id:
            abort(403)
    
    try:
        contact.delete()
        flash(f'Contact "{contact.prenom} {contact.nom}" supprimé avec succès.', 'success')
    except Exception as e:
        flash(f'Erreur lors de la suppression du contact: {str(e)}', 'danger')
    
    return redirect(url_for('operateurs.details', id=operateur.id))


# API endpoints
@operateurs.route('/api/search')
@login_required
def api_search():
    """API pour la recherche d'opérateurs"""
    query = request.args.get('q', '', type=str)
    
    if not query:
        return jsonify([])
    
    # Restrictions selon le rôle
    base_query = Operateur.query.filter(Operateur.actif == True)
    
    if not current_user.is_super_admin():
        if current_user.operateur:
            base_query = base_query.filter(Operateur.id == current_user.operateur.id)
        else:
            return jsonify([])
    
    operateurs = base_query.filter(
        db.or_(
            Operateur.nom.contains(query),
            Operateur.sigle.contains(query)
        )
    ).limit(10).all()
    
    return jsonify([{
        'id': op.id,
        'nom': op.nom,
        'sigle': op.sigle,
        'type_operateur': op.type_operateur
    } for op in operateurs])