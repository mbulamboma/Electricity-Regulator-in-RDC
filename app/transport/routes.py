"""
Routes pour le module Transport
Gestion des lignes de transport, postes et transformateurs
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
import json

from app.extensions import db
from app.models.transport import LigneTransport, PosteTransport, TransformateurTransport, RapportTransport
from app.models.operateurs import Operateur
from app.transport.forms import (
    LigneTransportForm, PosteTransportForm, TransformateurTransportForm, 
    RapportTransportForm, FiltreTransportForm
)
from app.utils.permissions import (
    get_accessible_operateurs, can_access_operateur, 
    filter_query_by_operateur, get_default_operateur_id
)

bp = Blueprint('transport', __name__, url_prefix='/transport')

def verifier_permission_operateur(operateur_id):
    """Vérifier si l'utilisateur peut accéder aux données de cet opérateur"""
    if current_user.is_admin():
        return True
    return current_user.operateur_id == operateur_id

@bp.route('/')
@login_required
def index():
    """Page d'accueil du module transport"""
    
    # Créer le formulaire de filtrage
    filtre_form = FiltreTransportForm(request.args)
    
    # Définir les choix pour les opérateurs dans le formulaire
    if current_user.is_admin():
        operateurs = Operateur.query.filter_by(actif=True).all()
        filtre_form.operateur.choices = [('', 'Tous les opérateurs')] + [(op.id, op.nom) for op in operateurs]
    else:
        operateurs = [current_user.operateur] if current_user.operateur else []
        if current_user.operateur:
            filtre_form.operateur.choices = [(current_user.operateur.id, current_user.operateur.nom)]
    
    # Filtres
    operateur_id = request.args.get('operateur', type=int)
    statut = request.args.get('statut')
    tension_min = request.args.get('tension_min', type=float)
    tension_max = request.args.get('tension_max', type=float)
    
    # Requête de base selon les permissions
    if current_user.is_admin():
        query_lignes = LigneTransport.query
        query_postes = PosteTransport.query
    else:
        query_lignes = LigneTransport.query.filter_by(operateur_id=current_user.operateur_id)
        query_postes = PosteTransport.query.filter_by(operateur_id=current_user.operateur_id)
    
    # Application des filtres
    if operateur_id:
        query_lignes = query_lignes.filter_by(operateur_id=operateur_id)
        query_postes = query_postes.filter_by(operateur_id=operateur_id)
    
    if statut:
        query_lignes = query_lignes.filter_by(statut=statut)
        query_postes = query_postes.filter_by(statut=statut)
    
    if tension_min:
        query_lignes = query_lignes.filter(LigneTransport.tension_nominale >= tension_min)
    
    if tension_max:
        query_lignes = query_lignes.filter(LigneTransport.tension_nominale <= tension_max)
    
    # Récupération des données
    lignes = query_lignes.filter_by(actif=True).all()
    postes = query_postes.filter_by(actif=True).all()
    
    # Statistiques
    stats = {
        'nb_lignes': len(lignes),
        'nb_postes': len(postes),
        'longueur_totale': sum([ligne.longueur_totale for ligne in lignes if ligne.longueur_totale]),
        'capacite_totale': sum([poste.puissance_installee for poste in postes if poste.puissance_installee]),
        'lignes_en_service': len([l for l in lignes if l.statut == 'en_service']),
        'postes_en_service': len([p for p in postes if p.statut == 'en_service'])
    }
    
    # Données pour les graphiques
    donnees_graphiques = generer_donnees_graphiques_transport(lignes, postes)
    
    return render_template('transport/index.html',
                         lignes=lignes,
                         postes=postes,
                         operateurs=operateurs,
                         stats=stats,
                         donnees_graphiques=donnees_graphiques,
                         filtre_form=filtre_form,
                         filtres=request.args)

@bp.route('/lignes')
@login_required
def liste_lignes():
    """Liste des lignes de transport"""
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)
    
    # Requête de base
    if current_user.is_admin():
        query = LigneTransport.query
        operateurs = Operateur.query.filter_by(actif=True).all()
    else:
        query = LigneTransport.query.filter_by(operateur_id=current_user.operateur_id)
        operateurs = [current_user.operateur] if current_user.operateur else []
    
    # Filtres
    operateur_id = request.args.get('operateur_id', type=int)
    if operateur_id:
        query = query.filter_by(operateur_id=operateur_id)
    
    statut = request.args.get('statut')
    if statut:
        query = query.filter_by(statut=statut)
    
    tension = request.args.get('tension', type=float)
    if tension:
        query = query.filter_by(tension_nominale=tension)
    
    # Tri
    sort_by = request.args.get('sort', 'nom')
    sort_order = request.args.get('order', 'asc')
    
    if hasattr(LigneTransport, sort_by):
        column = getattr(LigneTransport, sort_by)
        if sort_order == 'desc':
            query = query.order_by(column.desc())
        else:
            query = query.order_by(column.asc())
    
    # Pagination
    lignes_paginated = query.filter_by(actif=True).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('transport/lignes/liste.html',
                         lignes=lignes_paginated,
                         operateurs=operateurs)

@bp.route('/lignes/nouveau', methods=['GET', 'POST'])
@login_required
def nouvelle_ligne():
    """Créer une nouvelle ligne de transport"""
    
    form = LigneTransportForm()
    
    # Limiter les opérateurs selon les permissions
    if current_user.is_admin():
        # Les admins peuvent assigner à tous les opérateurs actifs
        form.operateur_id.choices = [
            (op.id, op.nom) for op in 
            Operateur.query.filter_by(actif=True).all()
        ]
    else:
        # Les utilisateurs non-admin ne peuvent créer que pour leur propre opérateur
        if current_user.operateur:
            form.operateur_id.choices = [(current_user.operateur_id, current_user.operateur.nom)]
            form.operateur_id.data = current_user.operateur_id
        else:
            flash('Vous n\'avez pas l\'autorisation de créer une ligne de transport.', 'error')
            return redirect(url_for('transport.index'))
    
    if form.validate_on_submit():
        try:
            ligne = LigneTransport()
            form.populate_obj(ligne)
            ligne.save()
            
            flash(f'Ligne de transport "{ligne.nom}" créée avec succès.', 'success')
            return redirect(url_for('transport.detail_ligne', id=ligne.id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la création de la ligne : {str(e)}', 'error')
    
    return render_template('transport/lignes/formulaire.html', form=form, mode='creation')

@bp.route('/lignes/<int:id>')
@login_required
def detail_ligne(id):
    """Détail d'une ligne de transport"""
    
    ligne = LigneTransport.query.get_or_404(id)
    
    if not verifier_permission_operateur(ligne.operateur_id):
        abort(403)
    
    # Données pour les graphiques
    donnees_performance = generer_donnees_performance_ligne(ligne)
    
    # Rapports associés
    rapports = RapportTransport.query.filter_by(
        ligne_id=ligne.id,
        actif=True
    ).order_by(RapportTransport.periode_debut.desc()).limit(10).all()
    
    return render_template('transport/lignes/detail.html',
                         ligne=ligne,
                         rapports=rapports,
                         donnees_performance=donnees_performance)

@bp.route('/lignes/<int:id>/modifier', methods=['GET', 'POST'])
@login_required
def modifier_ligne(id):
    """Modifier une ligne de transport"""
    
    ligne = LigneTransport.query.get_or_404(id)
    
    if not verifier_permission_operateur(ligne.operateur_id):
        abort(403)
    
    form = LigneTransportForm(obj=ligne)
    
    # Configuration des choix selon les permissions
    if current_user.is_admin():
        form.operateur_id.choices = [
            (op.id, op.nom) for op in 
            Operateur.query.filter_by(actif=True).all()
        ]
    else:
        form.operateur_id.choices = [(ligne.operateur_id, ligne.operateur.nom)]
    
    if form.validate_on_submit():
        try:
            form.populate_obj(ligne)
            ligne.update()
            
            flash(f'Ligne de transport "{ligne.nom}" modifiée avec succès.', 'success')
            return redirect(url_for('transport.detail_ligne', id=ligne.id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la modification : {str(e)}', 'error')
    
    return render_template('transport/lignes/formulaire.html', 
                         form=form, ligne=ligne, mode='modification')

@bp.route('/postes')
@login_required
def liste_postes():
    """Liste des postes de transport"""
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)
    
    # Requête de base
    if current_user.is_admin():
        query = PosteTransport.query
        operateurs = Operateur.query.filter_by(actif=True).all()
    else:
        query = PosteTransport.query.filter_by(operateur_id=current_user.operateur_id)
        operateurs = [current_user.operateur] if current_user.operateur else []
    
    # Application des filtres
    operateur_id = request.args.get('operateur_id', type=int)
    if operateur_id:
        query = query.filter_by(operateur_id=operateur_id)
    
    type_poste = request.args.get('type_poste')
    if type_poste:
        query = query.filter_by(type_poste=type_poste)
    
    statut = request.args.get('statut')
    if statut:
        query = query.filter_by(statut=statut)
    
    # Pagination
    postes_paginated = query.filter_by(actif=True).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('transport/postes/liste.html',
                         postes=postes_paginated,
                         operateurs=operateurs)

@bp.route('/postes/nouveau', methods=['GET', 'POST'])
@login_required
def nouveau_poste():
    """Créer un nouveau poste de transport"""
    
    form = PosteTransportForm()
    
    # Configuration des choix d'opérateurs
    if current_user.is_admin():
        form.operateur_id.choices = [
            (op.id, op.nom) for op in 
            Operateur.query.filter_by(actif=True).all()
        ]
    else:
        if current_user.operateur:
            form.operateur_id.choices = [(current_user.operateur_id, current_user.operateur.nom)]
            form.operateur_id.data = current_user.operateur_id
        else:
            flash('Vous n\'avez pas l\'autorisation de créer un poste de transport.', 'error')
            return redirect(url_for('transport.index'))
    
    if form.validate_on_submit():
        try:
            poste = PosteTransport()
            form.populate_obj(poste)
            poste.save()
            
            flash(f'Poste de transport "{poste.nom}" créé avec succès.', 'success')
            return redirect(url_for('transport.detail_poste', id=poste.id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la création du poste : {str(e)}', 'error')
    
    return render_template('transport/postes/formulaire.html', form=form, mode='creation')

@bp.route('/postes/<int:id>')
@login_required
def detail_poste(id):
    """Détail d'un poste de transport"""
    
    poste = PosteTransport.query.get_or_404(id)
    
    if not verifier_permission_operateur(poste.operateur_id):
        abort(403)
    
    # Transformateurs du poste
    transformateurs = TransformateurTransport.query.filter_by(
        poste_id=poste.id,
        actif=True
    ).all()
    
    # Données pour les graphiques
    donnees_charge = generer_donnees_charge_poste(poste)
    
    return render_template('transport/postes/detail.html',
                         poste=poste,
                         transformateurs=transformateurs,
                         donnees_charge=donnees_charge)

@bp.route('/postes/<int:id>/modifier', methods=['GET', 'POST'])
@login_required
def modifier_poste(id):
    """Modifier un poste de transport"""
    
    poste = PosteTransport.query.get_or_404(id)
    
    if not verifier_permission_operateur(poste.operateur_id):
        abort(403)
    
    form = PosteTransportForm(obj=poste)
    
    if form.validate_on_submit():
        try:
            # Vérifier les permissions sur le nouvel opérateur si changé
            if form.operateur_id.data != poste.operateur_id:
                if not verifier_permission_operateur(form.operateur_id.data):
                    abort(403)
            
            poste.update(
                operateur_id=form.operateur_id.data,
                nom=form.nom.data,
                code=form.code.data,
                type_poste=form.type_poste.data,
                localisation=form.localisation.data,
                province=form.province.data,
                latitude=form.latitude.data,
                longitude=form.longitude.data,
                altitude=form.altitude.data,
                tension_primaire=form.tension_primaire.data,
                tension_secondaire=form.tension_secondaire.data,
                tension_tertiaire=form.tension_tertiaire.data,
                nombre_transformateurs=form.nombre_transformateurs.data,
                puissance_installee=form.puissance_installee.data,
                puissance_disponible=form.puissance_disponible.data,
                schema_unifilaire=form.schema_unifilaire.data,
                nombre_disjoncteurs=form.nombre_disjoncteurs.data,
                nombre_sectionneurs=form.nombre_sectionneurs.data,
                parafoudres=form.parafoudres.data,
                systeme_scada=form.systeme_scada.data,
                telecommande=form.telecommande.data,
                telemesure=form.telemesure.data,
                date_mise_service=form.date_mise_service.data,
                statut=form.statut.data,
                regime_neutre=form.regime_neutre.data,
                taux_disponibilite=form.taux_disponibilite.data,
                nombre_incidents_annuels=form.nombre_incidents_annuels.data,
                duree_moyenne_indisponibilite=form.duree_moyenne_indisponibilite.data,
                date_derniere_maintenance=form.date_derniere_maintenance.data,
                periodicite_maintenance=form.periodicite_maintenance.data,
                cloture_securite=form.cloture_securite.data,
                systeme_incendie=form.systeme_incendie.data,
                bac_retention_huile=form.bac_retention_huile.data,
                description=form.description.data,
                observations=form.observations.data
            )
            
            flash('Poste modifié avec succès.', 'success')
            return redirect(url_for('transport.detail_poste', id=poste.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la modification du poste : {str(e)}', 'error')
    
    return render_template('transport/postes/formulaire.html', 
                         form=form, 
                         poste=poste, 
                         mode='modification')

@bp.route('/postes/<int:id>/supprimer', methods=['POST'])
@login_required
def supprimer_poste(id):
    """Supprimer un poste de transport"""
    
    poste = PosteTransport.query.get_or_404(id)
    
    if not verifier_permission_operateur(poste.operateur_id):
        abort(403)
    
    try:
        # Vérifier s'il y a des transformateurs liés
        transformateurs_count = TransformateurTransport.query.filter_by(
            poste_id=poste.id, 
            actif=True
        ).count()
        
        if transformateurs_count > 0:
            flash(f'Impossible de supprimer ce poste : {transformateurs_count} transformateur(s) y sont encore rattachés.', 'error')
            return redirect(url_for('transport.detail_poste', id=id))
        
        poste.soft_delete()
        flash('Poste supprimé avec succès.', 'success')
        return redirect(url_for('transport.liste_postes'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression du poste : {str(e)}', 'error')
        return redirect(url_for('transport.detail_poste', id=id))

@bp.route('/transformateurs')
@login_required
def liste_transformateurs():
    """Liste des transformateurs de transport"""
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)
    
    # Requête de base
    if current_user.is_admin():
        query = TransformateurTransport.query.join(PosteTransport)
    else:
        query = TransformateurTransport.query.join(PosteTransport).filter(
            PosteTransport.operateur_id == current_user.operateur_id
        )
    
    # Filtres
    poste_id = request.args.get('poste_id', type=int)
    if poste_id:
        query = query.filter_by(poste_id=poste_id)
    
    statut = request.args.get('statut')
    if statut:
        query = query.filter(TransformateurTransport.statut == statut)
    
    # Pagination
    transformateurs_paginated = query.filter(
        TransformateurTransport.actif == True
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    # Postes pour le filtre
    if current_user.is_admin():
        postes = PosteTransport.query.filter_by(actif=True).all()
    else:
        postes = PosteTransport.query.filter_by(
            operateur_id=current_user.operateur_id,
            actif=True
        ).all()
    
    return render_template('transport/transformateurs/liste.html',
                         transformateurs=transformateurs_paginated,
                         postes=postes)

@bp.route('/transformateurs/nouveau', methods=['GET', 'POST'])
@login_required
def nouveau_transformateur():
    """Créer un nouveau transformateur de transport"""
    
    form = TransformateurTransportForm()
    
    if form.validate_on_submit():
        # Vérifier les permissions
        poste = PosteTransport.query.get_or_404(form.poste_id.data)
        if not current_user.is_admin() and poste.operateur_id != current_user.operateur_id:
            abort(403)
        
        transformateur = TransformateurTransport(
            poste_id=form.poste_id.data,
            nom=form.nom.data,
            numero_serie=form.numero_serie.data,
            constructeur=form.constructeur.data,
            annee_fabrication=form.annee_fabrication.data,
            puissance_nominale=form.puissance_nominale.data,
            tension_primaire=form.tension_primaire.data,
            tension_secondaire=form.tension_secondaire.data,
            tension_tertiaire=form.tension_tertiaire.data,
            couplage=form.couplage.data,
            type_refroidissement=form.type_refroidissement.data,
            poids_total=form.poids_total.data,
            volume_huile=form.volume_huile.data,
            type_huile=form.type_huile.data,
            impedance_cc=form.impedance_cc.data,
            pertes_vide=form.pertes_vide.data,
            pertes_charge=form.pertes_charge.data,
            courant_vide=form.courant_vide.data,
            changeur_prises=form.changeur_prises.data,
            nombre_prises=form.nombre_prises.data,
            plage_reglage=form.plage_reglage.data,
            pas_reglage=form.pas_reglage.data,
            statut=form.statut.data,
            date_mise_service=form.date_mise_service.data,
            date_derniere_maintenance=form.date_derniere_maintenance.data,
            type_derniere_maintenance=form.type_derniere_maintenance.data,
            prochaine_maintenance=form.prochaine_maintenance.data,
            temperature_huile=form.temperature_huile.data,
            temperature_enroulements=form.temperature_enroulements.data,
            niveau_huile=form.niveau_huile.data,
            pression_huile=form.pression_huile.data,
            date_derniere_analyse_huile=form.date_derniere_analyse_huile.data,
            resultat_analyse_huile=form.resultat_analyse_huile.data,
            date_dernier_test_isolement=form.date_dernier_test_isolement.data,
            resistance_isolement=form.resistance_isolement.data,
            observations=form.observations.data
        )
        
        transformateur.save()
        flash('Transformateur créé avec succès.', 'success')
        return redirect(url_for('transport.liste_transformateurs'))
    
    return render_template('transport/transformateurs/formulaire.html', 
                         form=form, 
                         titre='Nouveau transformateur')

@bp.route('/transformateurs/<int:id>')
@login_required
def detail_transformateur(id):
    """Afficher les détails d'un transformateur"""
    
    transformateur = TransformateurTransport.query.get_or_404(id)
    
    # Vérifier les permissions
    if not current_user.is_admin() and transformateur.poste.operateur_id != current_user.operateur_id:
        abort(403)
    
    return render_template('transport/transformateurs/detail.html',
                         transformateur=transformateur)

@bp.route('/transformateurs/<int:id>/modifier', methods=['GET', 'POST'])
@login_required
def modifier_transformateur(id):
    """Modifier un transformateur de transport"""
    
    transformateur = TransformateurTransport.query.get_or_404(id)
    
    # Vérifier les permissions
    if not current_user.is_admin() and transformateur.poste.operateur_id != current_user.operateur_id:
        abort(403)
    
    form = TransformateurTransportForm(obj=transformateur)
    
    if form.validate_on_submit():
        # Vérifier les permissions sur le nouveau poste si changé
        if form.poste_id.data != transformateur.poste_id:
            nouveau_poste = PosteTransport.query.get_or_404(form.poste_id.data)
            if not current_user.is_admin() and nouveau_poste.operateur_id != current_user.operateur_id:
                abort(403)
        
        transformateur.update(
            poste_id=form.poste_id.data,
            nom=form.nom.data,
            numero_serie=form.numero_serie.data,
            constructeur=form.constructeur.data,
            annee_fabrication=form.annee_fabrication.data,
            puissance_nominale=form.puissance_nominale.data,
            tension_primaire=form.tension_primaire.data,
            tension_secondaire=form.tension_secondaire.data,
            tension_tertiaire=form.tension_tertiaire.data,
            couplage=form.couplage.data,
            type_refroidissement=form.type_refroidissement.data,
            poids_total=form.poids_total.data,
            volume_huile=form.volume_huile.data,
            type_huile=form.type_huile.data,
            impedance_cc=form.impedance_cc.data,
            pertes_vide=form.pertes_vide.data,
            pertes_charge=form.pertes_charge.data,
            courant_vide=form.courant_vide.data,
            changeur_prises=form.changeur_prises.data,
            nombre_prises=form.nombre_prises.data,
            plage_reglage=form.plage_reglage.data,
            pas_reglage=form.pas_reglage.data,
            statut=form.statut.data,
            date_mise_service=form.date_mise_service.data,
            date_derniere_maintenance=form.date_derniere_maintenance.data,
            type_derniere_maintenance=form.type_derniere_maintenance.data,
            prochaine_maintenance=form.prochaine_maintenance.data,
            temperature_huile=form.temperature_huile.data,
            temperature_enroulements=form.temperature_enroulements.data,
            niveau_huile=form.niveau_huile.data,
            pression_huile=form.pression_huile.data,
            date_derniere_analyse_huile=form.date_derniere_analyse_huile.data,
            resultat_analyse_huile=form.resultat_analyse_huile.data,
            date_dernier_test_isolement=form.date_dernier_test_isolement.data,
            resistance_isolement=form.resistance_isolement.data,
            observations=form.observations.data
        )
        
        flash('Transformateur modifié avec succès.', 'success')
        return redirect(url_for('transport.detail_transformateur', id=transformateur.id))
    
    return render_template('transport/transformateurs/formulaire.html', 
                         form=form, 
                         transformateur=transformateur,
                         titre='Modifier transformateur')

@bp.route('/transformateurs/<int:id>/supprimer', methods=['POST'])
@login_required
def supprimer_transformateur(id):
    """Supprimer un transformateur de transport"""
    
    transformateur = TransformateurTransport.query.get_or_404(id)
    
    # Vérifier les permissions
    if not current_user.is_admin() and transformateur.poste.operateur_id != current_user.operateur_id:
        abort(403)
    
    transformateur.soft_delete()
    flash('Transformateur supprimé avec succès.', 'success')
    return redirect(url_for('transport.liste_transformateurs'))

@bp.route('/rapports')
@login_required
def liste_rapports():
    """Liste des rapports de transport"""
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)
    
    # Requête de base selon les permissions
    if current_user.is_admin():
        query = RapportTransport.query.join(PosteTransport)
    else:
        query = RapportTransport.query.join(PosteTransport).filter(
            PosteTransport.operateur_id == current_user.operateur_id
        )
    
    # Filtres par date
    date_debut = request.args.get('date_debut')
    date_fin = request.args.get('date_fin')
    
    if date_debut:
        try:
            date_debut = datetime.strptime(date_debut, '%Y-%m-%d').date()
            query = query.filter(RapportTransport.periode_debut >= date_debut)
        except ValueError:
            flash('Format de date de début invalide.', 'error')
    
    if date_fin:
        try:
            date_fin = datetime.strptime(date_fin, '%Y-%m-%d').date()
            query = query.filter(RapportTransport.periode_debut <= date_fin)
        except ValueError:
            flash('Format de date de fin invalide.', 'error')
    
    # Type de rapport
    type_rapport = request.args.get('type_rapport')
    if type_rapport:
        query = query.filter_by(type_rapport=type_rapport)
    
    # Pagination
    rapports_paginated = query.filter_by(actif=True).order_by(
        RapportTransport.periode_debut.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('transport/rapports/liste.html',
                         rapports=rapports_paginated)

@bp.route('/rapports/nouveau', methods=['GET', 'POST'])
@login_required
def nouveau_rapport():
    """Créer un nouveau rapport de transport"""
    
    form = RapportTransportForm()
    
    # Configuration des choix selon les permissions
    if current_user.is_admin():
        postes = PosteTransport.query.filter_by(actif=True).all()
        lignes = LigneTransport.query.filter_by(actif=True).all()
    else:
        postes = PosteTransport.query.filter_by(
            operateur_id=current_user.operateur_id,
            actif=True
        ).all()
        lignes = LigneTransport.query.filter_by(
            operateur_id=current_user.operateur_id,
            actif=True
        ).all()
    
    form.poste_id.choices = [(0, 'Sélectionner un poste')] + [(p.id, p.nom) for p in postes]
    form.ligne_id.choices = [(0, 'Sélectionner une ligne')] + [(l.id, l.nom) for l in lignes]
    
    if form.validate_on_submit():
        try:
            rapport = RapportTransport()
            form.populate_obj(rapport)
            
            # Validation des données
            if rapport.poste_id == 0:
                rapport.poste_id = None
            if rapport.ligne_id == 0:
                rapport.ligne_id = None
            
            if not rapport.poste_id and not rapport.ligne_id:
                flash('Vous devez sélectionner au moins un poste ou une ligne.', 'error')
                return render_template('transport/rapports/formulaire.html', 
                                     form=form, mode='creation')
            
            rapport.save()
            
            flash('Rapport de transport créé avec succès.', 'success')
            return redirect(url_for('transport.detail_rapport', id=rapport.id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la création du rapport : {str(e)}', 'error')
    
    return render_template('transport/rapports/formulaire.html', form=form, mode='creation')

# API Routes
@bp.route('/api/statistiques')
@login_required
def api_statistiques():
    """API pour récupérer les statistiques de transport"""
    
    # Période (défaut: 30 derniers jours)
    periode = request.args.get('periode', '30j')
    
    if periode == '7j':
        date_debut = datetime.now() - timedelta(days=7)
    elif periode == '30j':
        date_debut = datetime.now() - timedelta(days=30)
    elif periode == '1an':
        date_debut = datetime.now() - timedelta(days=365)
    else:
        date_debut = datetime.now() - timedelta(days=30)
    
    # Requêtes selon les permissions
    if current_user.is_admin():
        query_base = db.session.query
    else:
        query_base = db.session.query
    
    # Statistiques générales
    if current_user.is_admin():
        total_lignes = LigneTransport.query.filter_by(actif=True).count()
        total_postes = PosteTransport.query.filter_by(actif=True).count()
    else:
        total_lignes = LigneTransport.query.filter_by(
            operateur_id=current_user.operateur_id,
            actif=True
        ).count()
        total_postes = PosteTransport.query.filter_by(
            operateur_id=current_user.operateur_id,
            actif=True
        ).count()
    
    # Disponibilité moyenne
    rapports_periode = RapportTransport.query.filter(
        RapportTransport.periode_debut >= date_debut.date(),
        RapportTransport.actif == True
    )
    
    if not current_user.is_admin():
        rapports_periode = rapports_periode.join(PosteTransport).filter(
            PosteTransport.operateur_id == current_user.operateur_id
        )
    
    rapports = rapports_periode.all()
    
    if rapports:
        disponibilite_moyenne = sum([r.disponibilite for r in rapports if r.disponibilite]) / len(rapports)
        fiabilite_moyenne = sum([r.fiabilite for r in rapports if r.fiabilite]) / len(rapports)
    else:
        disponibilite_moyenne = 0
        fiabilite_moyenne = 0
    
    return jsonify({
        'total_lignes': total_lignes,
        'total_postes': total_postes,
        'disponibilite_moyenne': round(disponibilite_moyenne, 2),
        'fiabilite_moyenne': round(fiabilite_moyenne, 2),
        'periode': periode
    })

# Fonctions utilitaires
def generer_donnees_graphiques_transport(lignes, postes):
    """Générer les données pour les graphiques du dashboard transport"""
    
    donnees = {
        'repartition_tension': {},
        'statuts_lignes': {},
        'statuts_postes': {},
        'evolution_indisponibilites': []
    }
    
    # Répartition par niveau de tension
    for ligne in lignes:
        tension = f"{ligne.tension_nominale} kV"
        donnees['repartition_tension'][tension] = donnees['repartition_tension'].get(tension, 0) + 1
    
    # Statuts des lignes
    for ligne in lignes:
        statut = ligne.statut or 'Non défini'
        donnees['statuts_lignes'][statut] = donnees['statuts_lignes'].get(statut, 0) + 1
    
    # Statuts des postes
    for poste in postes:
        statut = poste.statut or 'Non défini'
        donnees['statuts_postes'][statut] = donnees['statuts_postes'].get(statut, 0) + 1
    
    return donnees

def generer_donnees_performance_ligne(ligne):
    """Générer les données de performance pour une ligne"""
    
    # Récupérer les rapports des 12 derniers mois
    date_limite = datetime.now() - timedelta(days=365)
    
    rapports = RapportTransport.query.filter(
        RapportTransport.ligne_id == ligne.id,
        RapportTransport.periode_debut >= date_limite.date(),
        RapportTransport.actif == True
    ).order_by(RapportTransport.periode_debut.asc()).all()
    
    donnees = {
        'labels': [],
        'disponibilite': [],
        'fiabilite': [],
        'charge': []
    }
    
    for rapport in rapports:
        donnees['labels'].append(rapport.periode_debut.strftime('%m/%Y'))
        # Disponibilité basée sur le taux d'utilisation
        donnees['disponibilite'].append(rapport.taux_utilisation or 0)
        # Fiabilité calculée à partir des incidents (100% - impact des incidents)
        fiabilite = max(0, 100 - (rapport.nombre_incidents or 0) * 10)  # Estimation simple
        donnees['fiabilite'].append(fiabilite)
        donnees['charge'].append(rapport.charge_moyenne or 0)
    
    return donnees

def generer_donnees_charge_poste(poste):
    """Générer les données de charge pour un poste"""
    
    # Données simulées pour l'exemple - à remplacer par des vraies données
    from random import randint
    
    donnees = {
        'labels': [f"H{h:02d}" for h in range(0, 24)],
        'charge_actuelle': [randint(40, 95) for _ in range(24)],
        'charge_prevue': [randint(30, 85) for _ in range(24)]
    }
    
    return donnees