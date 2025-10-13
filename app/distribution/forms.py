"""
Formulaires pour le module Distribution
"""
from flask_wtf import FlaskForm
from wtforms import (StringField, FloatField, IntegerField, SelectField, 
                     TextAreaField, DateField, BooleanField, FieldList, 
                     FormField, HiddenField)
from wtforms.validators import DataRequired, Optional, NumberRange, Length, ValidationError
from wtforms.widgets import TextArea
from app.utils.permissions import get_operateur_choices, get_default_operateur_id
from app.utils.helpers import safe_int_coerce


class ReseauDistributionForm(FlaskForm):
    """Formulaire pour les réseaux de distribution"""
    
    # Opérateur (requis)
    operateur_id = SelectField('Opérateur', coerce=safe_int_coerce, validators=[DataRequired()])
    
    # Informations de base
    nom = StringField('Nom du réseau', validators=[DataRequired(), Length(max=200)])
    code = StringField('Code', validators=[DataRequired(), Length(max=50)])
    type_reseau = SelectField('Type de réseau', choices=[
        ('urbain', 'Urbain'),
        ('rural', 'Rural'),
        ('industriel', 'Industriel')
    ], validators=[Optional()])
    
    # Zone de desserte
    zone_desserte = StringField('Zone de desserte', validators=[Optional(), Length(max=200)])
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
    commune = StringField('Commune', validators=[Optional(), Length(max=100)])
    superficie = FloatField('Superficie (km²)', validators=[Optional(), NumberRange(min=0)])
    
    # Coordonnées
    centre_latitude = FloatField('Latitude centre', validators=[Optional(), NumberRange(min=-90, max=90)])
    centre_longitude = FloatField('Longitude centre', validators=[Optional(), NumberRange(min=-180, max=180)])
    
    # Caractéristiques du réseau
    tension_distribution = FloatField('Tension distribution (kV)', validators=[DataRequired(), NumberRange(min=0)])
    tension_basse = FloatField('Tension basse (kV)', validators=[Optional(), NumberRange(min=0)], default=0.4)
    schema_exploitation = SelectField('Schéma d\'exploitation', choices=[
        ('radial', 'Radial'),
        ('boucle', 'Bouclé'),
        ('maille', 'Maillé')
    ], validators=[Optional()])
    
    # Lignes et infrastructure
    longueur_reseau_mt = FloatField('Longueur réseau MT (km)', validators=[Optional(), NumberRange(min=0)])
    longueur_reseau_bt = FloatField('Longueur réseau BT (km)', validators=[Optional(), NumberRange(min=0)])
    nombre_postes_source = IntegerField('Nombre postes source', validators=[Optional(), NumberRange(min=0)], default=0)
    nombre_postes_distribution = IntegerField('Nombre postes distribution', validators=[Optional(), NumberRange(min=0)], default=0)
    nombre_transformateurs_mt_bt = IntegerField('Nombre transformateurs MT/BT', validators=[Optional(), NumberRange(min=0)], default=0)
    
    # Type de réseau
    type_construction = SelectField('Type de construction', choices=[
        ('aerien', 'Aérien'),
        ('souterrain', 'Souterrain'),
        ('mixte', 'Mixte')
    ], validators=[Optional()])
    pourcentage_aerien = FloatField('Pourcentage aérien (%)', validators=[Optional(), NumberRange(min=0, max=100)], default=100.0)
    pourcentage_souterrain = FloatField('Pourcentage souterrain (%)', validators=[Optional(), NumberRange(min=0, max=100)], default=0.0)
    
    # Clientèle
    nombre_clients_total = IntegerField('Nombre clients total', validators=[Optional(), NumberRange(min=0)], default=0)
    nombre_clients_domestiques = IntegerField('Clients domestiques', validators=[Optional(), NumberRange(min=0)], default=0)
    nombre_clients_commerciaux = IntegerField('Clients commerciaux', validators=[Optional(), NumberRange(min=0)], default=0)
    nombre_clients_industriels = IntegerField('Clients industriels', validators=[Optional(), NumberRange(min=0)], default=0)
    nombre_clients_autres = IntegerField('Autres clients', validators=[Optional(), NumberRange(min=0)], default=0)
    
    # Puissance et énergie
    puissance_installee = FloatField('Puissance installée (MVA)', validators=[Optional(), NumberRange(min=0)])
    puissance_souscrite = FloatField('Puissance souscrite (MVA)', validators=[Optional(), NumberRange(min=0)])
    puissance_maximale = FloatField('Puissance maximale (MW)', validators=[Optional(), NumberRange(min=0)])
    demande_moyenne = FloatField('Demande moyenne (MW)', validators=[Optional(), NumberRange(min=0)])
    
    # Performance
    taux_electrification = FloatField('Taux d\'électrification (%)', validators=[Optional(), NumberRange(min=0, max=100)], default=0.0)
    densite_clientele = FloatField('Densité clientèle (clients/km²)', validators=[Optional(), NumberRange(min=0)], default=0.0)
    charge_lineique = FloatField('Charge linéique (kVA/km)', validators=[Optional(), NumberRange(min=0)], default=0.0)
    
    # Qualité de service
    saidi_objectif = FloatField('SAIDI objectif (min/an)', validators=[Optional(), NumberRange(min=0)], default=0.0)
    saifi_objectif = FloatField('SAIFI objectif (coupures/an)', validators=[Optional(), NumberRange(min=0)], default=0.0)
    taux_disponibilite_objectif = FloatField('Taux disponibilité objectif (%)', validators=[Optional(), NumberRange(min=0, max=100)], default=99.0)
    
    # Exploitation
    date_mise_service = DateField('Date de mise en service', validators=[Optional()])
    statut = SelectField('Statut', choices=[
        ('en_service', 'En service'),
        ('hors_service', 'Hors service'),
        ('construction', 'En construction')
    ], default='en_service')
    gestionnaire = StringField('Gestionnaire', validators=[Optional(), Length(max=200)])
    
    # Observations
    description = TextAreaField('Description', validators=[Optional()], widget=TextArea())
    observations = TextAreaField('Observations', validators=[Optional()], widget=TextArea())
    
    def __init__(self, *args, **kwargs):
        super(ReseauDistributionForm, self).__init__(*args, **kwargs)
        # Configurer les choix d'opérateurs selon les permissions
        self.operateur_id.choices = get_operateur_choices()
        # Définir la valeur par défaut si non admin
        if not kwargs.get('obj') and get_default_operateur_id():
            self.operateur_id.data = get_default_operateur_id()
    
    def validate_code(self, field):
        """Validation personnalisée pour vérifier l'unicité du code"""
        from app.models.distribution import ReseauDistribution
        
        # Vérifier s'il s'agit d'une modification d'un réseau existant
        existing_reseau = None
        if hasattr(self, '_obj') and self._obj:
            existing_reseau = self._obj
        
        # Rechercher un réseau avec le même code
        reseau_existant = ReseauDistribution.query.filter_by(code=field.data, actif=True).first()
        
        if reseau_existant and (not existing_reseau or reseau_existant.id != existing_reseau.id):
            raise ValidationError('Ce code est déjà utilisé par un autre réseau. Veuillez choisir un code unique.')


class PosteDistributionForm(FlaskForm):
    """Formulaire pour les postes de distribution"""
    
    # Réseau parent (requis)
    reseau_id = SelectField('Réseau de distribution', coerce=safe_int_coerce, validators=[DataRequired()])
    
    # Informations de base
    nom = StringField('Nom du poste', validators=[DataRequired(), Length(max=200)])
    code = StringField('Code', validators=[DataRequired(), Length(max=50)])
    type_poste = SelectField('Type de poste', choices=[
        ('source', 'Poste source'),
        ('distribution', 'Poste de distribution'),
        ('client', 'Poste client')
    ], validators=[Optional()])
    
    # Localisation
    localisation = StringField('Localisation', validators=[Optional(), Length(max=200)])
    quartier = StringField('Quartier', validators=[Optional(), Length(max=100)])
    latitude = FloatField('Latitude', validators=[Optional(), NumberRange(min=-90, max=90)])
    longitude = FloatField('Longitude', validators=[Optional(), NumberRange(min=-180, max=180)])
    
    # Caractéristiques électriques
    tension_primaire = FloatField('Tension primaire (kV)', validators=[Optional(), NumberRange(min=0)])
    tension_secondaire = FloatField('Tension secondaire (kV)', validators=[Optional(), NumberRange(min=0)])
    puissance_installee = FloatField('Puissance installée (kVA)', validators=[Optional(), NumberRange(min=0)])
    puissance_souscrite = FloatField('Puissance souscrite (kVA)', validators=[Optional(), NumberRange(min=0)])
    
    # Configuration
    nombre_transformateurs = IntegerField('Nombre de transformateurs', validators=[Optional(), NumberRange(min=0)], default=1)
    nombre_departs = IntegerField('Nombre de départs', validators=[Optional(), NumberRange(min=0)], default=0)
    schema_exploitation = SelectField('Schéma d\'exploitation', choices=[
        ('normal_ouvert', 'Normal ouvert'),
        ('normal_ferme', 'Normal fermé')
    ], validators=[Optional()])
    
    # Protection
    protection_primaire = SelectField('Protection primaire', choices=[
        ('disjoncteur', 'Disjoncteur'),
        ('fusible', 'Fusible'),
        ('sectionneur', 'Sectionneur')
    ], validators=[Optional()])
    protection_secondaire = SelectField('Protection secondaire', choices=[
        ('disjoncteur', 'Disjoncteur'),
        ('fusible', 'Fusible'),
        ('differentiel', 'Différentiel')
    ], validators=[Optional()])
    mise_terre = SelectField('Régime de mise à la terre', choices=[
        ('TT', 'TT'),
        ('TN', 'TN'),
        ('IT', 'IT')
    ], validators=[Optional()])
    
    # Clientèle desservie
    nombre_clients_raccordes = IntegerField('Clients raccordés', validators=[Optional(), NumberRange(min=0)], default=0)
    
    # Performance
    taux_charge = FloatField('Taux de charge (%)', validators=[Optional(), NumberRange(min=0, max=100)], default=0.0)
    facteur_puissance = FloatField('Facteur de puissance', validators=[Optional(), NumberRange(min=0, max=1)], default=0.9)
    pertes_transformateur = FloatField('Pertes transformateur (%)', validators=[Optional(), NumberRange(min=0, max=100)], default=0.0)
    
    # État et maintenance
    statut = SelectField('Statut', choices=[
        ('en_service', 'En service'),
        ('hors_service', 'Hors service'),
        ('maintenance', 'En maintenance')
    ], default='en_service')
    date_mise_service = DateField('Date de mise en service', validators=[Optional()])
    date_derniere_maintenance = DateField('Dernière maintenance', validators=[Optional()])
    
    # Observations
    observations = TextAreaField('Observations', validators=[Optional()], widget=TextArea())
    
    def __init__(self, *args, **kwargs):
        super(PosteDistributionForm, self).__init__(*args, **kwargs)
        # Configurer les choix de réseaux selon les permissions
        from app.models.distribution import ReseauDistribution
        from flask_login import current_user
        
        if current_user.is_admin():
            reseaux = ReseauDistribution.query.filter_by(actif=True).all()
        elif current_user.operateur_id:
            reseaux = ReseauDistribution.query.filter_by(
                operateur_id=current_user.operateur_id, 
                actif=True
            ).all()
        else:
            reseaux = []
        
        self.reseau_id.choices = [('', 'Sélectionner un réseau')] + [
            (r.id, f"{r.nom} ({r.operateur.nom})") for r in reseaux
        ]
    
    def validate_code(self, field):
        """Validation personnalisée pour vérifier l'unicité du code du poste"""
        from app.models.distribution import PosteDistribution
        
        # Vérifier s'il s'agit d'une modification d'un poste existant
        existing_poste = None
        if hasattr(self, '_obj') and self._obj:
            existing_poste = self._obj
        
        # Rechercher un poste avec le même code
        poste_existant = PosteDistribution.query.filter_by(code=field.data, actif=True).first()
        
        if poste_existant and (not existing_poste or poste_existant.id != existing_poste.id):
            raise ValidationError('Ce code est déjà utilisé par un autre poste. Veuillez choisir un code unique.')


class TransformateurDistributionForm(FlaskForm):
    """Formulaire pour les transformateurs de distribution"""
    
    # Relations
    poste_distribution_id = SelectField('Poste de distribution', coerce=safe_int_coerce, validators=[DataRequired()])
    
    # Identification
    nom = StringField('Nom du transformateur', validators=[DataRequired(), Length(max=200)])
    type_transformateur = SelectField('Type de transformateur', choices=[
        ('monophase', 'Monophasé'),
        ('triphase', 'Triphasé'),
        ('distribution', 'Distribution'),
        ('puissance', 'Puissance')
    ], validators=[Optional()])
    numero_serie = StringField('Numéro de série', validators=[Optional(), Length(max=100)])
    constructeur = StringField('Constructeur', validators=[Optional(), Length(max=100)])
    modele = StringField('Modèle', validators=[Optional(), Length(max=100)])
    annee_fabrication = IntegerField('Année de fabrication', validators=[Optional(), NumberRange(min=1900, max=2030)])
    date_installation = DateField('Date d\'installation', validators=[Optional()])
    
    # Caractéristiques électriques
    puissance_nominale = FloatField('Puissance nominale (kVA)', validators=[DataRequired(), NumberRange(min=0)])
    tension_primaire = FloatField('Tension primaire (kV)', validators=[DataRequired(), NumberRange(min=0)])
    tension_secondaire = FloatField('Tension secondaire (V)', validators=[DataRequired(), NumberRange(min=0)])
    couplage = StringField('Couplage', validators=[Optional(), Length(max=20)])
    
    # Caractéristiques techniques
    type_refroidissement = SelectField('Type de refroidissement', choices=[
        ('ONAN', 'ONAN - Huile naturelle, air naturel'),
        ('AN', 'AN - Air naturel'),
        ('AF', 'AF - Air forcé')
    ], validators=[Optional()])
    type_installation = SelectField('Type d\'installation', choices=[
        ('poteau', 'Sur poteau'),
        ('cabine', 'En cabine'),
        ('sol', 'Au sol')
    ], validators=[Optional()])
    indice_protection = StringField('Indice de protection (IP)', validators=[Optional(), Length(max=10)])
    classe_isolation = SelectField('Classe d\'isolation', choices=[
        ('A', 'Classe A'),
        ('B', 'Classe B'),
        ('F', 'Classe F'),
        ('H', 'Classe H')
    ], validators=[Optional()])
    
    # Impédances et pertes
    impedance_cc = FloatField('Impédance court-circuit (%)', validators=[Optional(), NumberRange(min=0)])
    pertes_vide = FloatField('Pertes à vide (W)', validators=[Optional(), NumberRange(min=0)])
    pertes_charge = FloatField('Pertes en charge (W)', validators=[Optional(), NumberRange(min=0)])
    courant_vide = FloatField('Courant à vide (%)', validators=[Optional(), NumberRange(min=0)])
    
    # Réglage
    prises_reglage = IntegerField('Prises de réglage', validators=[Optional(), NumberRange(min=0)], default=0)
    plage_reglage = FloatField('Plage de réglage (%)', validators=[Optional(), NumberRange(min=0)], default=0.0)
    position_prise = IntegerField('Position prise actuelle', validators=[Optional(), NumberRange(min=0)], default=0)
    
    # Charge et utilisation
    charge_actuelle = FloatField('Charge actuelle (%)', validators=[Optional(), NumberRange(min=0, max=100)], default=0.0)
    charge_maximale = FloatField('Charge maximale (%)', validators=[Optional(), NumberRange(min=0, max=100)], default=0.0)
    heures_fonctionnement = FloatField('Heures de fonctionnement', validators=[Optional(), NumberRange(min=0)], default=0.0)
    
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
    niveau_huile = SelectField('Niveau d\'huile', choices=[
        ('normal', 'Normal'),
        ('bas', 'Bas'),
        ('critique', 'Critique')
    ], validators=[Optional()])
    
    # Position géographique
    latitude = FloatField('Latitude', validators=[Optional(), NumberRange(min=-90, max=90)])
    longitude = FloatField('Longitude', validators=[Optional(), NumberRange(min=-180, max=180)])
    
    # Observations
    observations = TextAreaField('Observations', validators=[Optional()], widget=TextArea())
    
    def __init__(self, *args, **kwargs):
        super(TransformateurDistributionForm, self).__init__(*args, **kwargs)
        # Configurer les choix de postes selon les permissions
        from app.models.distribution import PosteDistribution, ReseauDistribution
        from flask_login import current_user
        
        if current_user.is_admin():
            postes = PosteDistribution.query.filter_by(actif=True).all()
        elif current_user.operateur_id:
            postes = PosteDistribution.query.join(ReseauDistribution).filter(
                ReseauDistribution.operateur_id == current_user.operateur_id,
                PosteDistribution.actif == True
            ).all()
        else:
            postes = []
        
        self.poste_distribution_id.choices = [('', 'Sélectionner un poste')] + [
            (p.id, f"{p.nom} ({p.reseau.nom})") for p in postes
        ]


class FeederDistributionForm(FlaskForm):
    """Formulaire pour les feeders de distribution"""
    
    # Relations
    reseau_id = SelectField('Réseau de distribution', coerce=safe_int_coerce, validators=[DataRequired()])
    poste_source_id = SelectField('Poste source', coerce=safe_int_coerce, validators=[Optional()])
    
    # Informations de base
    nom = StringField('Nom du feeder', validators=[DataRequired(), Length(max=200)])
    code = StringField('Code', validators=[DataRequired(), Length(max=50)])
    type_feeder = SelectField('Type de feeder', choices=[
        ('urbain', 'Urbain'),
        ('rural', 'Rural'),
        ('industriel', 'Industriel')
    ], validators=[Optional()])
    
    # Caractéristiques électriques
    tension_nominale = FloatField('Tension nominale (kV)', validators=[DataRequired(), NumberRange(min=0)])
    longueur_totale = FloatField('Longueur totale (km)', validators=[Optional(), NumberRange(min=0)])
    section_conducteur = FloatField('Section conducteur (mm²)', validators=[Optional(), NumberRange(min=0)])
    type_conducteur = SelectField('Type de conducteur', choices=[
        ('Al', 'Aluminium'),
        ('Cu', 'Cuivre'),
        ('ACSR', 'ACSR'),
        ('AAAC', 'AAAC')
    ], validators=[Optional()])
    
    # Topologie
    type_reseau = SelectField('Type de réseau', choices=[
        ('radial', 'Radial'),
        ('boucle', 'Bouclé')
    ], validators=[Optional()])
    nombre_branches = IntegerField('Nombre de branches', validators=[Optional(), NumberRange(min=1)], default=1)
    
    # Protection
    protection_tete = SelectField('Protection en tête', choices=[
        ('disjoncteur', 'Disjoncteur'),
        ('reenclencheur', 'Réenclencheur'),
        ('fusible', 'Fusible')
    ], validators=[Optional()])
    automatisation = BooleanField('Automatisation')
    
    # Clientèle
    nombre_clients = IntegerField('Nombre de clients', validators=[Optional(), NumberRange(min=0)], default=0)
    puissance_souscrite = FloatField('Puissance souscrite (kVA)', validators=[Optional(), NumberRange(min=0)], default=0.0)
    charge_maximale = FloatField('Charge maximale (kW)', validators=[Optional(), NumberRange(min=0)], default=0.0)
    
    # Performance
    taux_charge = FloatField('Taux de charge (%)', validators=[Optional(), NumberRange(min=0, max=100)], default=0.0)
    pertes_techniques = FloatField('Pertes techniques (%)', validators=[Optional(), NumberRange(min=0, max=100)], default=0.0)
    facteur_puissance = FloatField('Facteur de puissance', validators=[Optional(), NumberRange(min=0, max=1)], default=0.9)
    
    # Fiabilité
    saidi_annuel = FloatField('SAIDI annuel (minutes)', validators=[Optional(), NumberRange(min=0)], default=0.0)
    saifi_annuel = FloatField('SAIFI annuel (coupures)', validators=[Optional(), NumberRange(min=0)], default=0.0)
    nombre_defauts_annuels = IntegerField('Défauts annuels', validators=[Optional(), NumberRange(min=0)], default=0)
    
    # État
    statut = SelectField('Statut', choices=[
        ('en_service', 'En service'),
        ('hors_service', 'Hors service'),
        ('maintenance', 'En maintenance')
    ], default='en_service')
    date_mise_service = DateField('Date de mise en service', validators=[Optional()])
    
    # Observations
    observations = TextAreaField('Observations', validators=[Optional()], widget=TextArea())
    
    def __init__(self, *args, **kwargs):
        super(FeederDistributionForm, self).__init__(*args, **kwargs)
        # Configurer les choix selon les permissions
        from app.models.distribution import ReseauDistribution, PosteDistribution
        from flask_login import current_user
        
        if current_user.is_admin():
            reseaux = ReseauDistribution.query.filter_by(actif=True).all()
        elif current_user.operateur_id:
            reseaux = ReseauDistribution.query.filter_by(
                operateur_id=current_user.operateur_id, 
                actif=True
            ).all()
        else:
            reseaux = []
        
        self.reseau_id.choices = [('', 'Sélectionner un réseau')] + [
            (r.id, f"{r.nom} ({r.operateur.nom})") for r in reseaux
        ]
        
        # Les postes seront mis à jour via JavaScript selon le réseau sélectionné
        self.poste_source_id.choices = [('', 'Sélectionner un poste source')]
    
    def validate_code(self, field):
        """Validation personnalisée pour vérifier l'unicité du code du feeder"""
        from app.models.distribution import FeederDistribution
        
        # Vérifier s'il s'agit d'une modification d'un feeder existant
        existing_feeder = None
        if hasattr(self, '_obj') and self._obj:
            existing_feeder = self._obj
        
        # Rechercher un feeder avec le même code
        feeder_existant = FeederDistribution.query.filter_by(code=field.data, actif=True).first()
        
        if feeder_existant and (not existing_feeder or feeder_existant.id != existing_feeder.id):
            raise ValidationError('Ce code est déjà utilisé par un autre feeder. Veuillez choisir un code unique.')


class RapportDistributionForm(FlaskForm):
    """Formulaire pour les rapports de distribution"""
    
    # Sélection réseau
    reseau_id = SelectField('Réseau de distribution', coerce=safe_int_coerce, validators=[DataRequired()])
    
    # Période
    annee = IntegerField('Année', validators=[DataRequired(), NumberRange(min=2000, max=2050)])
    mois = SelectField('Mois', choices=[
        (1, 'Janvier'), (2, 'Février'), (3, 'Mars'), (4, 'Avril'),
        (5, 'Mai'), (6, 'Juin'), (7, 'Juillet'), (8, 'Août'),
        (9, 'Septembre'), (10, 'Octobre'), (11, 'Novembre'), (12, 'Décembre')
    ], coerce=safe_int_coerce, validators=[DataRequired()])
    periode_debut = DateField('Début de période', validators=[DataRequired()])
    periode_fin = DateField('Fin de période', validators=[DataRequired()])
    
    # Énergie et approvisionnement
    energie_achetee = FloatField('Énergie achetée (MWh)', validators=[Optional(), NumberRange(min=0)])
    energie_distribuee = FloatField('Énergie distribuée (MWh)', validators=[Optional(), NumberRange(min=0)])
    energie_vendue = FloatField('Énergie vendue (MWh)', validators=[Optional(), NumberRange(min=0)])
    pointe_distribution = FloatField('Pointe de distribution (MW)', validators=[Optional(), NumberRange(min=0)])
    heure_pointe = StringField('Heure de pointe (HH:MM)', validators=[Optional(), Length(max=10)])
    
    # Clientèle
    nombre_clients_debut = IntegerField('Clients début période', validators=[Optional(), NumberRange(min=0)], default=0)
    nouveaux_raccordements = IntegerField('Nouveaux raccordements', validators=[Optional(), NumberRange(min=0)], default=0)
    resiliations = IntegerField('Résiliations', validators=[Optional(), NumberRange(min=0)], default=0)
    nombre_clients_fin = IntegerField('Clients fin période', validators=[Optional(), NumberRange(min=0)], default=0)
    
    # Répartition clientèle
    clients_domestiques = IntegerField('Clients domestiques', validators=[Optional(), NumberRange(min=0)], default=0)
    clients_commerciaux = IntegerField('Clients commerciaux', validators=[Optional(), NumberRange(min=0)], default=0)
    clients_industriels = IntegerField('Clients industriels', validators=[Optional(), NumberRange(min=0)], default=0)
    clients_autres = IntegerField('Autres clients', validators=[Optional(), NumberRange(min=0)], default=0)
    
    # Consommation par catégorie
    energie_domestique = FloatField('Énergie domestique (MWh)', validators=[Optional(), NumberRange(min=0)], default=0.0)
    energie_commerciale = FloatField('Énergie commerciale (MWh)', validators=[Optional(), NumberRange(min=0)], default=0.0)
    energie_industrielle = FloatField('Énergie industrielle (MWh)', validators=[Optional(), NumberRange(min=0)], default=0.0)
    energie_autres = FloatField('Énergie autres (MWh)', validators=[Optional(), NumberRange(min=0)], default=0.0)
    
    # Qualité de fourniture
    nombre_coupures = IntegerField('Nombre de coupures', validators=[Optional(), NumberRange(min=0)], default=0)
    duree_total_coupures = FloatField('Durée totale coupures (min)', validators=[Optional(), NumberRange(min=0)], default=0.0)
    saidi_realise = FloatField('SAIDI réalisé (min)', validators=[Optional(), NumberRange(min=0)], default=0.0)
    saifi_realise = FloatField('SAIFI réalisé (coupures/client)', validators=[Optional(), NumberRange(min=0)], default=0.0)
    energie_non_distribuee = FloatField('Énergie non distribuée (MWh)', validators=[Optional(), NumberRange(min=0)], default=0.0)
    
    # Causes des coupures
    coupures_programmees = IntegerField('Coupures programmées', validators=[Optional(), NumberRange(min=0)], default=0)
    coupures_incidents = IntegerField('Coupures incidents', validators=[Optional(), NumberRange(min=0)], default=0)
    coupures_climatiques = IntegerField('Coupures climatiques', validators=[Optional(), NumberRange(min=0)], default=0)
    coupures_tiers = IntegerField('Coupures tiers', validators=[Optional(), NumberRange(min=0)], default=0)
    
    # Pertes
    pertes_techniques = FloatField('Pertes techniques (%)', validators=[Optional(), NumberRange(min=0, max=100)], default=0.0)
    pertes_non_techniques = FloatField('Pertes non techniques (%)', validators=[Optional(), NumberRange(min=0, max=100)], default=0.0)
    pertes_totales = FloatField('Pertes totales (%)', validators=[Optional(), NumberRange(min=0, max=100)], default=0.0)
    energie_pertes = FloatField('Énergie de pertes (MWh)', validators=[Optional(), NumberRange(min=0)], default=0.0)
    
    # Maintenance
    maintenances_preventives = IntegerField('Maintenances préventives', validators=[Optional(), NumberRange(min=0)], default=0)
    maintenances_correctives = IntegerField('Maintenances correctives', validators=[Optional(), NumberRange(min=0)], default=0)
    travaux_extension = IntegerField('Travaux d\'extension', validators=[Optional(), NumberRange(min=0)], default=0)
    investissements = FloatField('Investissements (USD)', validators=[Optional(), NumberRange(min=0)], default=0.0)
    
    # Performance technique
    taux_disponibilite = FloatField('Taux de disponibilité (%)', validators=[Optional(), NumberRange(min=0, max=100)], default=0.0)
    facteur_charge = FloatField('Facteur de charge (%)', validators=[Optional(), NumberRange(min=0, max=100)], default=0.0)
    facteur_puissance_moyen = FloatField('Facteur puissance moyen', validators=[Optional(), NumberRange(min=0, max=1)], default=0.0)
    
    # Qualité tension
    variations_tension = IntegerField('Variations de tension', validators=[Optional(), NumberRange(min=0)], default=0)
    harmoniques_depassement = IntegerField('Dépassements harmoniques', validators=[Optional(), NumberRange(min=0)], default=0)
    desequilibres_tension = IntegerField('Déséquilibres tension', validators=[Optional(), NumberRange(min=0)], default=0)
    
    # Réclamations et satisfaction
    nombre_reclamations = IntegerField('Nombre réclamations', validators=[Optional(), NumberRange(min=0)], default=0)
    reclamations_qualite = IntegerField('Réclamations qualité', validators=[Optional(), NumberRange(min=0)], default=0)
    reclamations_facturation = IntegerField('Réclamations facturation', validators=[Optional(), NumberRange(min=0)], default=0)
    taux_satisfaction = FloatField('Taux de satisfaction (%)', validators=[Optional(), NumberRange(min=0, max=100)], default=0.0)
    
    # Aspects environnementaux
    emissions_evitees = FloatField('Émissions évitées (tonnes CO2)', validators=[Optional(), NumberRange(min=0)], default=0.0)
    consommation_auxiliaires = FloatField('Consommation auxiliaires (MWh)', validators=[Optional(), NumberRange(min=0)], default=0.0)
    
    # Observations
    observations = TextAreaField('Observations', validators=[Optional()], widget=TextArea())
    
    def __init__(self, *args, **kwargs):
        super(RapportDistributionForm, self).__init__(*args, **kwargs)
        # Configurer les choix de réseaux selon les permissions
        from app.models.distribution import ReseauDistribution
        from flask_login import current_user
        
        if current_user.is_admin():
            reseaux = ReseauDistribution.query.filter_by(actif=True).all()
        elif current_user.operateur_id:
            reseaux = ReseauDistribution.query.filter_by(
                operateur_id=current_user.operateur_id, 
                actif=True
            ).all()
        else:
            reseaux = []
        
        self.reseau_id.choices = [('', 'Sélectionner un réseau')] + [
            (r.id, f"{r.nom} ({r.operateur.nom})") for r in reseaux
        ]


class FiltreDistributionForm(FlaskForm):
    """Formulaire de filtrage pour les infrastructures de distribution"""
    
    # Filtres par type d'infrastructure
    type_infrastructure = SelectField('Type d\'infrastructure', choices=[
        ('', 'Tous les types'),
        ('reseau', 'Réseaux de distribution'),
        ('feeder', 'Feeders'),
        ('poste', 'Postes de distribution')
    ], validators=[Optional()])
    
    # Filtres par type de réseau
    type_reseau = SelectField('Type de réseau', choices=[
        ('', 'Tous les types'),
        ('urbain', 'Urbain'),
        ('rural', 'Rural'),
        ('industriel', 'Industriel')
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
    
    # Filtres par nombre de clients
    clients_min = IntegerField('Clients minimum', validators=[Optional(), NumberRange(min=0)])
    clients_max = IntegerField('Clients maximum', validators=[Optional(), NumberRange(min=0)])
    
    # Filtres par longueur
    longueur_min = FloatField('Longueur minimum (km)', validators=[Optional(), NumberRange(min=0)])
    longueur_max = FloatField('Longueur maximum (km)', validators=[Optional(), NumberRange(min=0)])
    
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