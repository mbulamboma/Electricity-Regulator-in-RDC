"""
Routes pour la collecte mensuelle des données des opérateurs
Évite les fake data en permettant aux opérateurs de soumettre leurs vraies données
"""
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date
from app.collecte import collecte_bp
from app.collecte.forms import CollecteDonneesMensuellesForm, CollecteProjetNouveauForm
from app.models.collecte_donnees import CollecteDonneesMensuelles, CollecteProjetNouveau
from app.models.operateurs import Operateur
from app.utils.decorators import role_required
from app.utils.permissions import can_access_operateur
from app.extensions import db


@collecte_bp.route('/')
@login_required
@role_required('operateur', 'admin_operateur', 'super_admin')
def index():
    """Page d'accueil de la collecte de données"""
    
    # Déterminer l'opérateur à afficher
    if current_user.role == 'super_admin':
        # Super admin peut voir tous les opérateurs
        operateurs = Operateur.query.filter_by(actif=True).all()
        operateur_id = request.args.get('operateur_id', type=int)
        if operateur_id:
            operateur_actuel = Operateur.query.get_or_404(operateur_id)
        else:
            operateur_actuel = operateurs[0] if operateurs else None
    else:
        # Opérateur ne voit que ses propres données
        operateur_actuel = current_user.operateur
        operateurs = [operateur_actuel] if operateur_actuel else []
    
    if not operateur_actuel:
        flash("Aucun opérateur associé à votre compte.", "warning")
        return redirect(url_for('main.index'))
    
    # Récupérer les collectes récentes
    collectes_recentes = CollecteDonneesMensuelles.query.filter(
        CollecteDonneesMensuelles.operateur_id == operateur_actuel.id,
        CollecteDonneesMensuelles.actif == True
    ).order_by(
        CollecteDonneesMensuelles.annee.desc(),
        CollecteDonneesMensuelles.mois.desc()
    ).limit(12).all()
    
    # Statistiques de collecte
    total_collectes = CollecteDonneesMensuelles.query.filter(
        CollecteDonneesMensuelles.operateur_id == operateur_actuel.id,
        CollecteDonneesMensuelles.actif == True
    ).count()
    
    collectes_validees = CollecteDonneesMensuelles.query.filter(
        CollecteDonneesMensuelles.operateur_id == operateur_actuel.id,
        CollecteDonneesMensuelles.statut == 'valide',
        CollecteDonneesMensuelles.actif == True
    ).count()
    
    collectes_en_attente = CollecteDonneesMensuelles.query.filter(
        CollecteDonneesMensuelles.operateur_id == operateur_actuel.id,
        CollecteDonneesMensuelles.statut.in_(['soumis', 'en_validation']),
        CollecteDonneesMensuelles.actif == True
    ).count()
    
    # Projets récents
    projets_recents = CollecteProjetNouveau.query.filter(
        CollecteProjetNouveau.operateur_id == operateur_actuel.id,
        CollecteProjetNouveau.actif == True
    ).order_by(CollecteProjetNouveau.date_soumission.desc()).limit(5).all()
    
    return render_template('collecte/index.html',
                         operateur_actuel=operateur_actuel,
                         operateurs=operateurs,
                         collectes_recentes=collectes_recentes,
                         projets_recents=projets_recents,
                         total_collectes=total_collectes,
                         collectes_validees=collectes_validees,
                         collectes_en_attente=collectes_en_attente)


@collecte_bp.route('/nouvelle-collecte')
@login_required
@role_required('operateur', 'admin_operateur')
def nouvelle_collecte():
    """Formulaire pour une nouvelle collecte mensuelle"""
    
    if not current_user.operateur:
        flash("Vous devez être associé à un opérateur pour collecter des données.", "error")
        return redirect(url_for('collecte.index'))
    
    form = CollecteDonneesMensuellesForm()
    
    return render_template('collecte/nouvelle_collecte.html',
                         form=form,
                         operateur=current_user.operateur)


@collecte_bp.route('/soumettre-collecte', methods=['POST'])
@login_required
@role_required('operateur', 'admin_operateur')
def soumettre_collecte():
    """Traiter la soumission d'une collecte mensuelle"""
    
    if not current_user.operateur:
        flash("Vous devez être associé à un opérateur pour collecter des données.", "error")
        return redirect(url_for('collecte.index'))
    
    form = CollecteDonneesMensuellesForm()
    
    if form.validate_on_submit():
        # Vérifier si une collecte existe déjà
        existing = CollecteDonneesMensuelles.query.filter(
            CollecteDonneesMensuelles.operateur_id == current_user.operateur.id,
            CollecteDonneesMensuelles.annee == int(form.annee.data),
            CollecteDonneesMensuelles.mois == int(form.mois.data),
            CollecteDonneesMensuelles.actif == True
        ).first()
        
        if existing:
            if existing.statut != 'brouillon':
                flash(f"Une collecte existe déjà pour {form.mois.data}/{form.annee.data} avec le statut: {existing.statut}", "error")
                return render_template('collecte/nouvelle_collecte.html',
                                     form=form, operateur=current_user.operateur)
            else:
                # Mettre à jour le brouillon existant
                collecte = existing
        else:
            # Créer une nouvelle collecte
            collecte = CollecteDonneesMensuelles(
                operateur_id=current_user.operateur.id,
                annee=int(form.annee.data),
                mois=int(form.mois.data),
                soumis_par=current_user.id
            )
        
        # Déterminer le statut selon le bouton cliqué
        if 'save_draft' in request.form:
            collecte.statut = 'brouillon'
            message_success = "Brouillon enregistré avec succès"
        else:
            collecte.statut = 'soumis'
            collecte.date_soumission = datetime.utcnow()
            message_success = "Collecte soumise avec succès à l'ARE pour validation"
        
        # Remplir les données du formulaire
        collecte.chiffre_affaires_mois = form.chiffre_affaires_mois.data
        collecte.investissements_realises_mois = form.investissements_realises_mois.data
        collecte.cout_combustible_mois = form.cout_combustible_mois.data
        collecte.tarifs_moyens_ht = form.tarifs_moyens_ht.data
        collecte.tarifs_moyens_mt = form.tarifs_moyens_mt.data
        collecte.tarifs_moyens_bt = form.tarifs_moyens_bt.data
        
        collecte.nouveaux_clients_ht_mois = form.nouveaux_clients_ht_mois.data
        collecte.nouveaux_clients_mt_mois = form.nouveaux_clients_mt_mois.data
        collecte.nouveaux_clients_bt_mois = form.nouveaux_clients_bt_mois.data
        collecte.clients_deconnectes_ht_mois = form.clients_deconnectes_ht_mois.data
        collecte.clients_deconnectes_mt_mois = form.clients_deconnectes_mt_mois.data
        collecte.clients_deconnectes_bt_mois = form.clients_deconnectes_bt_mois.data
        
        collecte.nouvelles_localites_desservies = form.nouvelles_localites_desservies.data
        collecte.longueur_nouveaux_reseaux_km = form.longueur_nouveaux_reseaux_km.data
        collecte.population_nouvelle_couverte = form.population_nouvelle_couverte.data
        
        collecte.duree_moyenne_coupures_heures = form.duree_moyenne_coupures_heures.data
        collecte.nombre_incidents_techniques = form.nombre_incidents_techniques.data
        collecte.taux_disponibilite_reseau = form.taux_disponibilite_reseau.data
        
        collecte.emissions_co2_tonnes = form.emissions_co2_tonnes.data
        collecte.consommation_eau_m3 = form.consommation_eau_m3.data
        
        collecte.observations_mois = form.observations_mois.data
        collecte.difficultees_rencontrees = form.difficultees_rencontrees.data
        
        collecte.save()
        
        flash(message_success, "success")
        return redirect(url_for('collecte.voir_collecte', collecte_id=collecte.id))
    
    # Erreurs de validation
    return render_template('collecte/nouvelle_collecte.html',
                         form=form,
                         operateur=current_user.operateur)


@collecte_bp.route('/collecte/<int:collecte_id>')
@login_required
def voir_collecte(collecte_id):
    """Voir le détail d'une collecte"""
    
    collecte = CollecteDonneesMensuelles.query.get_or_404(collecte_id)
    
    # Vérification des permissions
    if current_user.role not in ['super_admin'] and current_user.operateur_id != collecte.operateur_id:
        flash("Vous n'avez pas l'autorisation de voir cette collecte.", "error")
        return redirect(url_for('collecte.index'))
    
    return render_template('collecte/voir_collecte.html', collecte=collecte)


@collecte_bp.route('/mes-collectes')
@login_required
@role_required('operateur', 'admin_operateur', 'super_admin')
def mes_collectes():
    """Liste des collectes de l'opérateur"""
    
    # Déterminer l'opérateur
    if current_user.role == 'super_admin':
        operateur_id = request.args.get('operateur_id', type=int)
        if operateur_id:
            if not can_access_operateur(operateur_id):
                flash("Accès non autorisé à cet opérateur.", "error")
                return redirect(url_for('collecte.index'))
            operateur = Operateur.query.get_or_404(operateur_id)
        else:
            operateur = None
    else:
        operateur = current_user.operateur
    
    if operateur:
        collectes = CollecteDonneesMensuelles.query.filter(
            CollecteDonneesMensuelles.operateur_id == operateur.id,
            CollecteDonneesMensuelles.actif == True
        ).order_by(
            CollecteDonneesMensuelles.annee.desc(),
            CollecteDonneesMensuelles.mois.desc()
        ).all()
    else:
        # Super admin sans opérateur spécifique - voir toutes les collectes
        collectes = CollecteDonneesMensuelles.query.filter(
            CollecteDonneesMensuelles.actif == True
        ).order_by(
            CollecteDonneesMensuelles.annee.desc(),
            CollecteDonneesMensuelles.mois.desc()
        ).all()
    
    return render_template('collecte/mes_collectes.html',
                         collectes=collectes,
                         operateur=operateur)


@collecte_bp.route('/nouveau-projet')
@login_required
@role_required('operateur', 'admin_operateur')
def nouveau_projet():
    """Formulaire pour soumettre un nouveau projet à l'ARE"""
    
    if not current_user.operateur:
        flash("Vous devez être associé à un opérateur pour soumettre un projet.", "error")
        return redirect(url_for('collecte.index'))
    
    form = CollecteProjetNouveauForm()
    
    return render_template('collecte/nouveau_projet.html',
                         form=form,
                         operateur=current_user.operateur)


@collecte_bp.route('/soumettre-projet', methods=['POST'])
@login_required
@role_required('operateur', 'admin_operateur')
def soumettre_projet():
    """Traiter la soumission d'un nouveau projet"""
    
    if not current_user.operateur:
        flash("Vous devez être associé à un opérateur pour soumettre un projet.", "error")
        return redirect(url_for('collecte.index'))
    
    form = CollecteProjetNouveauForm()
    
    if form.validate_on_submit():
        # Déterminer le statut selon le bouton cliqué
        if 'save_draft' in request.form:
            statut = 'brouillon'
            message_success = "Brouillon de projet enregistré avec succès"
        else:
            statut = 'soumis'
            message_success = "Projet soumis avec succès à l'ARE pour évaluation"
        
        # Créer le projet
        projet = CollecteProjetNouveau(
            operateur_id=current_user.operateur.id,
            nom_projet=form.nom_projet.data,
            type_projet=form.type_projet.data,
            description_projet=form.description_projet.data,
            capacite_prevue_mw=form.capacite_prevue_mw.data,
            longueur_prevue_km=form.longueur_prevue_km.data,
            tension_nominale_kv=form.tension_nominale_kv.data,
            province=form.province.data,
            localisation_precise=form.localisation_precise.data,
            cout_estime_usd=form.cout_estime_usd.data,
            financement_acquis=form.financement_acquis.data,
            source_financement=form.source_financement.data,
            date_debut_prevue=form.date_debut_prevue.data,
            duree_travaux_mois=form.duree_travaux_mois.data,
            date_mise_service_prevue=form.date_mise_service_prevue.data,
            population_beneficiaire=form.population_beneficiaire.data,
            emplois_crees=form.emplois_crees.data,
            etude_impact_realisee=form.etude_impact_realisee.data,
            autorisation_environnementale=form.autorisation_environnementale.data,
            etude_faisabilite_realisee=form.etude_faisabilite_realisee.data,
            commentaires_supplementaires=form.commentaires_supplementaires.data,
            statut=statut,
            soumis_par=current_user.id
        )
        
        if statut == 'soumis':
            projet.date_soumission = datetime.utcnow()
        
        projet.save()
        
        flash(message_success, "success")
        return redirect(url_for('collecte.voir_projet', projet_id=projet.id))
    
    # Erreurs de validation
    return render_template('collecte/nouveau_projet.html',
                         form=form,
                         operateur=current_user.operateur)


@collecte_bp.route('/projet/<int:projet_id>')
@login_required
def voir_projet(projet_id):
    """Voir le détail d'un projet"""
    
    projet = CollecteProjetNouveau.query.get_or_404(projet_id)
    
    # Vérification des permissions
    if current_user.role not in ['super_admin'] and current_user.operateur_id != projet.operateur_id:
        flash("Vous n'avez pas l'autorisation de voir ce projet.", "error")
        return redirect(url_for('collecte.index'))
    
    return render_template('collecte/voir_projet.html', projet=projet)


@collecte_bp.route('/mes-projets')
@login_required
@role_required('operateur', 'admin_operateur', 'super_admin')
def mes_projets():
    """Liste des projets de l'opérateur"""
    
    # Déterminer l'opérateur
    if current_user.role == 'super_admin':
        operateur_id = request.args.get('operateur_id', type=int)
        if operateur_id:
            operateur = Operateur.query.get_or_404(operateur_id)
        else:
            operateur = None
    else:
        operateur = current_user.operateur
    
    if operateur:
        projets = CollecteProjetNouveau.query.filter(
            CollecteProjetNouveau.operateur_id == operateur.id,
            CollecteProjetNouveau.actif == True
        ).order_by(CollecteProjetNouveau.date_soumission.desc()).all()
    else:
        # Super admin sans opérateur spécifique
        projets = CollecteProjetNouveau.query.filter(
            CollecteProjetNouveau.actif == True
        ).order_by(CollecteProjetNouveau.date_soumission.desc()).all()
    
    return render_template('collecte/mes_projets.html',
                         projets=projets,
                         operateur=operateur)


# API Routes pour l'administration ARE
@collecte_bp.route('/api/validation/<int:collecte_id>')
@login_required
@role_required('super_admin')
def api_valider_collecte(collecte_id):
    """API pour valider/rejeter une collecte (ARE seulement)"""
    
    collecte = CollecteDonneesMensuelles.query.get_or_404(collecte_id)
    action = request.args.get('action')  # 'valider' ou 'rejeter'
    
    if action == 'valider':
        collecte.statut = 'valide'
        collecte.date_validation = datetime.utcnow()
        collecte.valide_par = current_user.id
        message = "Collecte validée avec succès"
    elif action == 'rejeter':
        collecte.statut = 'rejete'
        collecte.date_validation = datetime.utcnow()
        collecte.valide_par = current_user.id
        message = "Collecte rejetée"
    else:
        return jsonify({'error': 'Action non valide'}), 400
    
    collecte.save()
    
    return jsonify({
        'success': True,
        'message': message,
        'nouveau_statut': collecte.statut
    })