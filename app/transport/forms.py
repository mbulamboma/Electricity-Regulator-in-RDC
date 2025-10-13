"""
Formulaires pour le module Transport
"""
from flask_wtf import FlaskForm
from wtforms import (StringField, FloatField, IntegerField, SelectField, 
                     TextAreaField, DateField, BooleanField, FieldList, 
                     FormField, HiddenField)
from wtforms.validators import DataRequired, Optional, NumberRange, Length
from wtforms.widgets import TextArea
from app.utils.helpers import safe_int_coerce


class LigneTransportForm(FlaskForm):
    """Formulaire pour les lignes de transport"""
    
    # Relation avec l'opérateur
    operateur_id = SelectField('Opérateur', coerce=safe_int_coerce, validators=[DataRequired()])
    
    # Informations de base
    nom = StringField('Nom de la ligne', validators=[DataRequired(), Length(max=200)])
    code = StringField('Code', validators=[DataRequired(), Length(max=50)])
    designation = StringField('Désignation', validators=[Optional(), Length(max=300)])
    
    # Caractéristiques électriques
    tension_nominale = FloatField('Tension nominale (kV)', validators=[DataRequired(), NumberRange(min=0)])
    longueur_totale = FloatField('Longueur totale (km)', validators=[Optional(), NumberRange(min=0)])
    nombre_circuits = IntegerField('Nombre de circuits', validators=[Optional(), NumberRange(min=1)], default=1)
    type_ligne = SelectField('Type de ligne', choices=[
        ('aerienne', 'Aérienne'),
        ('souterraine', 'Souterraine'),
        ('mixte', 'Mixte')
    ], validators=[Optional()])
    
    # Points de connexion
    poste_depart = StringField('Poste de départ', validators=[Optional(), Length(max=200)])
    poste_arrivee = StringField('Poste d\'arrivée', validators=[Optional(), Length(max=200)])
    
    # Caractéristiques techniques
    type_conducteur = StringField('Type de conducteur', validators=[Optional(), Length(max=100)])
    section_conducteur = FloatField('Section conducteur (mm²)', validators=[Optional(), NumberRange(min=0)])
    nombre_conducteurs_par_phase = IntegerField('Conducteurs par phase', validators=[Optional(), NumberRange(min=1)], default=1)
    capacite_thermique = FloatField('Capacité thermique (A)', validators=[Optional(), NumberRange(min=0)])
    capacite_transport = FloatField('Capacité de transport (MVA)', validators=[Optional(), NumberRange(min=0)])
    
    # Support et isolation
    type_supports = StringField('Type de supports', validators=[Optional(), Length(max=100)])
    hauteur_moyenne_supports = FloatField('Hauteur moyenne supports (m)', validators=[Optional(), NumberRange(min=0)])
    portee_moyenne = FloatField('Portée moyenne (m)', validators=[Optional(), NumberRange(min=0)])
    type_isolateurs = StringField('Type d\'isolateurs', validators=[Optional(), Length(max=100)])
    
    # Protection
    conducteur_terre = BooleanField('Conducteur de terre')
    cable_garde = BooleanField('Câble de garde')
    systeme_protection = StringField('Système de protection', validators=[Optional(), Length(max=200)])
    
    # Exploitation
    date_mise_service = DateField('Date de mise en service', validators=[Optional()])
    statut = SelectField('Statut', choices=[
        ('en_service', 'En service'),
        ('hors_service', 'Hors service'),
        ('maintenance', 'En maintenance')
    ], default='en_service')
    proprietaire = StringField('Propriétaire', validators=[Optional(), Length(max=200)])
    exploitant = StringField('Exploitant', validators=[Optional(), Length(max=200)])
    
    # Performance
    taux_indisponibilite = FloatField('Taux d\'indisponibilité (%)', validators=[Optional(), NumberRange(min=0, max=100)], default=0.0)
    nombre_defauts_annuels = IntegerField('Défauts annuels', validators=[Optional(), NumberRange(min=0)], default=0)
    duree_moyenne_coupures = FloatField('Durée moyenne coupures (min)', validators=[Optional(), NumberRange(min=0)], default=0.0)
    
    # Maintenance
    date_derniere_inspection = DateField('Dernière inspection', validators=[Optional()])
    periodicite_inspection = IntegerField('Périodicité inspection (mois)', validators=[Optional(), NumberRange(min=1)], default=12)
    date_derniere_maintenance = DateField('Dernière maintenance', validators=[Optional()])
    
    # Observations
    observations = TextAreaField('Observations', validators=[Optional()], widget=TextArea())
    
    def __init__(self, *args, **kwargs):
        super(LigneTransportForm, self).__init__(*args, **kwargs)
        # Configurer les choix d'opérateurs selon les permissions
        from app.utils.permissions import get_operateur_choices, get_default_operateur_id
        self.operateur_id.choices = get_operateur_choices()
        # Définir la valeur par défaut si non admin
        if not kwargs.get('obj') and get_default_operateur_id():
            self.operateur_id.data = get_default_operateur_id()


class PosteTransportForm(FlaskForm):
    """Formulaire pour les postes de transport"""
    
    # Relation avec l'opérateur
    operateur_id = SelectField('Opérateur', coerce=safe_int_coerce, validators=[DataRequired()])
    
    # Informations de base
    nom = StringField('Nom du poste', validators=[DataRequired(), Length(max=200)])
    code = StringField('Code', validators=[DataRequired(), Length(max=50)])
    type_poste = SelectField('Type de poste', choices=[
        ('transformation', 'Transformation'),
        ('repartition', 'Répartition'),
        ('distribution', 'Distribution')
    ], validators=[Optional()])
    
    # Localisation
    localisation = StringField('Localisation', validators=[Optional(), Length(max=200)])
    province = SelectField('Province', choices=[
        ('kinshasa', 'Kinshasa'),
        ('bas_congo', 'Bas-Congo'),
        ('bandundu', 'Bandundu'),
        ('equateur', 'Équateur'),
        ('orientale', 'Province Orientale'),
        ('nord_kivu', 'Nord-Kivu'),
        ('sud_kivu', 'Sud-Kivu'),
        ('maniema', 'Maniema'),
        ('katanga', 'Katanga'),
        ('kasai_oriental', 'Kasaï Oriental'),
        ('kasai_occidental', 'Kasaï Occidental')
    ], validators=[Optional()])
    latitude = FloatField('Latitude', validators=[Optional(), NumberRange(min=-90, max=90)])
    longitude = FloatField('Longitude', validators=[Optional(), NumberRange(min=-180, max=180)])
    altitude = FloatField('Altitude (m)', validators=[Optional()])
    
    # Niveaux de tension
    tension_primaire = FloatField('Tension primaire (kV)', validators=[Optional(), NumberRange(min=0)])
    tension_secondaire = FloatField('Tension secondaire (kV)', validators=[Optional(), NumberRange(min=0)])
    tension_tertiaire = FloatField('Tension tertiaire (kV)', validators=[Optional(), NumberRange(min=0)])
    
    # Configuration
    nombre_transformateurs = IntegerField('Nombre de transformateurs', validators=[Optional(), NumberRange(min=0)], default=0)
    puissance_installee = FloatField('Puissance installée (MVA)', validators=[Optional(), NumberRange(min=0)])
    puissance_disponible = FloatField('Puissance disponible (MVA)', validators=[Optional(), NumberRange(min=0)])
    schema_unifilaire = SelectField('Schéma unifilaire', choices=[
        ('simple_barre', 'Simple barre'),
        ('double_barre', 'Double barre'),
        ('disjoncteur_demi', 'Disjoncteur et demi'),
        ('barre_transfert', 'Barre de transfert')
    ], validators=[Optional()])
    
    # Équipements de protection
    nombre_disjoncteurs = IntegerField('Nombre de disjoncteurs', validators=[Optional(), NumberRange(min=0)], default=0)
    nombre_sectionneurs = IntegerField('Nombre de sectionneurs', validators=[Optional(), NumberRange(min=0)], default=0)
    parafoudres = BooleanField('Parafoudres')
    
    # Surveillance et contrôle
    systeme_scada = BooleanField('Système SCADA')
    telecommande = BooleanField('Télécommande')
    telemesure = BooleanField('Télémesure')
    
    # Exploitation
    date_mise_service = DateField('Date de mise en service', validators=[Optional()])
    statut = SelectField('Statut', choices=[
        ('en_service', 'En service'),
        ('hors_service', 'Hors service'),
        ('maintenance', 'En maintenance')
    ], default='en_service')
    regime_neutre = SelectField('Régime de neutre', choices=[
        ('direct', 'Direct'),
        ('resistance', 'Résistance'),
        ('bobine', 'Bobine de Petersen')
    ], validators=[Optional()])
    
    # Performance
    taux_disponibilite = FloatField('Taux de disponibilité (%)', validators=[Optional(), NumberRange(min=0, max=100)], default=100.0)
    nombre_incidents_annuels = IntegerField('Incidents annuels', validators=[Optional(), NumberRange(min=0)], default=0)
    duree_moyenne_indisponibilite = FloatField('Durée moyenne indisponibilité (h)', validators=[Optional(), NumberRange(min=0)], default=0.0)
    
    # Maintenance
    date_derniere_maintenance = DateField('Dernière maintenance', validators=[Optional()])
    periodicite_maintenance = IntegerField('Périodicité maintenance (mois)', validators=[Optional(), NumberRange(min=1)], default=6)
    
    # Sécurité et environnement
    cloture_securite = BooleanField('Clôture de sécurité')
    systeme_incendie = BooleanField('Système anti-incendie')
    bac_retention_huile = BooleanField('Bac de rétention d\'huile')
    
    # Observations
    description = TextAreaField('Description', validators=[Optional()], widget=TextArea())
    observations = TextAreaField('Observations', validators=[Optional()], widget=TextArea())
    
    def __init__(self, *args, **kwargs):
        super(PosteTransportForm, self).__init__(*args, **kwargs)
        # Configurer les choix d'opérateurs selon les permissions
        from app.utils.permissions import get_operateur_choices, get_default_operateur_id
        self.operateur_id.choices = get_operateur_choices()
        # Définir la valeur par défaut si non admin
        if not kwargs.get('obj') and get_default_operateur_id():
            self.operateur_id.data = get_default_operateur_id()


class TransformateurTransportForm(FlaskForm):
    """Formulaire pour les transformateurs de transport"""
    
    # Relations
    poste_id = SelectField('Poste de transport', coerce=safe_int_coerce, validators=[DataRequired()])
    
    # Identification
    nom = StringField('Nom du transformateur', validators=[DataRequired(), Length(max=200)])
    numero_serie = StringField('Numéro de série', validators=[Optional(), Length(max=100)])
    constructeur = StringField('Constructeur', validators=[Optional(), Length(max=100)])
    annee_fabrication = IntegerField('Année de fabrication', validators=[Optional(), NumberRange(min=1900, max=2030)])
    
    # Caractéristiques électriques
    puissance_nominale = FloatField('Puissance nominale (MVA)', validators=[DataRequired(), NumberRange(min=0)])
    tension_primaire = FloatField('Tension primaire (kV)', validators=[DataRequired(), NumberRange(min=0)])
    tension_secondaire = FloatField('Tension secondaire (kV)', validators=[DataRequired(), NumberRange(min=0)])
    tension_tertiaire = FloatField('Tension tertiaire (kV)', validators=[Optional(), NumberRange(min=0)])
    couplage = StringField('Couplage', validators=[Optional(), Length(max=20)])
    
    # Caractéristiques techniques
    type_refroidissement = SelectField('Type de refroidissement', choices=[
        ('ONAN', 'ONAN - Huile naturelle, air naturel'),
        ('ONAF', 'ONAF - Huile naturelle, air forcé'),
        ('OFAF', 'OFAF - Huile forcée, air forcé'),
        ('ODAF', 'ODAF - Huile dirigée, air forcé')
    ], validators=[Optional()])
    poids_total = FloatField('Poids total (tonnes)', validators=[Optional(), NumberRange(min=0)])
    volume_huile = FloatField('Volume d\'huile (litres)', validators=[Optional(), NumberRange(min=0)])
    type_huile = StringField('Type d\'huile', validators=[Optional(), Length(max=100)])
    
    # Impédances et pertes
    impedance_cc = FloatField('Impédance court-circuit (%)', validators=[Optional(), NumberRange(min=0)])
    pertes_vide = FloatField('Pertes à vide (kW)', validators=[Optional(), NumberRange(min=0)])
    pertes_charge = FloatField('Pertes en charge (kW)', validators=[Optional(), NumberRange(min=0)])
    courant_vide = FloatField('Courant à vide (%)', validators=[Optional(), NumberRange(min=0)])
    
    # Réglage
    changeur_prises = BooleanField('Changeur de prises')
    nombre_prises = IntegerField('Nombre de prises', validators=[Optional(), NumberRange(min=0)], default=0)
    plage_reglage = FloatField('Plage de réglage (%)', validators=[Optional(), NumberRange(min=0)])
    pas_reglage = FloatField('Pas de réglage (%)', validators=[Optional(), NumberRange(min=0)])
    
    # État et maintenance
    statut = SelectField('Statut', choices=[
        ('en_service', 'En service'),
        ('hors_service', 'Hors service'),
        ('maintenance', 'En maintenance'),
        ('reserve', 'En réserve')
    ], default='en_service')
    date_mise_service = DateField('Date de mise en service', validators=[Optional()])
    date_derniere_maintenance = DateField('Dernière maintenance', validators=[Optional()])
    type_derniere_maintenance = StringField('Type dernière maintenance', validators=[Optional(), Length(max=100)])
    prochaine_maintenance = DateField('Prochaine maintenance', validators=[Optional()])
    
    # Surveillance
    temperature_huile = FloatField('Température huile (°C)', validators=[Optional()])
    temperature_enroulements = FloatField('Température enroulements (°C)', validators=[Optional()])
    niveau_huile = SelectField('Niveau d\'huile', choices=[
        ('normal', 'Normal'),
        ('bas', 'Bas'),
        ('critique', 'Critique')
    ], validators=[Optional()])
    pression_huile = FloatField('Pression huile (bar)', validators=[Optional()])
    
    # Tests et analyses
    date_derniere_analyse_huile = DateField('Dernière analyse huile', validators=[Optional()])
    resultat_analyse_huile = TextAreaField('Résultat analyse huile', validators=[Optional()], widget=TextArea())
    date_dernier_test_isolement = DateField('Dernier test isolement', validators=[Optional()])
    resistance_isolement = FloatField('Résistance isolement (MΩ)', validators=[Optional(), NumberRange(min=0)])
    
    # Observations
    observations = TextAreaField('Observations', validators=[Optional()], widget=TextArea())
    
    def __init__(self, *args, **kwargs):
        super(TransformateurTransportForm, self).__init__(*args, **kwargs)
        # Configurer les choix de postes selon les permissions
        from app.models.transport import PosteTransport
        from flask_login import current_user
        
        if current_user.is_admin():
            postes = PosteTransport.query.filter_by(actif=True).all()
        elif current_user.operateur_id:
            postes = PosteTransport.query.filter_by(
                operateur_id=current_user.operateur_id,
                actif=True
            ).all()
        else:
            postes = []
        
        self.poste_id.choices = [('', 'Sélectionner un poste')] + [
            (p.id, f"{p.nom} ({p.operateur.nom})") for p in postes
        ]


class RapportTransportForm(FlaskForm):
    """Formulaire pour les rapports de transport"""
    
    # Sélection ligne
    ligne_id = SelectField('Ligne de transport', coerce=safe_int_coerce, validators=[DataRequired()])
    
    # Période
    annee = IntegerField('Année', validators=[DataRequired(), NumberRange(min=2000, max=2050)])
    mois = SelectField('Mois', choices=[
        (1, 'Janvier'), (2, 'Février'), (3, 'Mars'), (4, 'Avril'),
        (5, 'Mai'), (6, 'Juin'), (7, 'Juillet'), (8, 'Août'),
        (9, 'Septembre'), (10, 'Octobre'), (11, 'Novembre'), (12, 'Décembre')
    ], coerce=safe_int_coerce, validators=[DataRequired()])
    periode_debut = DateField('Début de période', validators=[DataRequired()])
    periode_fin = DateField('Fin de période', validators=[DataRequired()])
    
    # Énergie transitée
    energie_transitee = FloatField('Énergie transitée (MWh)', validators=[Optional(), NumberRange(min=0)])
    energie_maximale = FloatField('Puissance maximale (MW)', validators=[Optional(), NumberRange(min=0)])
    heure_pointe = StringField('Heure de pointe (HH:MM)', validators=[Optional(), Length(max=10)])
    energie_minimale = FloatField('Puissance minimale (MW)', validators=[Optional(), NumberRange(min=0)])
    heure_creuse = StringField('Heure creuse (HH:MM)', validators=[Optional(), Length(max=10)])
    
    # Facteur de charge et utilisation
    facteur_charge = FloatField('Facteur de charge (%)', validators=[Optional(), NumberRange(min=0, max=100)])
    taux_utilisation = FloatField('Taux d\'utilisation (%)', validators=[Optional(), NumberRange(min=0, max=100)])
    charge_moyenne = FloatField('Charge moyenne (MW)', validators=[Optional(), NumberRange(min=0)])
    
    # Qualité et fiabilité
    nombre_incidents = IntegerField('Nombre d\'incidents', validators=[Optional(), NumberRange(min=0)], default=0)
    duree_total_incidents = FloatField('Durée totale incidents (h)', validators=[Optional(), NumberRange(min=0)], default=0.0)
    energie_non_fournie = FloatField('Énergie non fournie (MWh)', validators=[Optional(), NumberRange(min=0)], default=0.0)
    saidi = FloatField('SAIDI (minutes)', validators=[Optional(), NumberRange(min=0)], default=0.0)
    saifi = FloatField('SAIFI (interruptions/client)', validators=[Optional(), NumberRange(min=0)], default=0.0)
    
    # Maintenance
    maintenances_programmees = IntegerField('Maintenances programmées', validators=[Optional(), NumberRange(min=0)], default=0)
    duree_maintenances_programmees = FloatField('Durée maintenances programmées (h)', validators=[Optional(), NumberRange(min=0)], default=0.0)
    maintenances_urgentes = IntegerField('Maintenances urgentes', validators=[Optional(), NumberRange(min=0)], default=0)
    duree_maintenances_urgentes = FloatField('Durée maintenances urgentes (h)', validators=[Optional(), NumberRange(min=0)], default=0.0)
    
    # Pertes techniques
    pertes_ligne = FloatField('Pertes ligne (%)', validators=[Optional(), NumberRange(min=0, max=100)], default=0.0)
    pertes_transformateurs = FloatField('Pertes transformateurs (%)', validators=[Optional(), NumberRange(min=0, max=100)], default=0.0)
    pertes_totales = FloatField('Pertes totales (%)', validators=[Optional(), NumberRange(min=0, max=100)], default=0.0)
    
    # Conditions de fonctionnement
    temperature_moyenne = FloatField('Température moyenne (°C)', validators=[Optional()])
    temperature_maximale = FloatField('Température maximale (°C)', validators=[Optional()])
    humidite_moyenne = FloatField('Humidité moyenne (%)', validators=[Optional(), NumberRange(min=0, max=100)])
    vitesse_vent_moyenne = FloatField('Vitesse vent moyenne (m/s)', validators=[Optional(), NumberRange(min=0)])
    
    # Incidents et événements
    description_incidents = TextAreaField('Description des incidents', validators=[Optional()], widget=TextArea())
    causes_incidents = TextAreaField('Causes des incidents', validators=[Optional()], widget=TextArea())
    actions_correctives = TextAreaField('Actions correctives', validators=[Optional()], widget=TextArea())
    
    # Performance environnementale
    emissions_sf6 = FloatField('Émissions SF6 (kg eq CO2)', validators=[Optional(), NumberRange(min=0)], default=0.0)
    consommation_auxiliaires = FloatField('Consommation auxiliaires (kWh)', validators=[Optional(), NumberRange(min=0)], default=0.0)
    
    # Observations
    observations = TextAreaField('Observations', validators=[Optional()], widget=TextArea())
    
    def __init__(self, *args, **kwargs):
        super(RapportTransportForm, self).__init__(*args, **kwargs)
        # Configurer les choix de lignes selon les permissions
        from app.models.transport import LigneTransport
        from flask_login import current_user
        
        if current_user.is_admin():
            lignes = LigneTransport.query.filter_by(actif=True).all()
        elif current_user.operateur_id:
            lignes = LigneTransport.query.filter_by(
                operateur_id=current_user.operateur_id,
                actif=True
            ).all()
        else:
            lignes = []
        
        self.ligne_id.choices = [('', 'Sélectionner une ligne')] + [
            (l.id, f"{l.nom} ({l.operateur.nom})") for l in lignes
        ]


class FiltreTransportForm(FlaskForm):
    """Formulaire de filtrage pour les infrastructures de transport"""
    
    # Filtres par type d'infrastructure
    type_infrastructure = SelectField('Type d\'infrastructure', choices=[
        ('', 'Tous les types'),
        ('ligne', 'Lignes de transport'),
        ('poste', 'Postes de transformation')
    ], validators=[Optional()])
    
    # Filtres par niveau de tension
    tension_min = FloatField('Tension minimum (kV)', validators=[Optional(), NumberRange(min=0)])
    tension_max = FloatField('Tension maximum (kV)', validators=[Optional(), NumberRange(min=0)])
    
    # Filtres par province/région
    province = SelectField('Province', choices=[
        ('', 'Toutes les provinces'),
        ('kinshasa', 'Kinshasa'),
        ('bas_congo', 'Bas-Congo'),
        ('bandundu', 'Bandundu'),
        ('equateur', 'Équateur'),
        ('orientale', 'Province Orientale'),
        ('nord_kivu', 'Nord-Kivu'),
        ('sud_kivu', 'Sud-Kivu'),
        ('maniema', 'Maniema'),
        ('katanga', 'Katanga'),
        ('kasai_oriental', 'Kasaï Oriental'),
        ('kasai_occidental', 'Kasaï Occidental')
    ], validators=[Optional()])
    
    # Filtres par statut
    statut = SelectField('Statut', choices=[
        ('', 'Tous les statuts'),
        ('operationnel', 'Opérationnel'),
        ('maintenance', 'En maintenance'),
        ('hors_service', 'Hors service'),
        ('construction', 'En construction'),
        ('projet', 'En projet')
    ], validators=[Optional()])
    
    # Filtres par opérateur
    operateur = SelectField('Opérateur', choices=[], validators=[Optional()])
    
    # Filtres par capacité/performance
    capacite_min = FloatField('Capacité minimum (MVA)', validators=[Optional(), NumberRange(min=0)])
    capacite_max = FloatField('Capacité maximum (MVA)', validators=[Optional(), NumberRange(min=0)])
    
    # Filtres par date
    date_debut = DateField('Date de début', validators=[Optional()])
    date_fin = DateField('Date de fin', validators=[Optional()])
    
    # Recherche textuelle
    recherche = StringField('Recherche', validators=[Optional(), Length(max=200)], 
                           render_kw={'placeholder': 'Nom, code, ou description...'})
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Les choix pour l'opérateur seront remplis dynamiquement
        # depuis la vue avec les opérateurs disponibles