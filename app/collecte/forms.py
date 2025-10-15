"""
Formulaires pour la collecte mensuelle des données des opérateurs
Remplace les données fictives par des soumissions réelles
"""
from flask_wtf import FlaskForm
from wtforms import (
    StringField, IntegerField, FloatField, SelectField, TextAreaField, 
    SubmitField, DateField, DecimalField, BooleanField
)
from wtforms.validators import (
    DataRequired, Optional, NumberRange, Length, ValidationError
)
from datetime import datetime, date
from app.models.collecte_donnees import CollecteDonneesMensuelles, CollecteProjetNouveau
from app.models.operateurs import Operateur
from flask_login import current_user


class CollecteDonneesMensuellesForm(FlaskForm):
    """
    Formulaire de collecte mensuelle des données non-calculables
    Évite les fake data en récoltant les vraies informations
    """
    
    # Période de reporting
    annee = SelectField(
        'Année *',
        choices=[],  # Sera rempli dynamiquement
        validators=[DataRequired(message="L'année est requise")]
    )
    
    mois = SelectField(
        'Mois *',
        choices=[
            ('1', 'Janvier'), ('2', 'Février'), ('3', 'Mars'),
            ('4', 'Avril'), ('5', 'Mai'), ('6', 'Juin'),
            ('7', 'Juillet'), ('8', 'Août'), ('9', 'Septembre'),
            ('10', 'Octobre'), ('11', 'Novembre'), ('12', 'Décembre')
        ],
        validators=[DataRequired(message="Le mois est requis")]
    )
    
    # === DONNÉES FINANCIÈRES (non-calculables) ===
    chiffre_affaires_mois = DecimalField(
        'Chiffre d\'affaires du mois (USD)',
        validators=[
            Optional(),
            NumberRange(min=0, message="Le chiffre d'affaires ne peut pas être négatif")
        ],
        description="Revenus totaux générés pendant ce mois"
    )
    
    investissements_realises_mois = DecimalField(
        'Investissements réalisés (USD)',
        validators=[
            Optional(),
            NumberRange(min=0, message="Les investissements ne peuvent pas être négatifs")
        ],
        description="Montant investi en infrastructure ce mois"
    )
    
    cout_combustible_mois = DecimalField(
        'Coût combustible/carburant (USD)',
        validators=[
            Optional(),
            NumberRange(min=0, message="Le coût ne peut pas être négatif")
        ],
        description="Coût total du combustible pour les centrales thermiques"
    )
    
    tarifs_moyens_ht = DecimalField(
        'Tarif moyen HT (USD/kWh)',
        validators=[
            Optional(),
            NumberRange(min=0, message="Le tarif ne peut pas être négatif")
        ],
        description="Tarif moyen appliqué aux clients Haute Tension"
    )
    
    tarifs_moyens_mt = DecimalField(
        'Tarif moyen MT (USD/kWh)',
        validators=[
            Optional(),
            NumberRange(min=0, message="Le tarif ne peut pas être négatif")
        ],
        description="Tarif moyen appliqué aux clients Moyenne Tension"
    )
    
    tarifs_moyens_bt = DecimalField(
        'Tarif moyen BT (USD/kWh)',
        validators=[
            Optional(),
            NumberRange(min=0, message="Le tarif ne peut pas être négatif")
        ],
        description="Tarif moyen appliqué aux clients Basse Tension"
    )
    
    # === ÉVOLUTION DE LA CLIENTÈLE ===
    nouveaux_clients_ht_mois = IntegerField(
        'Nouveaux clients HT ce mois',
        validators=[
            Optional(),
            NumberRange(min=0, message="Le nombre ne peut pas être négatif")
        ],
        description="Nombre de nouveaux raccordements HT"
    )
    
    nouveaux_clients_mt_mois = IntegerField(
        'Nouveaux clients MT ce mois',
        validators=[
            Optional(),
            NumberRange(min=0, message="Le nombre ne peut pas être négatif")
        ]
    )
    
    nouveaux_clients_bt_mois = IntegerField(
        'Nouveaux clients BT ce mois',
        validators=[
            Optional(),
            NumberRange(min=0, message="Le nombre ne peut pas être négatif")
        ]
    )
    
    clients_deconnectes_ht_mois = IntegerField(
        'Clients HT déconnectés',
        validators=[
            Optional(),
            NumberRange(min=0, message="Le nombre ne peut pas être négatif")
        ],
        description="Déconnexions pour impayés ou autres raisons"
    )
    
    clients_deconnectes_mt_mois = IntegerField(
        'Clients MT déconnectés',
        validators=[
            Optional(),
            NumberRange(min=0, message="Le nombre ne peut pas être négatif")
        ]
    )
    
    clients_deconnectes_bt_mois = IntegerField(
        'Clients BT déconnectés',
        validators=[
            Optional(),
            NumberRange(min=0, message="Le nombre ne peut pas être négatif")
        ]
    )
    
    # === EXPANSION GÉOGRAPHIQUE ===
    nouvelles_localites_desservies = IntegerField(
        'Nouvelles localités desservies',
        validators=[
            Optional(),
            NumberRange(min=0, message="Le nombre ne peut pas être négatif")
        ],
        description="Nombre de nouvelles communautés électrifiées"
    )
    
    longueur_nouveaux_reseaux_km = FloatField(
        'Nouveaux réseaux construits (km)',
        validators=[
            Optional(),
            NumberRange(min=0, message="La longueur ne peut pas être négative")
        ],
        description="Kilomètres de lignes/câbles installés"
    )
    
    population_nouvelle_couverte = IntegerField(
        'Population nouvelle couverte',
        validators=[
            Optional(),
            NumberRange(min=0, message="La population ne peut pas être négative")
        ],
        description="Nombre d'habitants ayant accès à l'électricité"
    )
    
    # === QUALITÉ DE SERVICE ===
    duree_moyenne_coupures_heures = FloatField(
        'Durée moyenne des coupures (heures)',
        validators=[
            Optional(),
            NumberRange(min=0, message="La durée ne peut pas être négative")
        ],
        description="Temps moyen de coupure par incident"
    )
    
    nombre_incidents_techniques = IntegerField(
        'Nombre d\'incidents techniques',
        validators=[
            Optional(),
            NumberRange(min=0, message="Le nombre ne peut pas être négatif")
        ],
        description="Pannes, défaillances d'équipement, etc."
    )
    
    taux_disponibilite_reseau = FloatField(
        'Taux de disponibilité réseau (%)',
        validators=[
            Optional(),
            NumberRange(min=0, max=100, message="Le taux doit être entre 0 et 100%")
        ],
        description="Pourcentage de temps où le réseau est opérationnel"
    )
    
    # === IMPACT ENVIRONNEMENTAL ===
    emissions_co2_tonnes = FloatField(
        'Émissions CO2 estimées (tonnes)',
        validators=[
            Optional(),
            NumberRange(min=0, message="Les émissions ne peuvent pas être négatives")
        ],
        description="Émissions liées à la production thermique"
    )
    
    consommation_eau_m3 = FloatField(
        'Consommation d\'eau (m³)',
        validators=[
            Optional(),
            NumberRange(min=0, message="La consommation ne peut pas être négative")
        ],
        description="Eau utilisée pour le refroidissement, etc."
    )
    
    # === OBSERVATIONS ET COMMENTAIRES ===
    observations_mois = TextAreaField(
        'Observations du mois',
        validators=[
            Optional(),
            Length(max=1000, message="Maximum 1000 caractères")
        ],
        description="Événements marquants, défis rencontrés, projets en cours"
    )
    
    difficultees_rencontrees = TextAreaField(
        'Difficultés rencontrées',
        validators=[
            Optional(),
            Length(max=500, message="Maximum 500 caractères")
        ],
        description="Problèmes techniques, financiers, réglementaires"
    )
    
    # Actions
    submit = SubmitField('Soumettre les données mensuelles')
    save_draft = SubmitField('Enregistrer en brouillon')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Remplir les années disponibles (5 dernières + année courante + 2 prochaines)
        current_year = datetime.now().year
        years = [(str(y), str(y)) for y in range(current_year - 5, current_year + 3)]
        self.annee.choices = years
        
        # Valeur par défaut : année courante
        if not self.annee.data:
            self.annee.data = str(current_year)
    
    def validate(self, extra_validators=None):
        """Validation personnalisée du formulaire"""
        if not super().validate(extra_validators):
            return False
        
        # Vérifier si une collecte existe déjà pour cette période
        if current_user and hasattr(current_user, 'operateur_id') and current_user.operateur_id:
            existing = CollecteDonneesMensuelles.query.filter(
                CollecteDonneesMensuelles.operateur_id == current_user.operateur_id,
                CollecteDonneesMensuelles.annee == int(self.annee.data),
                CollecteDonneesMensuelles.mois == int(self.mois.data),
                CollecteDonneesMensuelles.actif == True
            ).first()
            
            if existing and existing.statut != 'brouillon':
                self.mois.errors.append(
                    f"Une collecte existe déjà pour {self.mois.data}/{self.annee.data} "
                    f"avec le statut: {existing.statut}"
                )
                return False
        
        # Vérifier que la période n'est pas dans le futur lointain
        try:
            periode = date(int(self.annee.data), int(self.mois.data), 1)
            if periode > date.today().replace(day=1):  # Début du mois suivant
                self.mois.errors.append(
                    "Vous ne pouvez pas soumettre de données pour une période future"
                )
                return False
        except ValueError:
            self.annee.errors.append("Année ou mois invalide")
            return False
        
        return True


class CollecteProjetNouveauForm(FlaskForm):
    """
    Formulaire pour la soumission de nouveaux projets à l'ARE
    """
    
    # Informations générales
    nom_projet = StringField(
        'Nom du projet *',
        validators=[
            DataRequired(message="Le nom du projet est requis"),
            Length(min=5, max=200, message="Le nom doit faire entre 5 et 200 caractères")
        ],
        description="Nom complet et descriptif du projet"
    )
    
    type_projet = SelectField(
        'Type de projet *',
        choices=[
            ('production_hydro', 'Centrale Hydroélectrique'),
            ('production_thermique', 'Centrale Thermique'),
            ('production_solaire', 'Centrale Solaire/Photovoltaïque'),
            ('transport', 'Ligne de Transport'),
            ('distribution', 'Réseau de Distribution'),
            ('poste_transformation', 'Poste de Transformation'),
            ('autre', 'Autre (préciser)')
        ],
        validators=[DataRequired(message="Le type de projet est requis")]
    )
    
    description_projet = TextAreaField(
        'Description détaillée *',
        validators=[
            DataRequired(message="La description est requise"),
            Length(min=50, max=2000, message="La description doit faire entre 50 et 2000 caractères")
        ],
        description="Objectifs, technologies utilisées, bénéficiaires"
    )
    
    # Caractéristiques techniques
    capacite_prevue_mw = FloatField(
        'Capacité prévue (MW)',
        validators=[
            Optional(),
            NumberRange(min=0.001, message="La capacité doit être positive")
        ],
        description="Puissance installée prévue"
    )
    
    longueur_prevue_km = FloatField(
        'Longueur prévue (km)',
        validators=[
            Optional(),
            NumberRange(min=0.001, message="La longueur doit être positive")
        ],
        description="Pour les projets de transport/distribution"
    )
    
    tension_nominale_kv = FloatField(
        'Tension nominale (kV)',
        validators=[
            Optional(),
            NumberRange(min=0.1, message="La tension doit être positive")
        ]
    )
    
    # Localisation
    province = SelectField(
        'Province *',
        choices=[
            ('kinshasa', 'Kinshasa'),
            ('bas_congo', 'Kongo Central'),
            ('bandundu', 'Kwilu, Kwango, Mai-Ndombe'),
            ('equateur', 'Équateur, Mongala, Nord-Ubangi, Sud-Ubangi, Tshuapa'),
            ('orientale', 'Bas-Uele, Haut-Uele, Ituri, Tshopo'),
            ('nord_kivu', 'Nord-Kivu'),
            ('sud_kivu', 'Sud-Kivu'),
            ('maniema', 'Maniema'),
            ('katanga', 'Haut-Katanga, Lualaba, Tanganyka, Haut-Lomami'),
            ('kasai_oriental', 'Kasaï, Kasaï Oriental, Kasaï Central, Lomami, Sankuru')
        ],
        validators=[DataRequired(message="La province est requise")]
    )
    
    localisation_precise = StringField(
        'Localisation précise *',
        validators=[
            DataRequired(message="La localisation est requise"),
            Length(max=200, message="Maximum 200 caractères")
        ],
        description="Territoire, ville, coordonnées si disponibles"
    )
    
    # Aspects économiques
    cout_estime_usd = DecimalField(
        'Coût estimé (USD)',
        validators=[
            Optional(),
            NumberRange(min=1, message="Le coût doit être positif")
        ],
        description="Investissement total prévu"
    )
    
    financement_acquis = BooleanField(
        'Financement acquis',
        description="Cochez si le financement est déjà sécurisé"
    )
    
    source_financement = StringField(
        'Source de financement',
        validators=[
            Optional(),
            Length(max=200, message="Maximum 200 caractères")
        ],
        description="Banque, partenaires, fonds propres, etc."
    )
    
    # Planning
    date_debut_prevue = DateField(
        'Date de début prévue',
        validators=[Optional()],
        description="Date prévue de démarrage des travaux"
    )
    
    duree_travaux_mois = IntegerField(
        'Durée des travaux (mois)',
        validators=[
            Optional(),
            NumberRange(min=1, max=120, message="Durée entre 1 et 120 mois")
        ]
    )
    
    date_mise_service_prevue = DateField(
        'Date de mise en service prévue',
        validators=[Optional()],
        description="Date prévue de mise en service commercial"
    )
    
    # Impact attendu
    population_beneficiaire = IntegerField(
        'Population bénéficiaire estimée',
        validators=[
            Optional(),
            NumberRange(min=1, message="La population doit être positive")
        ],
        description="Nombre d'habitants qui bénéficieront du projet"
    )
    
    emplois_crees = IntegerField(
        'Emplois créés (estimation)',
        validators=[
            Optional(),
            NumberRange(min=0, message="Le nombre d'emplois ne peut pas être négatif")
        ],
        description="Emplois directs et indirects créés"
    )
    
    # Documents et études
    etude_impact_realisee = BooleanField(
        'Étude d\'impact environnemental réalisée'
    )
    
    autorisation_environnementale = BooleanField(
        'Autorisation environnementale obtenue'
    )
    
    etude_faisabilite_realisee = BooleanField(
        'Étude de faisabilité technique et économique réalisée'
    )
    
    # Commentaires
    commentaires_supplementaires = TextAreaField(
        'Commentaires supplémentaires',
        validators=[
            Optional(),
            Length(max=1000, message="Maximum 1000 caractères")
        ],
        description="Informations additionnelles, défis particuliers, partenariats"
    )
    
    # Actions
    submit = SubmitField('Soumettre le projet')
    save_draft = SubmitField('Enregistrer en brouillon')
    
    def validate_date_mise_service_prevue(self, field):
        """Valider que la mise en service est après le début"""
        if field.data and self.date_debut_prevue.data:
            if field.data <= self.date_debut_prevue.data:
                raise ValidationError(
                    'La date de mise en service doit être postérieure au début des travaux'
                )